"""Codeberg Actions must never inherit the GitHub social publisher workflows."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SmokeIsolation(unittest.TestCase):
    def test_only_readonly_manual_smoke_configured(self):
        path=ROOT/".forgejo/workflows/codeberg-capability-smoke.yml"
        data=path.read_text(encoding="utf-8")
        self.assertIn("runs-on: codeberg-tiny",data)
        self.assertIn("workflow_dispatch:",data)
        self.assertIn("CODEBERG_PUBLISHER_NOT_ARMED=PASS",data)
        self.assertNotIn("schedule:",data)
        self.assertNotIn("LINKEDIN_PERSONAL_ACCESS_TOKEN",data)
        self.assertNotIn("BWS_ACCESS_TOKEN",data)
    def test_github_publication_triggers_not_copied_to_codeberg(self):
        files=list((ROOT/".forgejo/workflows").glob("*.yml"))
        self.assertEqual([p.name for p in files],["codeberg-capability-smoke.yml"])
if __name__=="__main__":
    unittest.main()
