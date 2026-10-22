"""Regression for daily Neon distribution totals across all active short networks."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"infra/neon-cortes-queue/index.mjs").read_text("utf8")
FIRST=SOURCE.index("action==='round-health'")
END=SOURCE.index("if(request.method!=='POST')",FIRST)
HEALTH=SOURCE[FIRST:END]


class RoundHealthThreadCoverage(unittest.TestCase):
    def test_threads_in_daily_distribution(self):
        self.assertIn("'threads:universoanthares'", HEALTH)
        self.assertIn("'pinterest:lucasyahn'", HEALTH)
        self.assertIn("'linkedin:personal'", HEALTH)
        self.assertIn("today_any_destination_count:allEnqueued", HEALTH)

    def test_kwai_counter_remains_scoped_and_producer_unverified(self):
        self.assertIn("today_master_count:kwaiEnqueued", HEALTH)
        self.assertIn("today_master_count_scope:'kwai:lucasrosalem enqueue only'", HEALTH)
        self.assertIn("producer_status:'unverified_by_queue'", HEALTH)
        self.assertIn("stalled_daily_distribution:allEnqueued===0", HEALTH)


if __name__=="__main__":
    unittest.main()
