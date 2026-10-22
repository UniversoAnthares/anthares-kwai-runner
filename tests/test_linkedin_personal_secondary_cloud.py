"""The second hosted publisher is isolated from local PCs and shares CAS."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PersonalFailover(unittest.TestCase):
    def test_secondary_is_cloud_oidc_and_bitwarden(self):
        wf=(ROOT/".github/workflows/cortes-linkedin-personal-fallback-cloud.yml").read_text()
        primary=(ROOT/".github/workflows/cortes-linkedin-personal-cloud.yml").read_text()
        self.assertIn("runs-on: ubuntu-22.04",wf)
        self.assertIn("id-token: write",wf)
        self.assertIn("bitwarden/sm-action@v2",wf)
        self.assertIn("python -u -m tools.cortes_linkedin_personal_cloud",wf)
        self.assertIn("group: cortes-linkedin-personal-cloud",wf)
        self.assertIn("group: cortes-linkedin-personal-cloud",primary)
        self.assertIn("workflow_run:",wf)
        self.assertIn("schedule:",wf)
        self.assertNotIn("self-hosted",wf)
    def test_oidc_authorizes_backup_with_same_personal_fence(self):
        s=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text()
        self.assertIn("wf==='cortes-linkedin-personal-fallback-cloud.yml'",s)
        self.assertIn("role='personal';platform='linkedin'",s)
        self.assertIn("const P_TARGET='linkedin:personal',P_OWNER='linkedin-personal:github-cloud-v1'",s)
        self.assertIn("lease_generation",s)
if __name__=="__main__":unittest.main()
