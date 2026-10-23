"""Buffer shared token HTTP 429 diagnostics without live requests or credential exposure."""
import contextlib
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from social_adapters import buffer_three_channels as b


class BufferRateLimitDiagnosticsTests(unittest.TestCase):
    def test_numeric_retry_after_preserved_and_bounded_for_shared_neon(self):
        error = urllib.error.HTTPError(
            b.ENDPOINT, 429, "rate limited",
            {"Retry-After": "2250", "RateLimit-Remaining": "0",
             "RateLimit-Limit": "120"}, None)
        out = io.StringIO()
        with patch.object(b.urllib.request, "urlopen", side_effect=error), contextlib.redirect_stdout(out):
            with self.assertRaisesRegex(b.BufferBlocked, "^BUFFER_HTTP_429$") as captured:
                b.api('query { account { organizations { id } } }', token="sensitive_fixture_never_print")
        self.assertEqual(captured.exception.retry_after_seconds, 2250)
        self.assertEqual(b.buffer_cooldown_seconds(captured.exception, 900), 2250)
        self.assertEqual(b.buffer_cooldown_seconds(captured.exception, 1800), 2250)
        diagnostic = json.loads(out.getvalue().strip())
        self.assertEqual(diagnostic["retry_after_seconds"], 2250)
        self.assertEqual(diagnostic["operation"], "account")
        self.assertEqual(diagnostic["rate_limit_remaining"], 0)
        self.assertNotIn("sensitive_fixture", out.getvalue())

    def test_no_retry_after_retains_existing_conservative_floor(self):
        e = b.BufferBlocked("BUFFER_HTTP_429")
        e.retry_after_seconds = None
        self.assertEqual(b.buffer_cooldown_seconds(e, 900), 900)
        self.assertEqual(b.buffer_cooldown_seconds(e, 1800), 1800)

    def test_backend_max_3600_respected(self):
        e = b.BufferBlocked("BUFFER_HTTP_429")
        e.retry_after_seconds = 7200
        self.assertEqual(b.buffer_cooldown_seconds(e, 1800), 3600)

    def test_non_numeric_headers_never_echoed(self):
        error = urllib.error.HTTPError(
            b.ENDPOINT, 429, "rate limited",
            {"Retry-After": "private_token_ABC", "RateLimit-Limit": "another-secret"}, None)
        output = io.StringIO()
        with patch.object(b.urllib.request, "urlopen", side_effect=error), contextlib.redirect_stdout(output):
            with self.assertRaises(b.BufferBlocked):
                b.api("query { posts(first: 2) { id } }", token="do_not_log")
        self.assertIsNone(json.loads(output.getvalue())["retry_after_seconds"])
        self.assertNotIn("secret", output.getvalue())
        self.assertNotIn("do_not_log", output.getvalue())

    def test_401_keeps_auth_error_without_429_telemetry(self):
        error = urllib.error.HTTPError(b.ENDPOINT, 401, "unauthorized", {}, None)
        output = io.StringIO()
        with patch.object(b.urllib.request, "urlopen", side_effect=error), contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(b.BufferBlocked, "^BUFFER_HTTP_401$"):
                b.api("query { account { id } }", token="do_not_log")
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
