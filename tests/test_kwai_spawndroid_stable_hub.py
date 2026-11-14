"""Offline WebDriver/Appium proof, readback and fail-closed lifecycle tests.

All HTTP requests are mocked; these tests never allocate Android minutes.
"""
import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "tools" / "kwai_spawndroid_stable_hub.py"
spec = importlib.util.spec_from_file_location("kwai_spawndroid_stable_hub", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Resp:
    def __init__(self, data):
        self.body = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, length=65536):
        return self.body[:length]


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.package = mod.KWAIPKG
        self.activate_ok = True
        self.state = 4
        self.source = "<hierarchy><node package='com.kwai.video'/></hierarchy>"
        self.delete_ok = True
        self.terminal_state = "stopped"
        self.active_sessions = []
        self.session_id = "webdriver_abc123456789"
        self.provider_id = "sess_abc123456789"

    @staticmethod
    def _error(req, code):
        return urllib.error.HTTPError(
            req.full_url, code, "backend", {},
            io.BytesIO(b'{"token":"DO_NOT_LOG"}'))

    def __call__(self, req, timeout=None):
        method = req.get_method()
        url = req.full_url
        if url.startswith(mod.HUB):
            path = url[len(mod.HUB):]
            channel = "hub"
        elif url.startswith(mod.API):
            path = url[len(mod.API):]
            channel = "api"
        else:
            raise AssertionError("unexpected host")
        self.calls.append((channel, method, path, req))
        if (channel, method, path) == ("api", "GET", "/api/apps"):
            return Resp({"apps": [{"slug": "official-kwai",
                                    "packageName": self.package}]})
        if (channel, method, path) == ("api", "GET", "/api/device-profiles"):
            return Resp({"profiles": [{"id": "android-14-phone"}]})
        if (channel, method, path) == ("api", "GET", "/api/sessions"):
            return Resp({"sessions": self.active_sessions})
        if channel == "api" and method == "GET" and path == (
                "/api/v1/sessions/" + self.provider_id):
            return Resp({"state": self.terminal_state})
        if (channel, method, path) == ("hub", "POST", "/session"):
            data = json.loads(req.data)
            assert data["capabilities"]["alwaysMatch"]["spawndroid:app"] == "official-kwai"
            return Resp({"value": {"sessionId": self.session_id,
                                   "capabilities": {
                                       "spawndroid:appPackage": self.package,
                                       "spawndroid:sessionId": self.provider_id,
                                       "appium:udid": "android-arm64-device-1",
                                       "platformVersion": "14"}}})
        if channel == "hub" and method == "POST" and path.endswith("/execute/sync"):
            script = json.loads(req.data)["script"]
            if script == "mobile: activateApp":
                if not self.activate_ok:
                    raise self._error(req, 502)
                return Resp({"value": None})
            if script == "mobile: queryAppState":
                return Resp({"value": self.state})
        if channel == "hub" and method == "GET" and path.endswith("/source"):
            return Resp({"value": self.source})
        if channel == "hub" and method == "DELETE" and path.startswith(
                "/session/" + self.session_id + "?result="):
            if not self.delete_ok:
                raise self._error(req, 502)
            return Resp({"value": None})
        raise AssertionError("unexpected request " + channel + " " + method + " " + path)


class TestHub(unittest.TestCase):
    def setUp(self):
        self.transport = FakeTransport()
        self.hub = mod.SpawnDroidHub("FAKE_CI_TOKEN",
                                    transport=self.transport,
                                    api_token="FAKE_API_TOKEN",
                                    api_transport=self.transport)

    def run_canary(self, **kwargs):
        return self.hub.verify_kwai_once(
            "official-kwai", enable=True, free_hobby=True,
            verified_slug="official-kwai", **kwargs)

    def hub_methods(self):
        return [item[1] for item in self.transport.calls if item[0] == "hub"]

    def test_credentials_required(self):
        with self.assertRaisesRegex(mod.HubError, "hub_token_missing"):
            mod.SpawnDroidHub("")
        with self.assertRaisesRegex(mod.HubError, "api_readback_key_missing"):
            mod.SpawnDroidHub("fake").verify_kwai_once(
                "official-kwai", enable=True, free_hobby=True,
                verified_slug="official-kwai")
        self.assertEqual(self.transport.calls, [])

    def test_explicit_gates_before_any_http(self):
        for enable, free in ((False, False), (True, False), (False, True)):
            with self.assertRaisesRegex(mod.HubError, "launch_guard_disabled"):
                self.hub.verify_kwai_once("official-kwai", enable=enable,
                                          free_hobby=free,
                                          verified_slug="official-kwai")
        with self.assertRaisesRegex(mod.HubError, "agent01_verified_slug_required"):
            self.hub.verify_kwai_once("official-kwai", enable=True, free_hobby=True)
        for bad in ("", "../private", "https://host", "a b", "/"):
            with self.assertRaises(mod.HubError):
                self.hub.verify_kwai_once(bad, enable=True, free_hobby=True,
                                          verified_slug=bad)
        self.assertEqual(self.transport.calls, [])

    def test_full_foreground_source_and_terminal_evidence(self):
        proof = self.run_canary()
        self.assertEqual(proof["package"], mod.KWAIPKG)
        self.assertEqual(proof["android_version"], "14")
        self.assertTrue(proof["device_serial"])
        self.assertEqual(proof["foreground_state"], 4)
        self.assertTrue(proof["ui_source_accessible"])
        self.assertTrue(proof["provider_terminal_confirmed"])
        self.assertEqual(proof["provider_terminal_state"], "stopped")
        self.assertFalse(proof["publication_attempted"])
        self.assertEqual(self.hub_methods(),
                         ["POST", "POST", "POST", "GET", "DELETE"])
        self.assertEqual(self.transport.calls[-1][2],
                         "/api/v1/sessions/" + self.transport.provider_id)
        self.assertEqual(len(proof["web_driver_session_ref"]), 16)

    def test_wrong_installed_package_is_not_activated(self):
        self.transport.package = "com.other.app"
        with self.assertRaisesRegex(mod.HubError, "registered_official_kwai_missing"):
            self.run_canary()
        self.assertEqual(self.hub_methods(), [])

    def test_concurrent_runner_blocks_allocation(self):
        self.transport.active_sessions = [{"state": "ready", "id": "another"}]
        with self.assertRaisesRegex(mod.HubError, "workspace_sessions_conflict"):
            self.run_canary()
        self.assertEqual(self.hub_methods(), [])

    def test_foreground_failure_reports_failed_then_closes(self):
        self.transport.state = 3
        with self.assertRaisesRegex(mod.HubError, "kwai_foreground_unverified"):
            self.run_canary()
        self.assertEqual(self.hub_methods()[-1], "DELETE")
        self.assertIn("result=failed", self.transport.calls[-2][2])

    def test_ui_source_failure_reports_failed_then_closes(self):
        self.transport.source = ""
        with self.assertRaisesRegex(mod.HubError, "ui_source_unverified"):
            self.run_canary()
        self.assertIn("result=failed", self.transport.calls[-2][2])

    def test_activation_exception_still_tears_down(self):
        self.transport.activate_ok = False
        with self.assertRaisesRegex(mod.HubError, "host_unavailable"):
            self.run_canary()
        self.assertIn("result=failed", self.transport.calls[-2][2])

    def test_delete_failure_requires_manual_reconciliation(self):
        self.transport.delete_ok = False
        with self.assertRaisesRegex(mod.HubError, "reconcile_required"):
            self.run_canary()
        self.assertEqual(self.hub_methods()[-1], "DELETE")

    def test_terminal_readback_failure_does_not_claim_success(self):
        self.transport.terminal_state = "ready"
        with patch.object(mod.time, "sleep", lambda _: None):
            with self.assertRaisesRegex(mod.HubError, "reconcile_required"):
                self.run_canary()
        self.assertEqual(self.hub_methods()[-1], "DELETE")

    def test_secrets_are_never_copied_into_errors(self):
        self.transport.activate_ok = False
        with self.assertRaises(mod.HubError) as ctx:
            self.run_canary()
        self.assertNotIn("FAKE_CI_TOKEN", str(ctx.exception))
        self.assertNotIn("FAKE_API_TOKEN", str(ctx.exception))
        self.assertNotIn("DO_NOT_LOG", str(ctx.exception))

    def test_no_publication_or_neon_api_contract(self):
        code = PATH.read_text()
        for forbidden in ("kwai-lease", "kwai-start", "kwai-confirm",
                          "mobile: click"):
            self.assertNotIn(forbidden, code)


if __name__ == "__main__":
    unittest.main()
