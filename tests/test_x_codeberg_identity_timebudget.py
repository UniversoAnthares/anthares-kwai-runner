import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class XCodebergTimeBudgetTest(unittest.TestCase):
    def test_identity_has_adequate_hosted_runner_limit(self):
        identity=(ROOT/".forgejo/workflows/x-codeberg-auth-identity.yml").read_text(encoding="utf8")
        self.assertIn("runs-on: codeberg-medium", identity)
        self.assertIn("timeout-minutes: 9", identity)
        browser=(ROOT/".forgejo/workflows/x-codeberg-primary.yml").read_text(encoding="utf8")
        self.assertIn("runs-on: codeberg-tiny",browser)
        self.assertIn("runs-on: codeberg-medium",browser)
if __name__=="__main__":unittest.main()
