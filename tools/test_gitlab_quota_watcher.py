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

    def test_no_dispatch_on_nonquota_failure(self):
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        def fake_api(url, *args, **kwargs):
            if "/pipelines?" in url:
                return [{"id": 100, "ref": "main", "sha": "f" * 40, "created_at": now}]
            return [{"failure_reason": "script_failure", "started_at": None}]
        with patch.object(mod, "api", side_effect=fake_api):
            self.assertIsNone(mod.recent_qualifying_failure("87361776"))


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
             patch.object(mod, "recent_qualifying_failure", side_effect=source), \
             patch.object(mod, "confirmed_terminal_before_reserve", return_value=True), \
             patch.object(mod, "latest_runs", return_value=[]), \
             patch.object(mod, "dispatch", side_effect=lambda component, workflow, event: called.append(component)):
            self.assertEqual(mod.main(), 1)
        self.assertEqual(called, ["clipper", "wordpress"])


    def test_stale_successful_successor_reconciles_without_dispatch(self):
        sha = "a" * 40
        run = {"id": 12345, "event": "workflow_dispatch", "status": "completed",
               "conclusion": "success",
               "display_title": "quota-rescue-cortes-glsha-" + sha,
               "created_at": (dt.datetime.now(dt.timezone.utc) -
                              dt.timedelta(hours=30)).isoformat()}
        pipeline = {"id": 3005500025, "sha": sha, "ref": "main",
                    "status": "failed"}
        with patch.object(mod, "GL_AUTH", "fixture"), \\
             patch.object(mod, "api", return_value=[pipeline]) as api_mock, \\
             patch.object(mod, "confirm_successful_quota_handoff",
                          return_value=True) as confirm_mock, \\
             patch.object(mod, "dispatch") as dispatch_mock:
            result = mod.reconcile_stale_successful_handoffs(
                "cortes", "87307248", "gitlab-quota-fallback.yml", [run])
        self.assertEqual(result, 1)
        api_mock.assert_called_once()
        confirm_mock.assert_called_once()
        dispatch_mock.assert_not_called()

    def test_stale_reconciliation_rejects_unproven_run(self):
        run = {"id": 12345, "event": "workflow_dispatch", "status": "completed",
               "conclusion": "failure",
               "display_title": "quota-rescue-cortes-glsha-" + "a" * 40,
               "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        with patch.object(mod, "api") as api_mock, \\
             patch.object(mod, "confirm_successful_quota_handoff") as confirm:
            result = mod.reconcile_stale_successful_handoffs(
                "cortes", "87307248", "gitlab-quota-fallback.yml", [run])
        self.assertEqual(result, 0)
        api_mock.assert_not_called()
        confirm.assert_not_called()



if __name__ == "__main__":
    unittest.main()
