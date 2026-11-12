"""Contracts for one canonical per-account CORTES day ending 23:00 MS."""
from datetime import datetime, timedelta, timezone
import unittest
from zoneinfo import ZoneInfo
from tools.cortes_deadline_pacing import plan_publications, assert_due

TZ = ZoneInfo("America/Campo_Grande")
def dt(hour, minute=0):
    return datetime(2026, 11, 12, hour, minute, tzinfo=TZ)

def plan(**extra):
    defaults = dict(now=dt(9), target_key="instagram:universoanthares",
                    queued=8, started_today=1, daily_limit=100,
                    first_confirmed_at=dt(8), last_confirmed_at=dt(8))
    defaults.update(extra)
    return plan_publications(**defaults)


class DeadlinePacingTests(unittest.TestCase):
    def test_first_confirmation_anchor_distributes_remaining_to_23h(self):
        p = plan(queued=3, now=dt(8), started_today=1)
        self.assertEqual(p.status, "WAIT")
        self.assertEqual(p.due_at, dt(12, 59) + timedelta(seconds=40))
        self.assertEqual(p.interval_seconds, 4 * 3600 + 59 * 60 + 40)

    def test_recalculate_after_actual_confirmation(self):
        p = plan(queued=2, now=dt(15), first_confirmed_at=dt(8),
                 last_confirmed_at=dt(14), started_today=2)
        self.assertEqual(p.due_at, dt(18, 29) + timedelta(seconds=30))
        self.assertEqual(p.status, "WAIT")
        self.assertTrue(plan(queued=2, now=dt(19), first_confirmed_at=dt(8),
                             last_confirmed_at=dt(14), started_today=2).is_due(dt(19)))

    def test_start_without_confirmation_is_due_now(self):
        p = plan(queued=30, started_today=0, first_confirmed_at=None,
                 last_confirmed_at=None, now=dt(9, 16))
        self.assertEqual(p.status, "DUE")
        self.assertEqual(p.due_at, dt(9, 16))

    def test_plan_is_independent_for_each_account(self):
        p = plan(target_key="kwai:lucasrosalem", now=dt(10), first_confirmed_at=dt(10),
                 last_confirmed_at=dt(10), queued=4, started_today=1)
        self.assertEqual(p.due_at, dt(13, 14) + timedelta(seconds=45))

    def test_last_eligible_occurs_by_23h(self):
        p = plan(queued=1, started_today=3, last_confirmed_at=dt(18),
                 now=dt(22))
        self.assertEqual(p.due_at, dt(22, 59))
        self.assertEqual(p.status, "WAIT")

    def test_daily_limit_and_inventory_are_distinct(self):
        p = plan(queued=230, daily_limit=100, started_today=92,
                 last_confirmed_at=dt(8))
        self.assertEqual(p.remaining_today, 8)
        self.assertEqual(p.deferred_due_to_limit, 222)

    def test_capacity_shortfall_reported_after_window(self):
        p = plan(queued=3, now=dt(23, 1))
        self.assertEqual(p.status, "BLOCKED_SAME_DAY_CAPACITY")

    def test_zero_posts_at_midnight_and_0559_first_due_at_0600(self):
        for hour, minute in ((0, 0), (5, 59)):
            p = plan(now=dt(hour, minute), queued=100, started_today=0,
                     first_confirmed_at=None, last_confirmed_at=None)
            self.assertEqual(p.status, "WAIT_DAY_START")
            self.assertEqual(p.due_at, dt(6))
            self.assertFalse(p.is_due(dt(hour, minute)))
        p = plan(now=dt(6), started_today=0, first_confirmed_at=None,
                 last_confirmed_at=None)
        self.assertEqual(p.status, "DUE")
        assert_due(p, dt(6))

    def test_last_slot_2259_and_2300_never_allowed(self):
        p = plan(now=dt(22), queued=1, started_today=10, last_confirmed_at=dt(16))
        self.assertEqual(p.due_at, dt(22, 59))
        self.assertEqual(p.status, "WAIT")
        assert_due(plan(now=dt(22, 59), queued=1,
                        started_today=10, last_confirmed_at=dt(16)), dt(22, 59))
        with self.assertRaisesRegex(RuntimeError, "WAIT_UNTIL_DUE"):
            assert_due(plan(now=dt(22, 59), queued=1,
                            started_today=10, last_confirmed_at=dt(16)), dt(23))
        self.assertEqual(plan(now=dt(23)).status, "BLOCKED_SAME_DAY_CAPACITY")

    def test_started_without_confirmation_prevents_rapid_flood(self):
        p = plan(now=dt(6, 1), queued=99, started_today=1,
                 first_confirmed_at=None, last_confirmed_at=None,
                 last_started_at=dt(6))
        self.assertEqual(p.status, "WAIT")
        self.assertGreater(p.due_at, dt(6, 10))

    def test_provider_actual_quota_always_wins(self):
        p = plan(queued=20, provider_remaining=0)
        self.assertEqual(p.status, "BLOCKED_PLATFORM_LIMIT")

    def test_provider_minimum_gap_can_block_infeasible_plan(self):
        p = plan(queued=60, now=dt(22, 1), first_confirmed_at=dt(22),
                 last_confirmed_at=dt(22), provider_min_gap_seconds=180)
        self.assertEqual(p.status, "BLOCKED_PLATFORM_LIMIT")

    def test_separate_double_check_rejects_early_send(self):
        p = plan()
        with self.assertRaisesRegex(RuntimeError, "CORTES_PACING_WAIT_UNTIL_DUE"):
            assert_due(p, dt(9))
        assert_due(plan(now=dt(22)), dt(22))

    def test_timestamp_must_be_aware_and_same_local_day(self):
        with self.assertRaisesRegex(ValueError, "NAIVE"):
            plan(now=datetime(2026, 11, 12, 9))
        with self.assertRaisesRegex(ValueError, "FIRST_OUTSIDE"):
            plan(first_confirmed_at=dt(8) - timedelta(days=1))

    def test_independent_utc_conversion(self):
        p = plan(now=dt(15).astimezone(timezone.utc))
        self.assertEqual(p.due_at.astimezone(TZ), datetime(2026, 11, 12, 9, 52, 22, 500000, tzinfo=TZ))


if __name__ == "__main__":
    unittest.main()
