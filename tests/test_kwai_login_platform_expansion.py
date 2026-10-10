import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class LoginPlatformExpansion(unittest.TestCase):
    def test_recovery_script_parses(self):
        ast.parse((ROOT/"tools/kwai_login_surface_recovery.py").read_text())
    def test_expansion_uses_observed_exact_widget(self):
        src=(ROOT/"tools/kwai_login_surface_recovery.py").read_text()
        self.assertIn('"login_platform_expand_text"',src)
        self.assertIn('return "expand_native_login_platforms"',src)
        self.assertIn('if (n.get("resource-id") or "").endswith("/"+suffix)',src)
    def test_authentication_still_requires_identity_proof(self):
        src=(ROOT/"kwai_auth_probe.py").read_text()
        self.assertIn("KWAI_IDENTITY_PROFILE_MATCH=1",src)
        self.assertIn("UNKNOWN_CREATE_SURFACE_NOT_IDENTITY_PROOF",src)
    def test_rotation_gate_preserved(self):
        src=(ROOT/".github/workflows/kwai-queue-publisher.yml").read_text()
        self.assertIn("vars.KWAI_CREDENTIALS_ROTATED == 'true'",src)
if __name__=="__main__":unittest.main()
