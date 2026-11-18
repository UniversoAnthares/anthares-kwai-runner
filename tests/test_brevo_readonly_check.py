"""No-network tests for the private-file Brevo health check."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from brevo_marketing import BrevoMarketing, BrevoAPIError
from brevo_readonly_check import key_from_private_file, read_only_status, main


class ReadOnlyCheckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "api-key.txt")
        with open(self.path, "w", encoding="utf-8") as stream:
            stream.write("xkeysib-" + "A" * 54 + "\n")
        os.chmod(self.path, 0o600)

    def tearDown(self):
        self.folder.cleanup()

    def test_key_requires_private_permissions(self):
        self.assertTrue(key_from_private_file(self.path).startswith("xkeysib-"))
        os.chmod(self.path, 0o644)
        with self.assertRaises(PermissionError):
            key_from_private_file(self.path)

    def test_key_must_be_valid(self):
        with open(self.path, "w", encoding="utf-8") as stream:
            stream.write("invalid")
        with self.assertRaises(ValueError):
            key_from_private_file(self.path)

    def test_readonly_status_never_exposes_identity_or_secret(self):
        calls = []
        def transport(method, path, body):
            calls.append((method, path))
            return {"email": "private@example.org", "key": "unprintable"}
        client = BrevoMarketing(api_key="xkeysib-secret", transport=transport)
        result = read_only_status(client)
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["sending"], "disabled")
        self.assertTrue(all(method == "GET" for method, _ in calls))
        self.assertNotIn("private@example.org", json.dumps(result))
        self.assertNotIn("unprintable", json.dumps(result))

    def test_provider_error_fails_readiness(self):
        def transport(method, path, body):
            if path == "/account":
                raise BrevoAPIError(403)
            return {}
        client = BrevoMarketing(transport=transport)
        report = read_only_status(client)
        self.assertFalse(report["authenticated"])
        self.assertEqual(report["read_endpoints"]["account"], "http_403")

    def test_cli_refuses_any_live_write_gate(self):
        buf = io.StringIO()
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with redirect_stdout(buf):
                code = main(["--key-file", self.path])
        self.assertEqual(code, 3)
        self.assertIn("write_gate_enabled", buf.getvalue())

    def test_cli_readonly_validated_without_network(self):
        buf = io.StringIO()
        safe_flags = {key: "0" for key in (
            "BREVO_LIVE_SEND_ENABLED", "BREVO_DRAFT_WRITE_ENABLED",
            "BREVO_CONTACT_SYNC_ENABLED", "BREVO_TEST_SEND_ENABLED",
        )}
        with patch.dict(os.environ, safe_flags):
            with patch("brevo_readonly_check.read_only_status",
                       return_value={"authenticated": True, "read_endpoints":
                                     {"account": "ok", "lists": "ok", "campaigns": "ok"},
                                     "sending": "disabled"}):
                with redirect_stdout(buf):
                    code = main(["--key-file", self.path])
        self.assertEqual(code, 0)
        report = json.loads(buf.getvalue())
        self.assertTrue(report["authenticated"])
        self.assertNotIn("xkeysib-", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
