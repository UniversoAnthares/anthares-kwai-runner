import unittest
from datetime import datetime, timedelta, timezone
from tools.pinterest_qa_cooldown_loop import assess, should_report


class PinterestAutonomousQA(unittest.TestCase):
    def setUp(self):
        self.pass_evidence = {"worker_conclusion": "success", "result": "PASS_NO_NEW_PIN"}

    def test_429_keeps_qa_open(self):
        state, remaining = assess({"worker_conclusion": "success", "result": "RATE_LIMIT_ISOLATED"},
                                  {"confirmed": 7, "queued": 42, "uncertain": 15},
                                  {"active": True, "cooldown_until": "2026-10-22T18:29:29Z"})
        self.assertEqual((state, remaining), ("COOLDOWN_HTTP_429", 57))

    def test_draft_and_existing_sent_receipts_do_not_close_qa(self):
        state, remaining = assess(self.pass_evidence,
                                  {"confirmed": 7, "queued": 42, "uncertain": 15},
                                  {"active": False})
        self.assertEqual((state, remaining), ("RETRY_UNTIL_CONFIRMED", 57))

    def test_closed_cooldown_but_unresolved_is_not_pass(self):
        state, remaining = assess({"worker_conclusion": "success",
                                   "result": "WAITING_BUFFER_DELIVERY"},
                                  {"confirmed": 8, "queued": 1, "uncertain": 1},
                                  {"active": False})
        self.assertEqual((state, remaining), ("BUFFER_BACKPRESSURE", 2))

    def test_only_fully_reconciled_extra_confirmed_post_passes(self):
        state, remaining = assess(self.pass_evidence,
                                  {"confirmed": 8, "queued": 0, "uncertain": 0},
                                  {"active": False})
        self.assertEqual((state, remaining), ("PASS", 0))

    def test_no_neon_proof_no_pass(self):
        state, _ = assess(self.pass_evidence, None, None)
        self.assertEqual(state, "QA_VISIBILITY_UNAVAILABLE")

    def test_workflow_failure_never_passes(self):
        state, _ = assess({"worker_conclusion": "failure", "result": "PASS_NO_NEW_PIN"},
                          {"confirmed": 8}, {"active": False})
        self.assertEqual(state, "EXECUTION_FAILED")

    def test_report_on_cooldown_change_but_no_comment_storm(self):
        now = datetime(2026, 10, 22, 18, 1, tzinfo=timezone.utc)
        prev = {"state": "COOLDOWN_HTTP_429", "expiry": "2026-10-22T18:29:29Z",
                "at": (now - timedelta(minutes=4)).isoformat()}
        self.assertFalse(should_report(prev, "COOLDOWN_HTTP_429",
                                       "2026-10-22T18:29:29Z", 57, now))
        self.assertTrue(should_report(prev, "COOLDOWN_HTTP_429",
                                      "2026-10-22T19:00:00Z", 57, now))
        self.assertTrue(should_report(prev, "PASS", None, 0, now))


if __name__ == "__main__":
    unittest.main()
