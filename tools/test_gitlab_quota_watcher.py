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


if __name__ == "__main__":
    unittest.main()
