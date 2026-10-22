"""A missing Codeberg API admin permission must not masquerade as git sync failure."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class CodebergMirrorBoundaries(unittest.TestCase):
    def test_admin_settings_are_optional_for_mirror_job(self):
        w=(ROOT/".github/workflows/mirror-codeberg.yml").read_text(encoding="utf-8")
        self.assertIn("continue-on-error: true",w)
        self.assertIn("CODEBERG_MAIN_SHA_MISMATCH",w)
        self.assertNotIn("--force",w)
    def test_health_checks_all_but_fails_only_for_source_parity(self):
        s=(ROOT/"tools/codeberg_mirror_health.py").read_text(encoding="utf-8")
        self.assertIn("CODEBERG_GIT_PARITY_PROVEN=",s)
        self.assertIn("CODEBERG_ACTIONS_CONFIG=",s)
        self.assertIn('raise SystemExit(0 if checks["sha_match"] else 2)',s)
if __name__=="__main__":
    unittest.main()
