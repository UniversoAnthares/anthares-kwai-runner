"""QA P0 executable playbooks: bounded, no blind remote media writes."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PS=(ROOT/"tools/cortes_qa_p0_recovery.ps1").read_text(encoding="utf8")
WF=(ROOT/".github/workflows/cortes-qa-p0-executor.yml").read_text(encoding="utf8")

class P0Recovery(unittest.TestCase):
    def test_incident_preflight_is_mandatory(self):
        self.assertIn("QA-P0",PS)
        self.assertIn("QA_AUTOHEAL_INCIDENT_NOT_AUTHORIZED",PS)
        self.assertIn("UniversoAnthares/anthares-kwai-runner",PS)
        self.assertIn("RUNNER_OS -ne 'Windows'",PS)
        self.assertIn("GITHUB_ACTIONS -ne 'true'",PS)

    def test_daily_recovery_requires_zero_verified_neon_masters(self):
        self.assertIn("action=round-health",PS)
        self.assertIn("America/Campo_Grande",PS)
        self.assertIn("today_master_count -eq 0",PS)
        self.assertIn("Anthares CORTES Shorts Daytime Recovery 20min",PS)
        self.assertIn("Start-ScheduledTask",PS)
        self.assertIn("DAILY_PRODUCER_WATCHDOG_WAKEUP_ACCEPTED",PS)
        self.assertNotIn("Stop-ScheduledTask",PS)

    def test_linkedin_only_personal_dispatch_no_unguarded_reposts(self):
        self.assertIn("CORTES LinkedIn personal",PS)
        self.assertIn("cortes-linkedin-personal-fallback-cloud.yml/dispatches",PS)
        self.assertIn("LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ACCEPTED",PS)
        self.assertNotIn("linkedin.com/v2/ugcPosts",PS)
        self.assertNotIn("linkedin.com/rest/posts",PS)

    def test_executor_wired_before_final_qa_comment(self):
        self.assertIn("tools\\cortes_qa_p0_recovery.ps1",WF)
        self.assertIn("id: recovery",WF)
        self.assertIn("QA_AUTOHEAL",WF)
        self.assertIn("actions: write",WF)
        self.assertIn("if: steps.preflight.outcome == 'success'",WF)
        self.assertIn("CODEBERG_TESTS_VERIFIED_REPAIR_UNCONFIRMED",WF)

if __name__=="__main__":unittest.main()
