"""Anthares cancel-first quota failover core.

Execution is opt-in through an authenticated controller: importing never dispatches.
SQLite ledger is SINGLE-HOST ONLY; multi-cloud requires a shared fenced store.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Callable, Iterable

QUOTA_CODES = {
    "ci_quota_exceeded", "quota_exceeded", "quota_exhausted",
    "insufficient_quota", "resource_exhausted", "rate_limit_exceeded",
    "billing_hard_limit_reached", "credits_exhausted", "usage_limit_reached",
    "monthly_quota_exceeded", "daily_quota_exceeded",
}
QUOTA_MESSAGE = re.compile(
    r"(?:quota|credit|usage|rate) (?:limit )?(?:exceeded|exhausted|reached)"
    r"|insufficient (?:credits|quota)|out of (?:credits|quota)", re.I
)
TERMINAL = {"CANCELED", "CANCELLED", "ABORTED", "FAILED", "TERMINATED", "EXPIRED"}
UNCERTAIN = {"STARTED", "COMMITTING", "SUBMITTING_UNCERTAIN", "UNKNOWN"}


@dataclass(frozen=True)
class Route:
    name: str
    quota_scope: str
    eligible: bool = False
    independent_quota_verified: bool = False
    cancellation_capable: bool = False


def is_quota(*, http_status: int | None, code: str = "", message: str = "") -> bool:
    norm = (code or "").strip().lower().replace("-", "_")
    if http_status in (401, 405, 451):
        return False
    if norm in QUOTA_CODES:
        return True
    if http_status in (429, 509):
        return True
    if http_status in (402, 403, 400, 500, 503) and QUOTA_MESSAGE.search(message or ""):
        return True
    return False


def successor_id(task: str, attempt: str, provider: str) -> str:
    return "quota-" + hashlib.sha256((task + "\0" + attempt + "\0" + provider).encode()).hexdigest()[:24]


class LocalLedger:
    """Durable atomic claim on one machine; never mount as multi-host ledger."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=5.0)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, state TEXT NOT NULL, data TEXT NOT NULL)")

    def claim(self, attempt: str, value: dict) -> tuple[bool, dict]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT data FROM attempts WHERE id=?", (attempt,)).fetchone()
            if row:
                self.db.commit()
                return False, json.loads(row[0])
            self.db.execute("INSERT INTO attempts VALUES (?,?,?)",
                            (attempt, value["state"], json.dumps(value)))
            self.db.commit()
            return True, dict(value)
        except BaseException:
            self.db.rollback()
            raise

    def update(self, attempt: str, value: dict):
        with self.db:
            self.db.execute("UPDATE attempts SET state=?,data=? WHERE id=?",
                            (value["state"], json.dumps(value), attempt))

    def close(self):
        self.db.close()


def cancel_first(*, ledger: LocalLedger, task_id: str, attempt_id: str,
                 current: Route, candidates: Iterable[Route],
                 http_status: int | None, provider_code: str, error_message: str,
                 cancel: Callable[[str], bool], status: Callable[[str], str],
                 enqueue: Callable[[Route, str, str], str],
                 side_effects_possible: bool = True,
                 reconcile: Callable[[str], str] | None = None) -> dict:
    """Cancel owned attempt immediately, verify terminal state, then fail over.

    Callback endpoints must be scoped to the EXACT owned remote run/pipeline ID.
    Never resume an uncertain enqueue, unconfirmed cancellation, or side effect.
    """
    if not is_quota(http_status=http_status, code=provider_code, message=error_message):
        return {"state": "NOT_QUOTA"}
    row = {"task": task_id, "attempt": attempt_id,
           "provider": current.name, "quota_scope": current.quota_scope,
           "reason": "CONFIRMED_QUOTA", "state": "CANCEL_REQUESTED",
           "ts": time.time(), "successor": None}
    won, row = ledger.claim(attempt_id, row)
    if not won:
        return row   # already owned by another observer; NO duplicate cancellation
    try:
        sent = cancel(attempt_id) is True
    except Exception:
        sent = False
    row["cancel_sent"] = sent
    if not sent:
        row["state"] = "CANCEL_UNCONFIRMED"
        ledger.update(attempt_id, row)
        return row
    try:
        remote = str(status(attempt_id)).upper()
    except Exception:
        remote = "UNKNOWN"
    row["provider_state"] = remote
    if remote not in TERMINAL:
        row["state"] = "CANCEL_UNCONFIRMED"
        ledger.update(attempt_id, row)
        return row
    row["state"] = "CANCELLED_QUOTA"
    ledger.update(attempt_id, row)
    if remote == "SUCCEEDED":
        row["state"] = "RECONCILE_REQUIRED"
        ledger.update(attempt_id, row)
        return row
    if side_effects_possible:
        try:
            proof = reconcile(task_id) if reconcile else "UNKNOWN"
        except Exception:
            proof = "UNKNOWN"
        if proof != "NOT_APPLIED":
            row["state"] = "RECONCILE_REQUIRED"
            ledger.update(attempt_id, row)
            return row
    eligible = next((r for r in candidates
                     if r.name != current.name and r.quota_scope != current.quota_scope
                     and r.eligible and r.independent_quota_verified
                     and r.cancellation_capable), None)
    if eligible is None:
        row["state"] = "CANCELLED_NO_INDEPENDENT_RESERVE"
        ledger.update(attempt_id, row)
        return row
    key = successor_id(task_id, attempt_id, eligible.name)
    row["successor"] = {"route": eligible.name, "idempotency_key": key}
    row["state"] = "FALLBACK_RESERVED"
    ledger.update(attempt_id, row)
    try:
        external_id = enqueue(eligible, task_id, key)
    except Exception:
        row["state"] = "FALLBACK_SUBMISSION_UNCERTAIN"
        ledger.update(attempt_id, row)
        return row
    if not external_id:
        row["state"] = "FALLBACK_SUBMISSION_UNCERTAIN"
        ledger.update(attempt_id, row)
        return row
    row["successor"]["external_id"] = str(external_id)
    row["state"] = "FALLBACK_QUEUED"
    ledger.update(attempt_id, row)
    return row


# Harness CI adapter. This code does not poll, enqueue or cancel upon import.
# API endpoints: https://apidocs.harness.io/pipeline-execute and
# https://apidocs.harness.io/pipeline-execution-details
import urllib.parse
import urllib.request


_HARNESS_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


@dataclass(frozen=True)
class HarnessExecution:
    account: str
    org: str
    project: str
    pipeline: str
    plan_execution_id: str

    def __post_init__(self):
        for field in (self.account, self.org, self.project,
                      self.pipeline, self.plan_execution_id):
            if not isinstance(field, str) or not _HARNESS_ID.fullmatch(field):
                raise ValueError("INVALID_HARNESS_EXECUTION_IDENTITY")


class HarnessCancelAdapter:
    """API client for ONE owned Harness execution, requiring exact identity.

    The caller supplies a secret API key and an injected transport when testing.
    A status response without unambiguous matching identity fails CLOSED.
    No authenticated request is made unless invoked explicitly.
    """

    def __init__(self, execution: HarnessExecution, api_key: str, *,
                 transport=None, origin: str = "https://app.harness.io"):
        if not api_key or not isinstance(api_key, str):
            raise ValueError("HARNESS_API_KEY_REQUIRED")
        if origin != "https://app.harness.io":
            raise ValueError("UNAPPROVED_HARNESS_API_ORIGIN")
        self.execution = execution
        self.api_key = api_key
        self.transport = transport or urllib.request.urlopen
        self.origin = origin

    def _url(self, endpoint: str) -> str:
        e = self.execution
        params = urllib.parse.urlencode({
            "accountIdentifier": e.account,
            "orgIdentifier": e.org,
            "projectIdentifier": e.project,
        })
        return self.origin + endpoint + "?" + params

    def _request(self, method: str, path: str) -> dict:
        req = urllib.request.Request(
            self._url(path),
            method=method,
            headers={"x-api-key": self.api_key, "Accept": "application/json"},
        )
        with self.transport(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("HARNESS_RESPONSE_INVALID")
        return result

    def _execution_summary(self, result: dict) -> dict:
        """Reject missing/ambiguous metadata rather than inferring an owned run."""
        data = result.get("data")
        if not isinstance(data, dict):
            raise ValueError("HARNESS_STATUS_DATA_MISSING")
        candidates = [data, data.get("pipelineExecutionSummary"),
                      data.get("executionDetails")]
        e = self.execution
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if (item.get("planExecutionId") == e.plan_execution_id
                    and item.get("pipelineIdentifier") == e.pipeline
                    and item.get("accountIdentifier") == e.account
                    and item.get("orgIdentifier") == e.org
                    and item.get("projectIdentifier") == e.project
                    and isinstance(item.get("status"), str)):
                return item
        raise ValueError("HARNESS_REMOTE_IDENTITY_UNCONFIRMED")

    def get_owned_status(self) -> str:
        e = self.execution
        path = "/pipeline/api/pipelines/execution/v2/" + e.plan_execution_id
        return self._execution_summary(self._request("GET", path))["status"].upper()

    def request_cancel(self) -> bool:
        """Verify identity BEFORE interrupt. Never infer success from HTTP alone."""
        before = self.get_owned_status()
        if before in TERMINAL or before in ("SUCCESS", "SUCCEEDED"):
            return False
        if before not in {
            "RUNNING", "QUEUED", "TASKWAITING", "RESOURCEWAITING",
            "ASYNCWAITING", "WAITSTEPRUNNING", "INPUTWAITING",
            "QUEUEDLICENSELIMITREACHED", "QUEUEDEXECUTIONCONCURRENCYREACHED",
        }:
            return False
        e = self.execution
        path = "/pipeline/api/pipeline/execute/interrupt/" + e.plan_execution_id
        self._request("PUT", path)
        return True


def cancel_harness_quota(*, ledger, execution: HarnessExecution,
                         api_key: str, task_id: str, attempt_id: str,
                         http_status: int | None, provider_code: str,
                         error_message: str, candidates: Iterable[Route] = (),
                         enqueue=None, side_effects_possible: bool = True,
                         reconcile=None, transport=None) -> dict:
    """Invoke the existing cancel-first contract, using a SHARED fenced ledger.

    A LOCAL SQLite ledger must never be passed in production; callers supply the
    opt-in SharedQuotaLedger/Neon service and reconcile an uncertain submission.
    No dispatch is attempted without explicitly supplied enqueue callback.
    """
    if not is_quota(http_status=http_status, code=provider_code,
                    message=error_message):
        return {"state": "NOT_QUOTA"}
    if not hasattr(ledger, "_owned") or not hasattr(ledger, "claim"):
        return {"state": "BLOCKED_SHARED_FENCING_UNAVAILABLE"}
    if not enqueue:
        enqueue = lambda _r, _t, _k: ""
    adapter = HarnessCancelAdapter(execution, api_key, transport=transport)
    current = Route("harness", "harness_cloud_account_" + execution.account,
                    eligible=True, independent_quota_verified=False,
                    cancellation_capable=True)
    return cancel_first(
        ledger=ledger, task_id=task_id, attempt_id=attempt_id,
        current=current, candidates=candidates,
        http_status=http_status, provider_code=provider_code,
        error_message=error_message,
        cancel=lambda attempt: adapter.request_cancel()
        if attempt == attempt_id else False,
        status=lambda attempt: adapter.get_owned_status()
        if attempt == attempt_id else "UNKNOWN",
        enqueue=enqueue, side_effects_possible=side_effects_possible,
        reconcile=reconcile,
    )
