"""Safety contracts for independent Windows provider mirroring."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools"/"cortes_provider_mirrors_windows.ps1"
INSTALLER=ROOT/"tools"/"install_provider_mirror_task.ps1"
class MirrorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SCRIPT.read_text(encoding="utf8")
        cls.install=INSTALLER.read_text(encoding="utf8")
    def test_no_force_push_and_git_terminal_prompt_disabled(self):
        self.assertIn("$env:GIT_TERMINAL_PROMPT = '0'",self.code)
        self.assertNotIn("'--force'",self.code)
        self.assertNotIn("push -f",self.code)
        self.assertIn("merge-base --is-ancestor",self.code)
        self.assertIn("REMOTE_SHA_MISMATCH",self.code)
    def test_separate_provider_failures(self):
        self.assertIn("@('gitlab','codeberg')",self.code)
        self.assertIn("GITLAB_SYNC_REQUIRES_REVIEW",self.code)
        self.assertIn("CODEBERG_AUTH_OR_DIVERGENCE_REQUIRES_REVIEW",self.code)
        self.assertIn("mirror-health-",self.code)
    def test_hidden_scheduled_user_principal(self):
        self.assertIn("-WindowStyle Hidden",self.install)
        self.assertIn("New-ScheduledTaskPrincipal",self.install)
        self.assertIn("LogonType Interactive",self.install)
        self.assertIn("Minutes 30",self.install)
    def test_no_secret_literals_or_api_token_in_source(self):
        self.assertNotIn("ghp_",self.code)
        self.assertNotIn("glpat-",self.code)
        self.assertNotIn("CODEBERG_ACCESS_TOKEN",self.code)
if __name__=="__main__":unittest.main()
