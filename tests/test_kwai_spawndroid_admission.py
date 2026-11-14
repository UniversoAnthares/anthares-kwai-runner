import copy
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "tools" / "kwai_spawndroid_admission.py"
spec = importlib.util.spec_from_file_location("kwai_spawndroid_admission", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NOW = datetime(2026, 11, 14, 12, 30, tzinfo=timezone.utc)


def iso(t):
    return t.isoformat()


def fixture():
    times = []
    for a, account in enumerate(mod.ACCOUNTS):
        for i in range(3):
            base = NOW - timedelta(hours=4 + a, minutes=i * 10)
            offsets = (0, 20, 60, 80, 120, 150, 160)
            entry = dict(
                account=account,
                session_id=f"sess-{account}-{i}",
                remote_url=f"https://www.kwai.com/@{account}/video/{5234000000000000000+a*100+i}",
                proof_kind="independent_public_readback_verified",
                provider_terminal="closed",
            )
            for phase, seconds in zip(mod.PHASES, offsets):
                entry[phase] = iso(base + timedelta(seconds=seconds))
            times.append(entry)
    neon = {}
    for account in mod.ACCOUNTS:
        neon[account] = dict(
            target_key="kwai:" + account, source="authenticated_neon_cortesqueue",
            observed_at=iso(NOW), queued=80, started_today=1,
            confirmed_today=1, inflight=0, uncertain=0,
            daily_limit=100, last_public_at=iso(NOW - timedelta(minutes=25)),
        )
    return dict(
        quota=dict(source="authenticated_spawndroid_settings",
                   observed_at=iso(NOW), plan="Hobby",
                   device_minutes_limit=200, device_minutes_used=0,
                   other_sessions_reserved_minutes=0,
                   parallel_runners=1, overage_enabled=False),
        measurements=times, neon=neon,
        minimum_spacing_seconds=600,
        failure_reserve_multiplier=1.25,
    )


class TestKwaiSpawnDroidAdmission(unittest.TestCase):
    def evaluate(self, body):
        return mod.evaluate(body, now=NOW)

    def test_fully_qualified_synthetic_fixture_never_arms_production(self):
        result = self.evaluate(fixture())
        self.assertEqual(result["status"], "OFFLINE_CAPACITY_ONLY")
        self.assertFalse(result["production_eligible"])
        self.assertFalse(result["cloud_cutover_enabled"])
        self.assertEqual(result["maximum_monthly_posts_shared"], 66)
        self.assertEqual(result["sustainable_daily_posts_shared"], 3)
        self.assertEqual(result["recommended_daily_posts_shared"], 3)
        self.assertTrue(result["accounts_share_single_runner"])
        self.assertEqual(result["remaining_days_in_month"], 17)
        self.assertEqual(result["accounts"]["lucasrosalem"]["reserved_device_minutes_per_post"], 3)
        self.assertEqual(result["accounts"]["universoanthares"]["reserved_device_minutes_per_post"], 3)
        self.assertGreater(result["accounts"]["lucasrosalem"]["p95_provision_seconds"], 0)
        self.assertGreater(result["accounts"]["lucasrosalem"]["phase_p95_seconds"]["proof_seconds"], 0)
        print("SPAWNDROID_200M_MONTHLY_SHARED_POOL_GUARD_PASS")

    def test_quota_is_cumulative_across_both_accounts(self):
        item = fixture()
        item["quota"]["device_minutes_used"] = 190
        item["quota"]["other_sessions_reserved_minutes"] = 4
        result = self.evaluate(item)
        self.assertEqual(result["maximum_monthly_posts_shared"], 2)
        self.assertEqual(result["sustainable_daily_posts_shared"], 0)
        self.assertEqual(result["recommended_daily_posts_shared"], 0)

    def test_unknown_and_stale_quota_fail_closed(self):
        for change in (
            {"plan": "Personal"}, {"source": "unverified_marketing"},
            {"device_minutes_limit": 500}, {"overage_enabled": True},
            {"parallel_runners": 2}, {"device_minutes_used": 201},
            {"other_sessions_reserved_minutes": -2},
            {"observed_at": iso(NOW - timedelta(minutes=3))},
        ):
            item = fixture()
            item["quota"].update(change)
            with self.subTest(change=change), self.assertRaises(mod.AdmissionError):
                self.evaluate(item)
        print("SPAWNDROID_NO_BILLING_OR_STALE_QUOTA_FAIL_CLOSED_PASS")

    def test_missing_real_samples_per_account_block(self):
        item = fixture()
        item["measurements"] = [x for x in item["measurements"]
                                if x["account"] != "universoanthares"]
        with self.assertRaisesRegex(mod.AdmissionError, "insufficient_real_samples"):
            self.evaluate(item)

    def test_unverified_public_proof_and_duplicate_identity_block(self):
        item = fixture()
        item["measurements"][0]["proof_kind"] = "webdriver_green"
        with self.assertRaisesRegex(mod.AdmissionError, "independent_public_proof"):
            self.evaluate(item)
        item = fixture()
        item["measurements"][1]["session_id"] = item["measurements"][0]["session_id"]
        with self.assertRaisesRegex(mod.AdmissionError, "unverifiable_session"):
            self.evaluate(item)
        item = fixture()
        item["measurements"][0]["remote_url"] = (
            "https://www.kwai.com/@universoanthares/video/12345")
        with self.assertRaisesRegex(mod.AdmissionError, "unverifiable_session"):
            self.evaluate(item)

    def test_session_15_minutes_and_order_guard(self):
        item = fixture()
        item["measurements"][0]["closed_at"] = iso(
            mod.timestamp(item["measurements"][0]["ready_at"]) +
            timedelta(seconds=901))
        with self.assertRaisesRegex(mod.AdmissionError, "session_exceeds"):
            self.evaluate(item)
        item = fixture()
        item["measurements"][0]["authenticated_at"] = item["measurements"][0]["ready_at"]
        with self.assertRaisesRegex(mod.AdmissionError, "phase_order"):
            self.evaluate(item)
        print("SPAWNDROID_15MIN_SESSION_BILLING_GUARD_PASS")

    def test_reconcile_blocks_only_affected_account(self):
        item = fixture()
        item["neon"]["universoanthares"]["uncertain"] = 1
        result = self.evaluate(item)
        self.assertEqual(result["account_day_windows"]["universoanthares"]["status"],
                         "RECONCILE_REQUIRED")
        self.assertEqual(result["account_day_windows"]["universoanthares"]["day_slots"], 0)
        self.assertGreater(result["account_day_windows"]["lucasrosalem"]["day_slots"], 0)
        print("SPAWNDROID_UNCERTAIN_NEVER_RESENT_PASS")

    def test_spacing_and_23h_exclusive(self):
        item = fixture()
        item["minimum_spacing_seconds"] = 86400
        self.assertEqual(self.evaluate(item)["recommended_daily_posts_shared"], 0)
        after_23_utc = datetime(2026, 11, 15, 3, 1, tzinfo=timezone.utc)
        for x in item["neon"].values():
            x["observed_at"] = iso(after_23_utc)
            x["last_public_at"] = None
            x["confirmed_today"] = 0
            x["started_today"] = 0
        item["quota"]["observed_at"] = iso(after_23_utc)
        item["measurements"] = [
            {**x, "requested_at": iso(mod.timestamp(x["requested_at"]) + timedelta(hours=1)),
             "ready_at": iso(mod.timestamp(x["ready_at"]) + timedelta(hours=1)),
             "authenticated_at": iso(mod.timestamp(x["authenticated_at"]) + timedelta(hours=1)),
             "mp4_loaded_at": iso(mod.timestamp(x["mp4_loaded_at"]) + timedelta(hours=1)),
             "published_at": iso(mod.timestamp(x["published_at"]) + timedelta(hours=1)),
             "public_verified_at": iso(mod.timestamp(x["public_verified_at"]) + timedelta(hours=1)),
             "closed_at": iso(mod.timestamp(x["closed_at"]) + timedelta(hours=1))}
            for x in item["measurements"]
        ]
        result = mod.evaluate(item, now=after_23_utc)
        self.assertEqual(result["recommended_daily_posts_shared"], 0)
        print("SPAWNDROID_EFFECTIVE_SPACING_AND_23H_EXCLUSION_PASS")

    def test_neon_authentication_and_daily_limit(self):
        item = fixture()
        item["neon"]["lucasrosalem"]["source"] = "user_cli"
        with self.assertRaisesRegex(mod.AdmissionError, "neon_origin_unverified"):
            self.evaluate(item)
        item = fixture()
        item["neon"]["lucasrosalem"]["daily_limit"] = 101
        with self.assertRaisesRegex(mod.AdmissionError, "invalid_daily_limit"):
            self.evaluate(item)
        print("SPAWNDROID_NEON_ACCOUNT_CAP_100_PASS")

    def test_cancel_quota_requires_terminal_and_no_external_effect(self):
        f = mod.quota_cancel_disposition
        self.assertEqual(f(http_status=402, session_owned=True,
                           provider_cancel_terminal=False, effect_state="NOT_APPLIED"),
                         "CANCEL_UNCONFIRMED")
        self.assertEqual(f(http_status=402, session_owned=True,
                           provider_cancel_terminal=True, effect_state="UNKNOWN"),
                         "RECONCILE_REQUIRED")
        self.assertEqual(f(http_status=402, session_owned=False,
                           provider_cancel_terminal=False, effect_state="NOT_APPLIED"),
                         "CANCELLED_NO_INDEPENDENT_RESERVE")
        self.assertEqual(f(http_status=402, session_owned=True,
                           provider_cancel_terminal=True, effect_state="NOT_APPLIED",
                           independent_reserve_verified=True),
                         "TERMINAL_NEW_FENCED_ATTEMPT_PERMITTED")
        self.assertEqual(f(http_status=429, session_owned=False,
                           provider_cancel_terminal=False, effect_state="UNKNOWN"),
                         "CONCURRENCY_BUSY_NO_PARALLEL_RETRY")
        self.assertEqual(f(http_status=403, session_owned=False,
                           provider_cancel_terminal=False, effect_state="UNKNOWN"),
                         "NOT_QUOTA_ERROR")
        print("SPAWNDROID_CANCEL_FIRST_QUOTA_AND_UNKNOWN_SIDE_EFFECTS_PASS")


if __name__ == "__main__":
    unittest.main()
