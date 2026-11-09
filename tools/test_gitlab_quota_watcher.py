#!/usr/bin/env python3
"""Offline regression tests for Anthares CI quota dispatch. No remote calls."""
import datetime as dt
import unittest
from unittest.mock import patch
import gitlab_quota_watcher as mod


class QuotaWatcherContract(unittest.TestCase):
    def test_each_system_dispatches_its_own_component(self):
        invocations = []
        def event(project_id):
            return {"id": int(project_id), "sha": str(project_id).zfill(40), "count": 1}
        with patch.object(mod, "GL_AUTH", "test-only"), \
             patch.object(mod, "GH_AUTH", "test-only"), \
             patch.object(mod, "DRY_RUN", False), \
             patch.object(mod, "reserve_quota_handoff", return_value="RESERVED"), \
             patch.object(mod, "acknowledge_quota_dispatch", return_value=True), \
             patch.object(mod, "recent_qualifying_failure", side_effect=event), \
             patch.object(mod, "confirmed_terminal_before_reserve", return_value=True), \
             patch.object(mod, "latest_runs", return_value=[]), \
             patch.object(mod, "dispatch", side_effect=lambda component, workflow, e: invocations.append((component, workflow))):
            self.assertEqual(mod.main(), 0)
        self.assertEqual(invocations, [
            ("cortes", "gitlab-quota-fallback.yml"),
            ("clipper", "private-ci-quota-rescue.yml"),
            ("wordpress", "private-ci-quota-rescue.yml"),
        ])

    def test_dedupe_by_component_and_sha(self):
        sha = "a" * 40
        run = {"display_title": "quota-rescue-wordpress-glsha-" + sha,
               "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "event": "workflow_dispatch"}
        self.assertTrue(mod.already_handled("wordpress", "private-ci-quota-rescue.yml", sha, [run]))
        self.assertFalse(mod.already_handled("clipper", "private-ci-quota-rescue.yml", sha, [run]))

    def test_one_shot_cooldown_allows_distinct_sha_only_after_terminal(self):
        sha = "ca4e7a0dbd2c7a72ba0b4ae953688213f49f845d"
        previous = {"display_title": "quota-rescue-cortes-glsha-" + "b" * 40,
                    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "event": "workflow_dispatch", "status": "completed"}
        with patch.object(mod, "HISTORICAL_AOI8_ONCE", True):
            self.assertFalse(mod.already_handled("cortes", "gitlab-quota-fallback.yml", sha, [previous]))
            previous["status"] = "in_progress"
            self.assertTrue(mod.already_handled("cortes", "gitlab-quota-fallback.yml", sha, [previous]))
            previous["status"] = "completed"
            previous["display_title"] = "quota-rescue-cortes-glsha-" + sha
            self.assertTrue(mod.already_handled("cortes", "gitlab-quota-fallback.yml", sha, [previous]))
        previous["display_title"] = "quota-rescue-cortes-glsha-" + "b" * 40
        with patch.object(mod, "HISTORICAL_AOI8_ONCE", False):
            self.assertTrue(mod.already_handled("cortes", "gitlab-quota-fallback.yml", sha, [previous]))

    def test_no_dispatch_on_nonquota_failure(self):
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        def fake_api(url, *args, **kwargs):
            if "/pipelines?" in url:
                return [{"id": 100, "ref": "main", "sha": "f" * 40, "created_at": now}]
            return [{"failure_reason": "script_failure", "started_at": None}]
        with patch.object(mod, "api", side_effect=fake_api):
            self.assertIsNone(mod.recent_qualifying_failure("87361776"))


    def test_single_real_terminal_quota_backlog_is_eligible(self):
        historical = "2026-10-30T19:38:08Z"
        original = {
            "id": 3010062525,
            "ref": "main",
            "sha": "ca4e7a0dbd2c7a72ba0b4ae953688213f49f845d",
            "status": "failed",
            "created_at": historical,
        }
        quota_job = {"failure_reason": "ci_quota_exceeded",
                     "status": "failed", "started_at": None}
        newer = {"id": 3010066125, "ref": "main",
                 "sha": "27beeff7fba0341ae0ebb2ee681d7de975a56597",
                 "status": "failed", "created_at": historical}
        def fake_api(url, *args, **kwargs):
            return [newer, original] if "/pipelines?" in url else [quota_job]
        with patch.object(mod, "api", side_effect=fake_api), \
             patch.object(mod, "HISTORICAL_AOI8_ONCE", True):
            self.assertEqual(mod.recent_qualifying_failure("87307248")["id"], 3010062525)
            self.assertIsNone(mod.recent_qualifying_failure("87361774"))
            original["sha"] = "f" * 40
            self.assertIsNone(mod.recent_qualifying_failure("87307248"))
        with patch.object(mod, "api", side_effect=fake_api), \
             patch.object(mod, "HISTORICAL_AOI8_ONCE", False):
            self.assertIsNone(mod.recent_qualifying_failure("87307248"))

    def test_quota_backup_pins_original_sha_without_publisher(self):
        from pathlib import Path
        yaml_path = Path(__file__).resolve().parents[1] / ".github/workflows/gitlab-quota-fallback.yml"
        content = yaml_path.read_text(encoding="utf-8")
        self.assertIn("AOI_EXACT_SOURCE_SHA: ${{ inputs.gitlab_sha }}", content)
        self.assertIn('git -C source checkout --quiet --detach "$AOI_EXACT_SOURCE_SHA"', content)
        self.assertNotIn("cortes_youtube_shorts_cloud.py", content)

    def test_timeout_retries_only_safe_read(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"ok":true}'
        with patch.object(mod.urllib.request, "urlopen",
                          side_effect=[TimeoutError("transient"), Response()]) as open_mock, \
             patch.object(mod.time, "sleep") as sleep_mock:
            result = mod.api("https://gitlab.com/api/v4/health", "test", gl=True)
        self.assertEqual(result, {"ok": True})
        self.assertEqual(open_mock.call_count, 2)
        sleep_mock.assert_called_once()

    def test_timeout_in_cortes_does_not_skip_private_projects(self):
        called = []
        def source(project_id):
            if project_id == "87307248":
                raise TimeoutError("GitLab temporarily unavailable")
            return {"id": 5, "sha": project_id.zfill(40), "count": 1}
        with patch.object(mod, "GL_AUTH", "fixture"), \
             patch.object(mod, "GH_AUTH", "fixture"), \
             patch.object(mod, "DRY_RUN", False), \
             patch.object(mod, "reserve_quota_handoff", return_value="RESERVED"), \
             patch.object(mod, "acknowledge_quota_dispatch", return_value=True), \
             patch.object(mod, "recent_qualifying_failure", side_effect=source), \
             patch.object(mod, "confirmed_terminal_before_reserve", return_value=True), \
             patch.object(mod, "latest_runs", return_value=[]), \
             patch.object(mod, "dispatch", side_effect=lambda component, workflow, event: called.append(component)):
            self.assertEqual(mod.main(), 1)
        self.assertEqual(called, ["clipper", "wordpress"])


    def test_exact_old_receipt_uses_authenticated_controller_without_new_dispatch(self):
        fields = {
            "ANTHARES_RECONCILE_ONLY": "true",
            "ANTHARES_RECONCILE_COMPONENT": "cortes",
            "ANTHARES_RECONCILE_PROJECT_ID": "87307248",
            "ANTHARES_RECONCILE_PIPELINE_ID": "3005500025",
            "ANTHARES_RECONCILE_SHA": "94ba06e628d0b1ba0bdfeabbdfd9a00b86508759",
            "ANTHARES_RECONCILE_GITHUB_RUN_ID": "40942048873",
        }
        with patch.dict(mod.os.environ, fields), \
             patch.object(mod, "GH_AUTH", "fixture"), \
             patch.object(mod, "DRY_RUN", False), \
             patch.object(mod, "confirm_successful_quota_handoff", return_value=True) as confirm, \
             patch.object(mod, "dispatch") as dispatch, \
             patch.object(mod, "api") as api:
            self.assertEqual(mod.main(), 0)
        confirm.assert_called_once_with("cortes", "87307248",
            {"id": 3005500025, "sha": fields["ANTHARES_RECONCILE_SHA"]},
            {"id": 40942048873})
        dispatch.assert_not_called()
        api.assert_not_called()

    def test_exact_receipt_neon_controller_requires_full_historical_tuple(self):
        class FakeReply:
            def __init__(self, value):
                self.value = value
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return mod.json.dumps(self.value).encode()

        sha = "94ba06e628d0b1ba0bdfeabbdfd9a00b86508759"
        observed = []
        def mocked(request, timeout=None):
            url = request.full_url
            observed.append(url)
            if "request-id-token" in url:
                return FakeReply({"value": "fixture-oidc"})
            if url == ("https://br-crimson-unit-b89nau08-cquotarec"
                        ".compute.c-14.us-east-1.aws.neon.tech/"):
                return FakeReply({"ok": True, "state": "FALLBACK_CONFIRMED"})
            if url.endswith("/api/gitlab-confirm"):
                return FakeReply({"ok": False, "state": "UNCONFIRMED"})
            raise AssertionError("Unexpected endpoint: " + url)

        fields = {
            "ANTHARES_RECONCILE_ONLY": "true",
            "ANTHARES_CI_QUOTA_LEDGER_URL":
                "https://anthares-ci-quota-controller.vercel.app/api/gitlab-reserve",
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.test/request-id-token",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-access",
        }
        with patch.dict(mod.os.environ, fields), \
             patch.object(mod, "GH_AUTH", "fixture-gh-token"), \
             patch.object(mod.urllib.request, "urlopen", side_effect=mocked):
            self.assertTrue(mod.confirm_successful_quota_handoff(
                "cortes", "87307248", {"id": 3005500025, "sha": sha},
                {"id": 40942048873}))
            self.assertFalse(mod.confirm_successful_quota_handoff(
                "cortes", "87307248", {"id": 3005500026, "sha": sha},
                {"id": 40942048873}))
        self.assertEqual(observed.count(
            "https://br-crimson-unit-b89nau08-cquotarec"
            ".compute.c-14.us-east-1.aws.neon.tech/"), 1)

    def test_exact_receipt_fails_closed_on_invalid_sha(self):
        fields = {"ANTHARES_RECONCILE_ONLY": "true",
            "ANTHARES_RECONCILE_COMPONENT": "cortes",
            "ANTHARES_RECONCILE_PROJECT_ID": "87307248",
            "ANTHARES_RECONCILE_PIPELINE_ID": "3005500025",
            "ANTHARES_RECONCILE_SHA": "not-a-sha",
            "ANTHARES_RECONCILE_GITHUB_RUN_ID": "40942048873"}
        with patch.dict(mod.os.environ, fields), \
             patch.object(mod, "GH_AUTH", "fixture"), \
             patch.object(mod, "DRY_RUN", False), \
             patch.object(mod, "confirm_successful_quota_handoff") as confirm:
            self.assertEqual(mod.main(), 2)
        confirm.assert_not_called()

    def test_exact_receipt_dry_run_has_no_write(self):
        fields = {"ANTHARES_RECONCILE_ONLY": "true",
            "ANTHARES_RECONCILE_COMPONENT": "cortes",
            "ANTHARES_RECONCILE_PROJECT_ID": "87307248",
            "ANTHARES_RECONCILE_PIPELINE_ID": "3005500025",
            "ANTHARES_RECONCILE_SHA": "94ba06e628d0b1ba0bdfeabbdfd9a00b86508759",
            "ANTHARES_RECONCILE_GITHUB_RUN_ID": "40942048873"}
        with patch.dict(mod.os.environ, fields), \
             patch.object(mod, "DRY_RUN", True), \
             patch.object(mod, "confirm_successful_quota_handoff") as confirm:
            self.assertEqual(mod.main(), 0)
        confirm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
