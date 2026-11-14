"""Offline-only tests of GitHub OIDC broker requester. No actual token or APK."""
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import kwai_spawndroid_oidc_cloud_audit as audit

class Response:
    status = 200
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, size=65536):
        return self.data

class ContractTests(unittest.TestCase):
    def test_denied_without_github_hosted_push(self):
        with patch.dict(os.environ, {
            "GITHUB_ACTIONS": "false", "GITHUB_REPOSITORY": audit.REPO,
            "GITHUB_REF": audit.BRANCH, "GITHUB_EVENT_NAME": "push",
            "RUNNER_TEMP": "/tmp",
        }, clear=True), patch.object(audit, "_get_oidc") as get:
            with self.assertRaisesRegex(audit.SplitError, "github_hosted_push_precondition_failed"):
                audit.audit_cloud()
            get.assert_not_called()

    def test_denied_cross_repo(self):
        with patch.dict(os.environ, {
            "GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "attacker/repo",
            "GITHUB_REF": audit.BRANCH, "GITHUB_EVENT_NAME": "push",
            "RUNNER_TEMP": "/tmp",
        }, clear=True), patch.object(audit, "_get_oidc") as get:
            with self.assertRaisesRegex(audit.SplitError, "github_hosted_push_precondition_failed"):
                audit.audit_cloud()
            get.assert_not_called()

    def test_denied_wrong_ref_or_pull_request(self):
        for event, ref in [("pull_request", audit.BRANCH), ("push", "refs/heads/main")]:
            with patch.dict(os.environ, {
                "GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": audit.REPO,
                "GITHUB_REF": ref, "GITHUB_EVENT_NAME": event, "RUNNER_TEMP": "/tmp",
            }, clear=True), patch.object(audit, "_get_oidc") as get:
                with self.assertRaisesRegex(audit.SplitError, "github_hosted_push_precondition_failed"):
                    audit.audit_cloud()
                get.assert_not_called()

    def test_oidc_request_uses_exact_audience(self):
        urls = []
        def read(request, timeout=0):
            urls.append(request.full_url)
            self.assertIn("Authorization", request.headers)
            self.assertNotIn("fake-token", request.full_url)
            return Response(json.dumps({"value": "x" * 110}).encode())
        env = {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://oidc.example.invalid/issue?foo=1",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fake-token",
        }
        with patch.dict(os.environ, env, clear=True), patch("urllib.request.urlopen", side_effect=read):
            self.assertEqual(len(audit._get_oidc()), 110)
        self.assertIn("audience=urn%3Aanthares%3Akwai%3Aapk-stage%3Av1", urls[0])

    def test_denied_without_runtime_token(self):
        with patch.dict(os.environ, {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://oidc.example.invalid/issue",
        }, clear=True):
            with self.assertRaisesRegex(audit.SplitError, "github_oidc_not_available"):
                audit._get_oidc()

    def test_broker_rejects_http403_without_leaking_token(self):
        def deny(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
        with patch("urllib.request.urlopen", side_effect=deny):
            with self.assertRaisesRegex(audit.SplitError, "broker_http_403") as cm:
                audit._fetch_manifest("SECRET_TEST_TOKEN")
            self.assertNotIn("SECRET_TEST_TOKEN", str(cm.exception))

    def test_broker_503_is_sanitized(self):
        def unavailable(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 503, "Service unavailable", None, None)
        with patch("urllib.request.urlopen", side_effect=unavailable):
            with self.assertRaisesRegex(audit.SplitError, "broker_http_503") as cm:
                audit._fetch_manifest("JWT_MUST_STAY_PRIVATE")
            self.assertNotIn("JWT_MUST_STAY_PRIVATE", str(cm.exception))

    def test_broker_never_sends_jwt_in_query(self):
        call = []
        def accept(req, timeout=0):
            call.append(req)
            return Response(b'{"package":"com.kwai.video","files":[]}')
        with patch("urllib.request.urlopen", side_effect=accept):
            audit._fetch_manifest("TEST_JWT_SHOULD_NOT_LOG")
        self.assertEqual(call[0].full_url, audit.URL)
        self.assertEqual(call[0].get_method(), "POST")
        self.assertEqual(call[0].headers["X-github-oidc-token"], "TEST_JWT_SHOULD_NOT_LOG")

    def test_tampered_manifest_fails_before_download(self):
        source = {
            "package": "com.kwai.video", "versionCode": 647103,
            "expiresAt": 9999999999, "files": []
        }
        with patch.dict(os.environ, {
            "GITHUB_ACTIONS":"true", "GITHUB_REPOSITORY":audit.REPO,
            "GITHUB_REF":audit.BRANCH, "GITHUB_EVENT_NAME":"push",
            "RUNNER_TEMP":"/tmp",
        }, clear=True), patch.object(audit,"_get_oidc",return_value="safe"), \
                patch.object(audit,"_fetch_manifest",return_value=source), \
                patch.object(audit,"download_and_verify") as dl:
            with self.assertRaises(audit.SplitError):
                audit.audit_cloud()
            dl.assert_not_called()

if __name__ == "__main__":
    unittest.main()
