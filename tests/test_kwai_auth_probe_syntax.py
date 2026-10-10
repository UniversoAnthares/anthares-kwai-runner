import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class KwaiAuthProbeSyntaxTests(unittest.TestCase):
    def test_auth_probe_parses(self):
        ast.parse((ROOT / "kwai_auth_probe.py").read_text(encoding="utf-8"))

    def test_identity_proof_requires_profile(self):
        source=(ROOT / "kwai_auth_probe.py").read_text(encoding="utf-8")
        self.assertIn("strong_identity(text)",source)
        self.assertIn("KWAI_IDENTITY_PROFILE_MATCH=1",source)
        self.assertIn("UNKNOWN_CREATE_SURFACE_NOT_IDENTITY_PROOF",source)

    def test_publisher_requires_rotation_gate(self):
        source=(ROOT / ".github/workflows/kwai-queue-publisher.yml").read_text(encoding="utf-8")
        self.assertIn("vars.KWAI_CREDENTIALS_ROTATED == 'true'",source)

if __name__=="__main__":
    unittest.main()
