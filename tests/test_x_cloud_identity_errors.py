import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class CloudIdentityDiagnosticTests(unittest.TestCase):
    def test_safe_error_codes_cover_missing_secret_and_vault(self):
        body=(ROOT/"tools/x_cloud_browser_identity_probe.py").read_text(encoding="utf-8")
        for code in ("X_SHARED_SECRET_NOT_CONFIGURED",
                     "X_ENCRYPTED_VAULT_EMPTY",
                     "X_VAULT_MISSING_AUTHENTICATED_COOKIES",
                     "X_CLOUD_LOGIN_REQUIRED",
                     "X_CLOUD_ACCOUNT_MISMATCH"):
            self.assertIn(code,body)
        self.assertIn("code in SAFE_CODES",body)
        self.assertNotIn('print("X_CLOUD_PREFLIGHT_ERROR_CODE=" + str(exc)',body)

if __name__=="__main__":
    unittest.main()
