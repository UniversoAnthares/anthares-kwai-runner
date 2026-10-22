from pathlib import Path
import unittest

W=(Path(__file__).resolve().parents[1]/".github/workflows/cortes-qa-p0-publication-watchdog.yml").read_text(encoding="utf8")

class FastP0Alerts(unittest.TestCase):
    def test_dedicated_proven_hosted_route(self):
        self.assertIn("runs-on: ubuntu-22.04",W)
        route=W.split("  route:",1)[1]
        self.assertNotIn("needs: test",route)
        self.assertIn("issues: write",route)
        self.assertIn("python3 -u tools/cortes_qa_p0_router.py",route)
        self.assertIn('if: github.event_name != \'pull_request\'',route)
    def test_qa_alerts_are_not_cancelled_by_pr_or_other_network(self):
        self.assertIn("cortes-p0-${{ github.event_name }}-",W)
        self.assertIn("github.event.workflow_run.name",W)
        self.assertIn("cancel-in-progress: false",W)
        self.assertIn('cron: "*/5 * * * *"',W)
    def test_both_personal_publishers_and_company_watchable(self):
        self.assertIn("CORTES LinkedIn personal - primary hosted cloud publisher",W)
        self.assertIn("CORTES LinkedIn personal - standby hosted publisher",W)
        self.assertIn("CORTES LinkedIn - automatic Buffer cloud publisher",W)
if __name__=="__main__":unittest.main()
