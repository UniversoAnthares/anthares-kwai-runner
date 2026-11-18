"""Offline Sender health check tests: no credentials or network required."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sender_marketing import SenderMarketing, SenderAPIError
from sender_readonly_check import private_sender_token, readiness, main


class SenderReadinessTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.token_path = os.path.join(self.folder.name, "sender-api-token.txt")
        with open(self.token_path, "w", encoding="utf-8") as f:
            f.write("sender_fake_token_" + "A" * 42)
        os.chmod(self.token_path, 0o600)

    def tearDown(self):
        self.folder.cleanup()

    def test_read_file_checks_mode(self):
        self.assertTrue(private_sender_token(self.token_path).startswith("sender_fake_token_"))
        os.chmod(self.token_path, 0o644)
        with self.assertRaises(PermissionError):
            private_sender_token(self.token_path)

    def test_empty_file_rejected(self):
        with open(self.token_path, "w", encoding="utf-8") as f:
            f.write("")
        with self.assertRaises(ValueError):
            private_sender_token(self.token_path)

    def test_readiness_is_get_only_and_no_pii(self):
        calls = []
        def fake(method, path, data):
            calls.append((method, path))
            return {"data": [{"email": "private@example.org"}]}
        result = readiness(SenderMarketing(transport=fake))
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["dispatch"], "disabled")
        self.assertTrue(all(m == "GET" for m, _ in calls))
        self.assertNotIn("private@example.org", str(result))

    def test_http_failures_are_redacted(self):
        def fake(method, path, data):
            raise SenderAPIError(401)
        result = readiness(SenderMarketing(transport=fake))
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["endpoints"]["campaign_drafts"], "http_401")

    def test_cli_refuses_writes(self):
        buffer = io.StringIO()
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with redirect_stdout(buffer):
                code = main(["--token-file", self.token_path])
        self.assertEqual(code, 3)
        self.assertIn("write_gate_enabled", buffer.getvalue())

    def test_cli_happy_path_has_no_secret(self):
        buffer = io.StringIO()
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "0",
                                     "SENDER_LIVE_SEND_ENABLED": "0"}):
            with patch("sender_readonly_check.readiness", return_value={
                "authenticated": True, "endpoints": {
                    "campaign_drafts": "ok", "groups": "ok"},
                "dispatch": "disabled",
            }):
                with redirect_stdout(buffer):
                    code = main(["--token-file", self.token_path])
        self.assertEqual(code, 0)
        self.assertIn('"authenticated": true', buffer.getvalue())
        self.assertNotIn("sender_fake_token_", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
