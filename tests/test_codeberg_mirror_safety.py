"""Codeberg mirror may never report success without verified destination SHA."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class CodebergMirrorSafety(unittest.TestCase):
    def test_automatic_main_sync(self):
        text=(ROOT/'.github/workflows/mirror-codeberg.yml').read_text(encoding='utf8')
        self.assertIn('branches: [main]',text)
        self.assertIn("cron: '13,43 * * * *'",text)
        self.assertIn('workflow_dispatch:',text)

    def test_fail_closed_without_codeberg_credential(self):
        text=(ROOT/'.github/workflows/mirror-codeberg.yml').read_text(encoding='utf8')
        self.assertIn('CODEBERG_PUSH_URL_MISSING',text)
        self.assertNotIn('exit 0\n          fi',text)

    def test_non_force_and_exact_sha_readback(self):
        text=(ROOT/'.github/workflows/mirror-codeberg.yml').read_text(encoding='utf8')
        self.assertNotIn("git push codeberg '+'",text)
        self.assertNotIn("' +refs/",text)
        self.assertIn('CODEBERG_DIVERGED_NON_FAST_FORWARD_STOP',text)
        self.assertIn('CODEBERG_MAIN_SHA_MISMATCH',text)
        self.assertIn('git ls-remote codeberg refs/heads/main',text)

if __name__=='__main__':
    unittest.main()
