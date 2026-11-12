"""Quota cancellation invariants: no real provider side effects."""
import tempfile
import unittest
from pathlib import Path
from tools.ci_quota_cancel_first import LocalLedger, Route, cancel_first, demote_blocked_scopes, is_quota

class QuotaTest(unittest.TestCase):
    def test_cancel_first_and_deduplication(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=LocalLedger(Path(directory)/"state.sqlite")
            events=[]
            primary=Route("gitlab","scope-a",True,True,True)
            reserve=Route("github","scope-b",True,True,True)
            def run():
                return cancel_first(
                    ledger=ledger,task_id="task",attempt_id="attempt",current=primary,
                    candidates=[reserve],http_status=None,provider_code="ci_quota_exceeded",
                    error_message="",cancel=lambda x:(events.append("cancel") or True),
                    status=lambda x:(events.append("status") or "CANCELED"),
                    enqueue=lambda r,t,i:(events.append("enqueue") or "external-id"),
                    side_effects_possible=False)
            self.assertEqual(run()["state"],"FALLBACK_QUEUED")
            self.assertEqual(run()["state"],"FALLBACK_QUEUED")
            self.assertEqual(events,["cancel","status","enqueue"])
            ledger.close()

    def test_uncertain_cancel_never_fails_over(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=LocalLedger(Path(directory)/"state.sqlite")
            primary=Route("a","scope-a",True,True,True)
            reserve=Route("b","scope-b",True,True,True)
            calls=[]
            out=cancel_first(
                ledger=ledger,task_id="task",attempt_id="attempt",current=primary,
                candidates=[reserve],http_status=429,provider_code="",error_message="",
                cancel=lambda x:True,status=lambda x:"RUNNING",
                enqueue=lambda r,t,i:(calls.append("enqueue") or "external"),
                side_effects_possible=False)
            self.assertEqual(out["state"],"CANCEL_UNCONFIRMED")
            self.assertFalse(calls)
            ledger.close()

    def test_permission_is_not_quota(self):
        self.assertFalse(is_quota(http_status=401,code="quota_exceeded"))
        self.assertFalse(is_quota(http_status=403,code="forbidden",message="unauthorized"))


    def test_blocked_quota_goes_to_tail_without_reordering_healthy_providers(self):
        routes = [
            Route("vercel-primary", "vercel_hobby_fluid_cpu", True, True, True),
            Route("neon-oidc", "neon_free_compute", True, True, True),
            Route("vercel-alias", "vercel_hobby_fluid_cpu", True, True, True),
            Route("cloudflare", "cloudflare_workers_runtime", True, True, True),
        ]
        self.assertEqual(
            [route.name for route in demote_blocked_scopes(
                routes, {"vercel_hobby_fluid_cpu"})],
            ["neon-oidc", "cloudflare", "vercel-primary", "vercel-alias"],
        )

    def test_cancelled_quota_skips_stale_ready_aliases_and_selects_independent_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = LocalLedger(Path(directory)/"state.sqlite")
            selected = []
            out = cancel_first(
                ledger=ledger, task_id="quota-swap", attempt_id="original-run",
                current=Route("vercel-primary", "vercel_hobby_fluid_cpu", True, True, True),
                candidates=[
                    Route("vercel-alias", "vercel_hobby_fluid_cpu", True, True, True),
                    Route("neon-oidc", "neon_free_compute", True, True, True),
                ],
                blocked_quota_scopes=["vercel_hobby_fluid_cpu"],
                http_status=402, provider_code="quota_exceeded", error_message="",
                cancel=lambda _: True, status=lambda _: "CANCELED",
                enqueue=lambda route, *_: (selected.append(route.name) or "successor-id"),
                side_effects_possible=False,
            )
            self.assertEqual(out["state"], "FALLBACK_QUEUED")
            self.assertEqual(selected, ["neon-oidc"])
            ledger.close()

    def test_no_independent_provider_means_terminal_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = LocalLedger(Path(directory)/"state.sqlite")
            out = cancel_first(
                ledger=ledger, task_id="quota-swap", attempt_id="no-reserve",
                current=Route("vercel", "vercel_hobby_fluid_cpu", True, True, True),
                candidates=[Route("same-team-alias", "vercel_hobby_fluid_cpu", True, True, True)],
                blocked_quota_scopes=["vercel_hobby_fluid_cpu"],
                http_status=402, provider_code="quota_exceeded", error_message="",
                cancel=lambda _: True, status=lambda _: "CANCELED",
                enqueue=lambda *_: self.fail("must not dispatch blocked quota"),
                side_effects_possible=False,
            )
            self.assertEqual(out["state"], "CANCELLED_NO_INDEPENDENT_RESERVE")
            ledger.close()

if __name__=="__main__":
    unittest.main()
