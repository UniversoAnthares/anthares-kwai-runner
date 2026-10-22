import unittest
from datetime import datetime, timedelta, timezone
from tools.cortes_linkedin_fallback_gate import need_standby, HEALTH_MINUTES
from pathlib import Path

NOW = datetime(2026,10,22,12,0,tzinfo=timezone.utc)
LABEL = "CORTES LinkedIn personal - primary hosted cloud publisher"

class PrimaryAndStandby(unittest.TestCase):
    def test_primary_proven_success_prevents_duplicate_standby_schedule(self):
        run=[{"name":LABEL,"conclusion":"success","updated_at":NOW.isoformat()}]
        self.assertFalse(need_standby("schedule",run,NOW))
        self.assertTrue(need_standby("workflow_dispatch",run,NOW))
        self.assertTrue(need_standby("workflow_run",run,NOW))

    def test_standby_activates_after_primary_failure_or_staleness(self):
        failed=[{"name":LABEL,"conclusion":"failure","updated_at":NOW.isoformat()}]
        self.assertTrue(need_standby("schedule",failed,NOW))
        old=[{"name":LABEL,"conclusion":"success","updated_at":(NOW-timedelta(minutes=HEALTH_MINUTES+1)).isoformat()}]
        self.assertTrue(need_standby("schedule",old,NOW))
        self.assertTrue(need_standby("schedule",[],NOW))
        self.assertFalse(need_standby("push",[],NOW))

    def test_no_trigger_cycle_or_loss_of_neon_cas(self):
        base=Path(__file__).resolve().parents[1]
        primary=(base/".github/workflows/cortes-linkedin-personal-fallback-cloud.yml").read_text(encoding="utf8")
        standby=(base/".github/workflows/cortes-linkedin-personal-cloud.yml").read_text(encoding="utf8")
        neon=(base/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf8")
        self.assertNotIn("workflow_run:",primary)
        self.assertIn('workflows: ["CORTES LinkedIn personal - primary hosted cloud publisher"]',standby)
        self.assertIn("group: cortes-linkedin-personal-primary-hosted",primary)
        self.assertIn("group: cortes-linkedin-personal-standby-hosted",standby)
        self.assertIn("lease_generation",neon)
        self.assertIn("P_OWNER='linkedin-personal:github-cloud-v1'",neon)
        self.assertIn("if: steps.primary-health.outputs.run == 'true'",standby)

if __name__=="__main__": unittest.main()
