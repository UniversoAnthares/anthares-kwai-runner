"""Provider cancellation/status adapters. No network at import time.

Use ONLY after a confirmed quota signal for an exact owned run/pipeline.
Never print API authorization credentials or invoke fallback by itself.
"""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ProviderUncertain(Exception):
    pass


def http_json(method: str, url: str, headers: dict) -> tuple[int, dict]:
    req = Request(url, method=method, headers=headers)
    try:
        with urlopen(req, timeout=12) as resp:
            data = resp.read(262144)
            return resp.status, json.loads(data) if data else {}
    except HTTPError as err:
        return err.code, {}
    except (URLError, OSError, ValueError):
        raise ProviderUncertain("PROVIDER_API_UNCERTAIN") from None


class GitHubActionsRun:
    def __init__(self, owner, repo, run_id, token, request=http_json):
        if not (owner and repo and str(run_id).isdigit() and token):
            raise ValueError("INVALID_RUN_IDENTITY")
        self.url = ("https://api.github.com/repos/" + quote(owner,safe="") + "/" +
                    quote(repo,safe="") + "/actions/runs/" + str(run_id))
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer " + token,
        }
        self.request = request

    def cancel(self, _attempt_id):
        code, _ = self.request("POST", self.url + "/cancel", self.headers)
        # 409 means perhaps already completed; verify exact run before acknowledging.
        return code in (202, 204) or (code == 409 and self.status(_attempt_id) in ("CANCELLED","FAILED"))

    def status(self, _attempt_id):
        code, data = self.request("GET", self.url, self.headers)
        if code != 200:
            return "UNKNOWN"
        if data.get("status") != "completed":
            return "RUNNING"
        conclusion = data.get("conclusion")
        if conclusion in ("cancelled","skipped"): return "CANCELLED"
        if conclusion in ("failure","timed_out","action_required"): return "FAILED"
        if conclusion == "success": return "SUCCEEDED"
        return "UNKNOWN"


class GitLabPipeline:
    def __init__(self, project_id, pipeline_id, token, request=http_json):
        if not (str(project_id).strip() and str(pipeline_id).isdigit() and token):
            raise ValueError("INVALID_PIPELINE_IDENTITY")
        self.url = ("https://gitlab.com/api/v4/projects/" +
                    quote(str(project_id),safe="") + "/pipelines/" + str(pipeline_id))
        self.headers = {"PRIVATE-TOKEN": token, "Accept": "application/json"}
        self.request = request

    def cancel(self, _attempt_id):
        code, _ = self.request("POST", self.url + "/cancel", self.headers)
        return code == 200

    def status(self, _attempt_id):
        code, data = self.request("GET", self.url, self.headers)
        if code != 200:
            return "UNKNOWN"
        state = data.get("status")
        if state == "canceled": return "CANCELLED"
        if state == "failed": return "FAILED"
        if state == "success": return "SUCCEEDED"
        return "RUNNING" if state in ("running","pending","created","preparing","waiting_for_resource","scheduled") else "UNKNOWN"


class HarnessPipelineRun:
    """Abort/status for one exact owned Harness NG pipeline execution.

    The caller MUST acquire the shared Neon fence and verify the execution's
    account, project, pipeline, git ref and side effects before invoking.
    Import/initialization performs no network requests or dispatch.
    """
    _TERMINAL = {
        "ABORTED": "CANCELLED", "CANCELLED": "CANCELLED",
        "FAILED": "FAILED", "ERROR": "FAILED", "ERRORED": "FAILED",
        "EXPIRED": "EXPIRED", "SUCCESS": "SUCCEEDED",
        "SUCCEEDED": "SUCCEEDED",
    }
    _ACTIVE = {"RUNNING", "QUEUED", "NOTSTARTED", "NOT_STARTED",
               "TASKWAITING", "ASYNCWAITING", "TIMEDWAITING",
               "PAUSED", "SUSPENDED"}

    def __init__(self, account, org, project, pipeline, execution_id,
                 token, request=http_json):
        import re
        ids = (account, org, project, pipeline, execution_id)
        if not token or not all(isinstance(x, str) and
                                re.fullmatch(r"[A-Za-z0-9_-]{1,160}", x)
                                for x in ids):
            raise ValueError("INVALID_HARNESS_EXECUTION_IDENTITY")
        self.execution_id = execution_id
        self.pipeline = pipeline
        self.account = account
        self.org = org
        self.project = project
        self.headers = {"x-api-key": token, "Accept": "application/json"}
        self.request = request
        query = ("?accountIdentifier=" + quote(account, safe="") +
                 "&orgIdentifier=" + quote(org, safe="") +
                 "&projectIdentifier=" + quote(project, safe=""))
        base = ("https://app.harness.io/pipeline/api/")
        self.status_url = (base + "pipelines/execution/v2/" +
                           quote(execution_id, safe="") + query)
        self.cancel_url = (base + "pipeline/execute/interrupt/" +
                           quote(execution_id, safe="") + query +
                           "&interruptType=AbortAll")

    def _require_owned(self, attempt_id):
        if attempt_id != self.execution_id:
            raise ValueError("HARNESS_ATTEMPT_NOT_OWNED")

    def cancel(self, attempt_id):
        self._require_owned(attempt_id)
        code, body = self.request("PUT", self.cancel_url, self.headers)
        # HTTP success is only an acknowledgement. Core must poll terminal.
        # Reject explicit application-level errors even when HTTP is 200.
        return code in (200, 202, 204) and (
            not isinstance(body, dict) or
            body.get("status", "SUCCESS").upper() == "SUCCESS"
        )

    def status(self, attempt_id):
        self._require_owned(attempt_id)
        code, data = self.request("GET", self.status_url, self.headers)
        if code != 200 or not isinstance(data, dict):
            return "UNKNOWN"
        response = data.get("data")
        if not isinstance(response, dict):
            return "UNKNOWN"
        # Harness execution v2 returns planExecution.status; other envelopes
        # are intentionally not guessed. An unexpected schema fails closed.
        plan = response.get("planExecution")
        if not isinstance(plan, dict):
            return "UNKNOWN"
        if plan.get("uuid") != self.execution_id:
            return "UNKNOWN"
        if plan.get("pipelineIdentifier") != self.pipeline:
            return "UNKNOWN"
        value = plan.get("status")
        if not isinstance(value, str):
            return "UNKNOWN"
        normalized = value.replace("_", "").upper()
        if normalized in self._TERMINAL:
            return self._TERMINAL[normalized]
        if normalized in self._ACTIVE:
            return "RUNNING"
        return "UNKNOWN"


def cancel_harness_quota_fenced(*, ledger, api: HarnessPipelineRun, task_id: str,
                                attempt_id: str, quota_code: str, http_status=None,
                                error_message="", owned_execution_proven=False,
                                reconcile=None):
    """Fail-closed shared-ledger cancel-first Harness handoff.

    Requires a SHARED transactional fenced ledger such as SharedQuotaLedger,
    not the single-host SQLite ledger. No successor dispatch is supported yet.
    Callers must independently establish that exact owned remote execution
    belongs to the expected account/project/pipeline and is quota-blocked.
    """
    from tools.ci_quota_cancel_first import Route, cancel_first, is_quota
    from tools.ci_quota_neon_ledger import SharedQuotaLedger
    if not isinstance(ledger, SharedQuotaLedger):
        raise ValueError("SHARED_NEON_LEDGER_REQUIRED")
    if not isinstance(api, HarnessPipelineRun):
        raise ValueError("HARNESS_PROVIDER_ADAPTER_REQUIRED")
    if not task_id or attempt_id != api.execution_id or not owned_execution_proven:
        raise ValueError("HARNESS_OWNERSHIP_PROOF_REQUIRED")
    if not is_quota(http_status=http_status, code=quota_code, message=error_message):
        return {"state": "NOT_QUOTA"}
    # Verify identity and pipeline scope by a read-only provider query BEFORE
    # obtaining a fence or sending a destructive interrupt. A caller-controlled
    # ownership boolean is not sufficient authentication on its own.
    try:
        preflight = api.status(attempt_id)
    except Exception:
        preflight = "UNKNOWN"
    if preflight != "RUNNING":
        return {"state": "HARNESS_PREFLIGHT_NOT_RUNNING_OR_UNVERIFIED"}
    def poll_terminal(_):
        import time
        last = "UNKNOWN"
        for index in range(4):
            try:
                last = api.status(attempt_id)
            except Exception:
                return "UNKNOWN"
            if last != "RUNNING":
                return last
            if index < 3:
                time.sleep(1)
        return last
    # Never enqueue a replacement here: cross-provider independent quota,
    # side-effect reconciliation and global fencing need additional proof.
    return cancel_first(
        ledger=ledger, task_id=task_id, attempt_id="harness:" + attempt_id,
        current=Route("harness", "harness_account:" + api.account,
                      eligible=False, independent_quota_verified=False,
                      cancellation_capable=True),
        candidates=[], http_status=http_status, provider_code=quota_code,
        error_message=error_message,
        cancel=lambda _id: api.cancel(attempt_id),
        status=poll_terminal,
        enqueue=lambda *_: (_ for _ in ()).throw(
            AssertionError("HARNESS_FALLBACK_DISPATCH_FORBIDDEN")),
        side_effects_possible=True, reconcile=reconcile)
