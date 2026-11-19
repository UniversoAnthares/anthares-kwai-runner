"""Offline tests for private-key Resend read-only health check."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from resend_readonly_check import private_api_key, read_only_status, main
from resend_marketing import ResendMarketing, ResendMarketingError


class ResendHealthTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "key.txt")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("re_" + "A" * 45)
        os.chmod(self.path, 0o600)

    def tearDown(self):
        self.folder.cleanup()

    def test_requires_private_key_mode(self):
        self.assertTrue(private_api_key(self.path).startswith("re_"))
        os.chmod(self.path, 0o644)
        with self.assertRaises(PermissionError):
            private_api_key(self.path)

    def test_missing_key_invalid(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("")
        with self.assertRaises(ValueError):
            private_api_key(self.path)

    def test_readiness_uses_get_only(self):
        calls = []
        def fake(method, route, body):
            calls.append((method,route))
            return {"data": [{"email": "hidden@example.org"}]}
        report = read_only_status(ResendMarketing(transport=fake))
        self.assertTrue(report["authenticated"])
        self.assertEqual(report["mailing_dispatch"], "disabled")
        self.assertTrue(all(method == "GET" for method,_ in calls))
        self.assertNotIn("hidden@example.org", str(report))

    def test_http_errors_are_sanitized(self):
        def fake(method, route, body):
            raise ResendMarketingError(403)
        report = read_only_status(ResendMarketing(transport=fake))
        self.assertFalse(report["authenticated"])
        self.assertEqual(report["resources"]["segments"], "http_403")

    def test_cli_rejects_mutating_switches(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"RESEND_DRAFT_WRITE_ENABLED": "1"}):
            with redirect_stdout(output):
                code = main(["--key-file", self.path])
        self.assertEqual(code,3)
        self.assertIn("mutating_gate_enabled", output.getvalue())


if __name__ == "__main__":
    unittest.main()
