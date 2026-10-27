"""Safe Harness quota watcher contract; no provider, GitHub, or Neon traffic."""
import datetime as dt
import os
import unittest
from unittest.mock import patch

from tools import ci_quota_harness_watcher as watcher
from tools.ci_quota_provider_adapters import HarnessPipelineRun

EXEC = "kbHfz70fTUiuYNoGx-QoBA"
SHA = "a" * 40


def detail(status="Running", code="quota_exceeded"):
    return {"status": "SUCCESS", "data": {"pipelineExecutionSummary": {
        "planExecutionId": EXEC, "pipelineIdentifier": watcher.PIPELINE,
        "orgIdentifier": watcher.ORG, "projectIdentifier": watcher.PROJECT,
        "status": status,
        "failureInfo": {"responseMessages": [{"code": code}]}
    }}}


def gh_status(*, creator=81930373, path=None, status="failure"):
    path = path or (
        "https://app.harness.io/ng/account/" + watcher.ACCOUNT +
        "/ci/orgs/default/projects/default_project/pipelines/" +
        watcher.PIPELINE + "/executions/" + EXEC + "/pipeline?stage=abc"
    )
    return {"context": watcher.GH_CONTEXT, "state": status,
        "creator": {"id": creator}, "target_url": path,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}


class HarnessWatcherTests(unittest.TestCase):
    def test_gh_status_scope_and_creator(self):
        self.assertEqual(watcher.owned_execution_id(gh_status()), EXEC)
        self.assertIsNone(watcher.owned_execution_id(gh_status(creator=5)))
        self.assertIsNone(watcher.owned_execution_id(
            gh_status(path="https://example.com"+"/executions/"+EXEC+"/pipeline")))
        self.assertIsNone(watcher.owned_execution_id(
            gh_status(path="https://app.harness.io/ng/account/OTHER/ci/orgs/default/"
                     "projects/default_project/pipelines/" + watcher.PIPELINE +
                     "/executions/" + EXEC + "/pipeline")))
        old = gh_status()
        old["created_at"] = "2025-01-01T00:00:00Z"
        self.assertIsNone(watcher.owned_execution_id(old))
        self.assertIsNone(watcher.owned_execution_id(
            dict(gh_status(), context="unrelated-pipeline")))

    def test_recent_discovery_deduplicates_exact_execution(self):
        def fake(url, token):
            if "/commits?sha=main" in url:
                return [{"sha": SHA}, {"sha": "b"*40}]
            return [gh_status(), gh_status()]
        self.assertEqual(watcher.recent_owned_runs("fixture", fake),
                         [(EXEC, SHA)])

    def test_structured_error_proof_only(self):
        self.assertEqual(watcher.structured_quota(detail(), EXEC),
                         "quota_exceeded")
        self.assertIsNone(watcher.structured_quota(
            detail(code="permission_denied"), EXEC))
        self.assertIsNone(watcher.structured_quota(
            {"data": {"planExecution": {"uuid": EXEC, "status": "Running"}}}, EXEC))
        self.assertIsNone(watcher.structured_quota(detail(), "different"))
        self.assertIsNone(watcher.structured_quota(
            {"data": {"pipelineExecutionSummary": {
                **detail()["data"]["pipelineExecutionSummary"],
                "projectIdentifier": "FOREIGN"
            }}}, EXEC))
        self.assertIsNone(watcher.structured_quota(
            {"data": {"pipelineExecutionSummary": {
                **detail()["data"]["pipelineExecutionSummary"],
                "failureInfo": {"message": "quota_exceeded"}
            }}}, EXEC))

    def test_real_order_claim_then_abort_then_terminal_then_report(self):
        actions = []
        status = {"v": "Running"}
        def request(method, url, headers):
            actions.append(method)
            if method == "PUT":
                status["v"] = "Aborted"
                return 200, {"status": "SUCCESS"}
            return 200, detail(status["v"])
        def controller(oidc, payload):
            actions.append(payload["phase"].upper())
            if payload["phase"] == "claim":
                self.assertEqual(payload["target"], EXEC)
                self.assertEqual(payload["sha"], SHA)
                return {"code": "CLAIMED", "owner_token": "11111111-1111-4111-8111-111111111111"}
            return {"code": "RECORDED"}
        api = HarnessPipelineRun(watcher.ACCOUNT, watcher.ORG,
            watcher.PROJECT, watcher.PIPELINE, EXEC, "fixture", request)
        result = watcher.check_and_cancel(
            EXEC, SHA, api, "synthetic-oidc", controller=controller, sleep=lambda _: None)
        self.assertEqual("CANCELLED_NO_INDEPENDENT_RESERVE", result)
        self.assertEqual(["GET","GET","CLAIM","GET","PUT","GET","REPORT"], actions)

    def test_unclaimed_cancel_is_forbidden(self):
        actions = []
        def request(method, *_):
            actions.append(method)
            if method == "PUT":
                raise AssertionError("ABORT_WITHOUT_FENCE")
            return 200, detail()
        api = HarnessPipelineRun(watcher.ACCOUNT, watcher.ORG,
            watcher.PROJECT, watcher.PIPELINE, EXEC, "fixture", request)
        value = watcher.check_and_cancel(
            EXEC, SHA, api, "oidc", controller=lambda *_: {"code": "ALREADY_CLAIMED"})
        self.assertEqual("NOT_EXCLUSIVELY_OWNED", value)
        self.assertEqual(["GET","GET"], actions)

    def test_no_quota_means_no_fence_and_no_abort(self):
        actions = []
        def request(method, *_):
            actions.append(method)
            if method == "PUT":
                raise AssertionError("FORBIDDEN")
            return 200, detail(code="forbidden")
        api = HarnessPipelineRun(watcher.ACCOUNT, watcher.ORG,
            watcher.PROJECT, watcher.PIPELINE, EXEC, "fixture", request)
        value = watcher.check_and_cancel(
            EXEC, SHA, api, "oidc",
            controller=lambda *_: (_ for _ in ()).throw(AssertionError("FENCE_INVALID")))
        self.assertEqual("NO_STRUCTURED_QUOTA", value)
        self.assertEqual(["GET"], actions)

    def test_quota_watch_disabled_does_not_touch_credentials(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": watcher.REPO,
                                     "HARNESS_QUOTA_WATCH_ENABLED": "false"}, clear=True):
            self.assertEqual(0, watcher.main())

    def test_enabled_without_secret_fails_closed(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": watcher.REPO,
                                     "HARNESS_QUOTA_WATCH_ENABLED": "true"}, clear=True):
            self.assertEqual(2, watcher.main())


if __name__ == "__main__":
    unittest.main()
