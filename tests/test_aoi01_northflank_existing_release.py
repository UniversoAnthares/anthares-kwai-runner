"""Offline contract tests for the existing Northflank TikTok release gate.

Only mocked calls: no remote deployment, no TikTok upload, no real secrets.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import textwrap
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "northflank-tiktok-worker.yml"
EXPECTED = "2026-11-10-cdp-fast-status-v12"


def inline_python():
    source = WORKFLOW.read_text(encoding="utf-8")
    code = source.split("python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]
    return textwrap.dedent(code)


class Response:
    def __init__(self, code, payload):
        self.status = code
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


class NorthflankReleaseTests(unittest.TestCase):
    def simulate(self, routes, admin_token=""):
        calls = []

        def urlopen(request, timeout=30):
            url = request.full_url
            calls.append((request.get_method(), url))
            for fragment, response in routes:
                if fragment in url:
                    code, payload = response
                    if code >= 400:
                        raise urllib.error.HTTPError(url, code, "synthetic", {}, None)
                    return Response(code, payload)
            raise AssertionError("Unexpected remote request: " + url)

        stream = io.StringIO()
        error = None
        with mock.patch.dict(os.environ, {"ARA_SHARED": "synthetic-runtime-test-token",
                                          "NORTHFLANK_API_TOKEN": admin_token}, clear=True):
            with mock.patch.object(urllib.request, "urlopen", side_effect=urlopen):
                with mock.patch("time.sleep", return_value=None):
                    with contextlib.redirect_stdout(stream):
                        try:
                            exec(compile(inline_python(), str(WORKFLOW), "exec"), {"__name__": "__aoi01_test__"})
                        except SystemExit as exc:
                            error = str(exc)
        return error, calls, stream.getvalue()

    def test_existing_v12_works_without_admin_credential(self):
        error, calls, output = self.simulate([
            ("/interactive-browser/revision", (200, {"revision": EXPECTED})),
            ("/interactive-browser/status", (200, {"ok": True, "backend": "northflank_chromium_cdp"})),
        ])
        self.assertIsNone(error)
        self.assertIn("NF_RELEASE_ALREADY_CURRENT=1", output)
        self.assertIn("NORTHFLANK_EXISTING_BROWSER_V12_VERIFIED=1", output)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("api.northflank.com" not in url for _, url in calls))

    def test_runtime_unauthorized_fails_before_admin(self):
        error, calls, _ = self.simulate([
            ("/interactive-browser/revision", (401, {})),
        ], admin_token="synthetic-valid-looking-admin-token")
        self.assertEqual(error, "NORTHFLANK_RUNTIME_AUTH_REQUIRED")
        self.assertEqual(len(calls), 1)

    def test_stale_runtime_requires_administration(self):
        error, calls, _ = self.simulate([
            ("/interactive-browser/revision", (200, {"revision": "v11"})),
        ])
        self.assertEqual(error, "NORTHFLANK_ADMIN_AUTH_REQUIRED")
        self.assertEqual(len(calls), 1)

    def test_bad_admin_token_does_not_trigger_build(self):
        error, calls, _ = self.simulate([
            ("/interactive-browser/revision", (200, {"revision": "v11"})),
            ("api.northflank.com/v1/projects", (401, {})),
        ], admin_token="synthetic-valid-looking-admin-token")
        self.assertEqual(error, "NORTHFLANK_ADMIN_AUTH_REQUIRED")
        self.assertEqual(len(calls), 2)
        self.assertFalse(any(method == "POST" for method, _ in calls))

    def test_existing_version_requires_healthy_browser_status(self):
        error, calls, _ = self.simulate([
            ("/interactive-browser/revision", (200, {"revision": EXPECTED})),
            ("/interactive-browser/status", (200, {"ok": True, "backend": "other"})),
        ])
        self.assertEqual(error, "NORTHFLANK_STATUS_NOT_READY")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
