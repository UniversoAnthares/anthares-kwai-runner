"""No-network synthetic contracts for the one-shot SpawnDroid Android installer."""
from __future__ import annotations
from contextlib import contextmanager
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import kwai_spawndroid_cloud_install_canary as canary


def example_env(root):
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": canary.source.REPO,
        "GITHUB_REF": canary.source.BRANCH,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "1",
        "SPAWNDROID_HOBBY_FREE_CONFIRMED": "1",
        "SPAWNDROID_API_KEY": "SYNTHETIC_TEST_KEY_000000",
        "SPAWNDROID_DEMO_ARTIFACT_SLUG": canary.ARTIFACT,
        "GITHUB_RUN_ID": "43699988888",
        "GITHUB_RUN_ATTEMPT": "1",
        "RUNNER_TEMP": root,
    }


class CanaryContracts(unittest.TestCase):
    def test_missing_key_fails_without_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            del env["SPAWNDROID_API_KEY"]
            with patch.object(canary, "preflight_workspace") as pre:
                with self.assertRaisesRegex(canary.CanaryBlocked, "official_api_key_missing"):
                    canary.run_real_canary(env)
                pre.assert_not_called()
        print("SPAWNDROID_CANARY_KEY_GUARD=PASS")

    def test_free_allowance_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            env["SPAWNDROID_HOBBY_FREE_CONFIRMED"] = "0"
            with patch.object(canary, "preflight_workspace") as pre:
                with self.assertRaisesRegex(canary.CanaryBlocked, "hobby_free_confirmed_disabled"):
                    canary.run_real_canary(env)
                pre.assert_not_called()

    def test_only_manual_workflow_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            env["GITHUB_EVENT_NAME"] = "push"
            with self.assertRaisesRegex(canary.CanaryBlocked, "gate_github_event_name_disabled"):
                canary.required_gates(env)

    def test_wrong_repository_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            env["GITHUB_REPOSITORY"] = "someone/else"
            with self.assertRaisesRegex(canary.CanaryBlocked, "gate_github_repository_disabled"):
                canary.required_gates(env)

    def test_wrong_slug_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            env["SPAWNDROID_DEMO_ARTIFACT_SLUG"] = "not-demo"
            with self.assertRaisesRegex(canary.CanaryBlocked, "demo_artifact_identity_unverified"):
                canary.required_gates(env)

    def test_idempotency_key_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            a = canary.required_gates(env)
            b = canary.required_gates(env)
            self.assertEqual(a, b)
            self.assertEqual(a[1], "kwai-item1-43699988888-1")

    def test_preflight_requires_demo(self):
        def fake(method, path, key, **kw):
            if path.endswith("/api/apps"):
                return {"apps": [{"slug": "foreign-app"}]}
            raise AssertionError("sessions must not be read")
        with self.assertRaisesRegex(canary.CanaryBlocked, "authorized_demo_artifact_missing"):
            canary.preflight_workspace("dummy-key", request=fake)

    def test_live_session_blocks_provisioning(self):
        def fake(method, path, key, **kw):
            if path.endswith("/api/apps"):
                return {"apps": [{"slug": canary.ARTIFACT}]}
            return {"sessions": [{"sessionId": "sess_active_123456",
                                  "status": "ready", "endedAt": None}]}
        with self.assertRaisesRegex(canary.CanaryBlocked, "live_or_unknown_session"):
            canary.preflight_workspace("dummy-key", request=fake)

    def test_unknown_session_blocks_provisioning(self):
        def fake(method, path, key, **kw):
            if path.endswith("/api/apps"):
                return {"apps": [{"slug": canary.ARTIFACT}]}
            return {"sessions": [{"sessionId": "sess_unknown_123", "status": ""}]}
        with self.assertRaisesRegex(canary.CanaryBlocked, "live_or_unknown_session"):
            canary.preflight_workspace("dummy-key", request=fake)

    def test_ended_sessions_pass_preflight(self):
        def fake(method, path, key, **kw):
            if path.endswith("/api/apps"):
                return {"apps": [{"slug": canary.ARTIFACT}]}
            return {"sessions": [{"sessionId": "sess_stopped_123",
                                  "status": "terminated", "endedAt": None}]}
        self.assertTrue(canary.preflight_workspace("dummy-key", request=fake))

    def test_bad_webdriver_host_denied(self):
        for url in ["http://stream.spawndroid.io/ci/x/wd/hub",
                    "https://evil.example.com/ci/x/wd/hub",
                    "https://stream.spawndroid.io/not-ci/wd/hub"]:
            with self.assertRaisesRegex(canary.CanaryBlocked, "webdriver_endpoint_invalid"):
                canary._webdriver_endpoint(url)

    def test_teardown_requires_provider_readback(self):
        sid = "sess_abcdefghijkl"
        def fake(method, url, token="", **kw):
            if method == "DELETE":
                return {"ok": True}
            return {"sessions": [{"sessionId": sid, "status": "ready", "endedAt": None}]}
        with self.assertRaisesRegex(canary.CanaryBlocked, "device_teardown_not_confirmed"):
            canary._close_session(sid, "fake", passed=False, request=fake)

    def test_teardown_success(self):
        sid = "sess_abcdefghijkl"
        seen = []
        def fake(method, url, token="", **kw):
            seen.append((method, kw.get("body")))
            if method == "DELETE":
                return {"ok": True}
            return {"sessions": [{"sessionId": sid, "status": "terminated",
                                  "endedAt": "2026-11-14T21:10:00Z"}]}
        self.assertTrue(canary._close_session(sid, "fake", passed=True, request=fake))
        self.assertEqual(seen[0], ("DELETE", {"result": "passed"}))

    def test_webdriver_execute_contract(self):
        calls = []
        def fake(method, url, token="", **kw):
            calls.append((method, url, kw["body"]))
            return {"value": True}
        exec_fn = canary.webdriver_executor(
            "https://stream.spawndroid.io/ci/sess_abcdefghijkl/tok_secret/wd/hub",
            "1234567890", request=fake)
        self.assertTrue(exec_fn("mobile: isAppInstalled", {"appId": canary.PACKAGE}))
        self.assertEqual(calls[0][2]["script"], "mobile: isAppInstalled")
        self.assertEqual(calls[0][2]["args"][0]["appId"], canary.PACKAGE)

    def synthetic_run(self, *, install_raises=False):
        with tempfile.TemporaryDirectory() as tmp:
            env = example_env(tmp)
            apk_entries = [
                {"name": "base.apk" if i == 0 else f"split_{i}.apk",
                 "url": "https://anthares.us/signed/fake/" + str(i) + ".apk"}
                for i in range(25)
            ]
            doc = {"package": canary.PACKAGE, "versionCode": canary.VERSION,
                   "files": apk_entries}
            parsed = dict(doc, bytes=canary.SIGNED_BYTES)
            receipts = {"signed_splits_verified": True,
                        "count": 25, "bytes": canary.SIGNED_BYTES,
                        "cert": canary.splits.guard.EXPECTED_CERT_SHA256}
            calls = []
            def fake_request(method, url, token="", **kwargs):
                calls.append((method, url, kwargs))
                if method == "POST" and url.endswith("/api/v1/sessions"):
                    return {"sessionId": "sess_abcdefghijklmno",
                            "webdriverUrl": "https://stream.spawndroid.io/ci/x/tok_wd/wd/hub",
                            "device": {"serial": "127.0.0.1:5555"}}
                if method == "POST" and url.endswith("/wd/hub/session"):
                    return {"value": {"sessionId": "abcdefghijklmno"}}
                if method == "POST" and "/execute/sync" in url:
                    return {"value": 4}
                return {"ok": True}
            def install(*args, **kwargs):
                if install_raises:
                    raise canary.splits.SplitError("synthetic_install_failed")
                return {"installed": True}
            with patch.object(canary, "preflight_workspace", return_value=True), \
                 patch.object(canary, "verify_cloud_source", return_value=(doc, parsed)), \
                 patch.object(canary.splits, "download_and_verify", return_value=receipts), \
                 patch.object(canary.splits, "webdriver_script", side_effect=install), \
                 patch.object(canary, "_get_ready", return_value={
                    "state": "ready",
                    "webdriverUrl": "https://stream.spawndroid.io/ci/x/tok_wd/wd/hub",
                    "device": {"serial": "127.0.0.1:5555"},
                 }), \
                 patch.object(canary, "_close_session", return_value=True) as closed:
                if install_raises:
                    with self.assertRaisesRegex(canary.splits.SplitError, "synthetic_install_failed"):
                        canary.run_real_canary(env, request=fake_request)
                    closed.assert_called_once()
                    self.assertFalse(closed.call_args.kwargs["passed"])
                else:
                    result = canary.run_real_canary(env, request=fake_request)
                    self.assertTrue(result["installed"])
                    self.assertTrue(result["foreground"])
                    self.assertFalse(result["published"])
                    closed.assert_called_once()
                    self.assertTrue(closed.call_args.kwargs["passed"])
            sessions = [x for x in calls if x[0] == "POST" and
                        x[1].endswith("/api/v1/sessions")]
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0][2]["headers"]["Idempotency-Key"],
                             "kwai-item1-43699988888-1")
            self.assertTrue(any(x[0] == "DELETE" and x[1].endswith("/session/abcdefghijklmno")
                                for x in calls))
            self.assertFalse(any("/publish" in x[1] or "/login" in x[1] for x in calls))

    def test_remote_install_and_teardown_contract(self):
        self.synthetic_run(install_raises=False)
        print("SPAWNDROID_ONE_SHOT_INSTALL_TEARDOWN_SYNTHETIC=PASS")

    def test_install_failure_teardown_contract(self):
        self.synthetic_run(install_raises=True)
        print("SPAWNDROID_ONE_SHOT_FAIL_CLOSED_TEARDOWN_SYNTHETIC=PASS")


if __name__ == "__main__":
    unittest.main()
