"""Static rate-budget guard for Buffer schedules.

The three channels share one API token (250 requests per provider window).
Do not allow previous 28-per-hour scheduled polling to return.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SharedBufferScheduleTests(unittest.TestCase):
    PLANS={
        "cortes-buffer-instagram-cloud.yml":"8 */3 * * *",
        "cortes-buffer-pinterest-cloud.yml":"38 */3 * * *",
        "cortes-buffer-linkedin-cloud.yml":"53 */3 * * *",
    }
    def test_scheduled_baseline_bounded_to_twenty_four_runs_per_day(self):
        total=0
        for file,cron in self.PLANS.items():
            text=(ROOT/".github"/"workflows"/file).read_text(encoding="utf8")
            patterns=re.findall(r"^\s*-\s*cron:\s*['\"]([^'\"]+)['\"]",text,re.M)
            self.assertEqual(patterns,[cron],file)
            self.assertIn("cancel-in-progress: false",text)
            self.assertIn("workflow_dispatch:",text)
            total+=8
        self.assertLessEqual(total,24)
        self.assertLess(total,250)

    def test_pinterest_probe_manual_only_and_publisher_still_scheduled(self):
        diag=(ROOT/".github"/"workflows"/"cortes-pinterest-board-paths-probe.yml").read_text(encoding="utf8")
        self.assertNotIn("  schedule:",diag)
        self.assertIn("workflow_dispatch:",diag)
        pub=(ROOT/".github"/"workflows"/"cortes-buffer-pinterest-cloud.yml").read_text(encoding="utf8")
        self.assertIn("schedule:",pub)
        self.assertIn("workflow_run:",pub)

if __name__=="__main__":
    unittest.main()
