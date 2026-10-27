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

    def test_readonly_ci_source_blob_fail_closed(self):
        records = []
        def reader(url, token):
            records.append((url, token))
            return {"type": "file", "sha": watcher.PINNED_PIPELINE_BLOB}
        self.assertTrue(watcher.read_only_pipeline_verified(SHA, "token", reader))
        self.assertEqual(len(records), 1)
        self.assertIn("?ref=" + SHA, records[0][0])
        self.assertFalse(watcher.read_only_pipeline_verified(SHA, "", reader))
        self.assertFalse(watcher.read_only_pipeline_verified("invalid", "token", reader))
        self.assertFalse(watcher.read_only_pipeline_verified(
            SHA, "token", lambda *_: {"sha": "deadbeef", "type": "file"}))
        self.assertFalse(watcher.read_only_pipeline_verified(
            SHA, "token", lambda *_: {"sha": watcher.PINNED_PIPELINE_BLOB,
                                     "type": "dir"}))
        self.assertEqual(len(records), 1)

    def test_fenced_fallback_dispatch_only_after_readonly_reservation(self):
        actions = []
        event = {"provider": "harness", "target": EXEC, "sha": SHA,
                 "code": "quota_exceeded"}
        def reader(*_):
            actions.append("SOURCE_BLOB")
            return {"type": "file", "sha": watcher.PINNED_PIPELINE_BLOB}
        def controller(oidc, payload):
            actions.append(payload["phase"].upper())
            self.assertEqual(payload["owner_token"], "owned")
            self.assertEqual(payload["pipeline_blob"], watcher.PINNED_PIPELINE_BLOB)
            self.assertEqual(payload["target"], EXEC)
            return {"code": {"reserve": "FALLBACK_RESERVED",
                             "ack": "FALLBACK_SUBMITTED"}[payload["phase"]]}
        def dispatch(sha, execution, token):
            actions.append("DISPATCH")
            self.assertEqual((sha, execution, token), (SHA, EXEC, "github"))
            return True
        result = watcher.fenced_harness_fallback(
            "oidc", event, "owned", "github", controller=controller,
            reader=reader, dispatch=dispatch)
        self.assertEqual(result, "FALLBACK_SUBMITTED")
        self.assertEqual(actions, ["SOURCE_BLOB", "RESERVE", "DISPATCH", "ACK"])

    def test_uncertain_submission_no_retry_or_ack(self):
        actions = []
        event = {"provider": "harness", "target": EXEC, "sha": SHA,
                 "code": "quota_exceeded"}
        def controller(_jwt, payload):
            actions.append(payload["phase"])
            return {"code": "FALLBACK_RESERVED"}
        def dispatch(*_):
            actions.append("dispatch")
            raise OSError("submission outcome uncertain")
        result = watcher.fenced_harness_fallback(
            "oidc", event, "owned", "github", controller=controller,
            reader=lambda *_: {"type": "file",
                               "sha": watcher.PINNED_PIPELINE_BLOB},
            dispatch=dispatch)
        self.assertEqual(result, "FALLBACK_SUBMISSION_UNCERTAIN")
        self.assertEqual(actions, ["reserve", "dispatch"])

    def test_foreign_stage_or_failed_reservation_never_dispatches(self):
        event = {"provider": "harness", "target": EXEC, "sha": SHA,
                 "code": "quota_exceeded"}
        def forbidden(*_):
            raise AssertionError("DISPATCH_FORBIDDEN")
        value = watcher.fenced_harness_fallback(
            "oidc", event, "owned", "github", reader=lambda *_: {
                "type": "file", "sha": "not-reviewed"}, dispatch=forbidden)
        self.assertEqual(value, "CANCELLED_NO_INDEPENDENT_RESERVE")
        value = watcher.fenced_harness_fallback(
            "oidc", event, "owned", "github",
            reader=lambda *_: {"type": "file",
                               "sha": watcher.PINNED_PIPELINE_BLOB},
            controller=lambda *_: {"code": "ALREADY_CLAIMED"},
            dispatch=forbidden)
        self.assertEqual(value, "FALLBACK_RESERVE_REJECTED")

    def test_terminal_callback_runs_after_fenced_report_only(self):
        actions = []
        status = {"v": "Running"}
        def request(method, *_):
            actions.append(method)
            if method == "PUT":
                status["v"] = "Aborted"
                return 200, {"status": "SUCCESS"}
            return 200, detail(status["v"])
        def controller(_, payload):
            actions.append(payload["phase"])
            if payload["phase"] == "claim":
                return {"code": "CLAIMED", "owner_token": "owned"}
            return {"code": "RECORDED"}
        def terminal(jwt, event, owner):
            actions.append("fallback")
            self.assertEqual(event["sha"], SHA)
            self.assertEqual(owner, "owned")
            return "FALLBACK_SUBMITTED"
        api = HarnessPipelineRun(watcher.ACCOUNT, watcher.ORG,
            watcher.PROJECT, watcher.PIPELINE, EXEC, "fixture", request)
        self.assertEqual(watcher.check_and_cancel(
            EXEC, SHA, api, "oidc", controller=controller, sleep=lambda _: None,
            on_terminal=terminal), "FALLBACK_SUBMITTED")
        self.assertEqual(actions, ["GET", "GET", "claim", "GET",
                                   "PUT", "GET", "report", "fallback"])

    def test_readonly_auth_probe_requires_exact_completed_owned_execution(self):
        self.assertEqual("NOT_CONFIGURED", watcher.readonly_auth_probe(""))
        statuses=[]
        def fake(method, url, headers):
            statuses.append(method)
            self.assertNotIn("fixture", url)
            self.assertEqual(headers["x-api-key"], "fixture")
            return 200, {"data": {"pipelineExecutionSummary": {
                "planExecutionId": "udezZluzS2KC0qbfKcwCng",
                "pipelineIdentifier": watcher.PIPELINE,
                "orgIdentifier": watcher.ORG,
                "projectIdentifier": watcher.PROJECT,
                "status": "Success"
            }}}
        self.assertEqual("VERIFIED_OWNED_EXECUTION_908",
            watcher.readonly_auth_probe("fixture", fake))
        self.assertEqual(["GET"], statuses)

    def test_readonly_auth_probe_rejects_wrong_run_or_permissions(self):
        def foreign(*_):
            return 200, {"data": {"pipelineExecutionSummary": {
                "planExecutionId": "foreigntokenrun",
                "pipelineIdentifier": watcher.PIPELINE,
                "orgIdentifier": watcher.ORG,
                "projectIdentifier": watcher.PROJECT,
                "status": "Success"
            }}}
        self.assertEqual("UNVERIFIED_RESPONSE_OR_CREDENTIAL",
                         watcher.readonly_auth_probe("fixture", foreign))
        self.assertEqual("UNVERIFIED_RESPONSE_OR_CREDENTIAL",
                         watcher.readonly_auth_probe("fixture",lambda *_: (401,{})))

    def test_main_probe_does_not_trigger_watch(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": watcher.REPO,
                                     "HARNESS_QUOTA_WATCH_ENABLED": "true",
                                     "HARNESS_AUTH_PROBE_ONLY": "true"}, clear=True):
            self.assertEqual(0, watcher.main())

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
