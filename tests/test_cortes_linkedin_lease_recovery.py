"""Ensure stale claims are recovered, never blindly replayed after start."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class LeaseRecoveryContracts(unittest.TestCase):
    def test_started_jobs_become_uncertain_and_not_requeued(self):
        f=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        block=f.split("async function recoverExpiredLinkedin(targetKey){",1)[1].split("async function personalAction",1)[0]
        self.assertIn("publication_started_at IS NULL THEN 'queued' ELSE 'uncertain'",block)
        self.assertIn("status IN ('leased','started')",block)
        self.assertIn("lease_until<now()",block)
        self.assertIn("lease_owner=NULL",block)
        self.assertIn("confirmed_on_network:false",block)

    def test_recovery_runs_before_each_linkedin_lease(self):
        f=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        self.assertIn("if(platform==='linkedin')await recoverExpiredLinkedin(dest);",f)
        self.assertIn("await recoverExpiredLinkedin(P_TARGET);",f)

    def test_other_network_leases_unchanged(self):
        f=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        self.assertNotIn("if(platform==='pinterest')await recoverExpiredLinkedin(dest);",f)
        self.assertNotIn("if(platform==='instagram')await recoverExpiredLinkedin(dest);",f)

if __name__=="__main__":
    unittest.main()
