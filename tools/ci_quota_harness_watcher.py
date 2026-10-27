#!/usr/bin/env python3
"""Strict opt-in Harness CI quota abort watcher via the production Neon controller.

No client secret is bundled. Credential MUST come from a protected runner
environment. The GitHub OIDC controller must already support provider=harness.
Disabled by default and does not enqueue successor work under any condition.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from tools.ci_quota_provider_adapters import HarnessPipelineRun
from tools.ci_quota_external_watcher import get_oidc, ledger

REPO = "UniversoAnthares/anthares-kwai-runner"
ACCOUNT = "xAEBvmMUTjql7g2Exxmp-g"
ORG = "default"
PROJECT = "default_project"
PIPELINE = "pipeline_UniversoAnthares_anthares_kwai_runner_build_9a3d"
GH_CONTEXT = "pipeline_UniversoAnthares_a...-Build_and_Test"
QUOTA_CODES = frozenset({
    "ci_quota_exceeded", "quota_exceeded", "quota_exhausted",
    "insufficient_quota", "resource_exhausted", "billing_hard_limit_reached",
    "credits_exhausted", "usage_limit_reached", "monthly_quota_exceeded",
    "daily_quota_exceeded",
})
EXACT_URL = re.compile(
    r"^/ng/account/" + re.escape(ACCOUNT) +
    r"/(?:ci/)?orgs/" + re.escape(ORG) +
    r"/projects/" + re.escape(PROJECT) +
    r"/pipelines/" + re.escape(PIPELINE) +
    r"/executions/([A-Za-z0-9_-]{16,64})/pipeline$")
SHA = re.compile(r"^[a-f0-9]{40}$")


def get_json(url: str, token: str) -> object:
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "Anthares-Harness-QuotaWatch/1",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=12) as resp:
        return json.load(resp)


def recent_status(value: dict, *, now=None) -> bool:
    if not isinstance(value, dict) or value.get("context") != GH_CONTEXT:
        return False
    # Only the repo owner-authored Harness integration status is accepted.
    creator = value.get("creator")
    if not isinstance(creator, dict) or creator.get("id") != 81930373:
        return False
    raw = value.get("created_at")
    try:
        moment = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        now = now or dt.datetime.now(dt.timezone.utc)
        age = (now - moment).total_seconds()
        return moment.tzinfo is not None and 0 <= age <= 5400
    except (TypeError, ValueError, AttributeError):
        return False


def owned_execution_id(status: dict):
    if not recent_status(status):
        return None
    uri = urlparse(str(status.get("target_url", "")))
    if uri.scheme != "https" or uri.netloc != "app.harness.io" or uri.username:
        return None
    match = EXACT_URL.fullmatch(uri.path)
    return match.group(1) if match else None


def recent_owned_runs(github_token, reader=get_json) -> list[tuple[str, str]]:
    base = "https://api.github.com/repos/" + REPO
    commits = reader(base + "/commits?sha=main&per_page=6", github_token)
    if not isinstance(commits, list):
        raise ValueError("INVALID_GITHUB_COMMITS_RESPONSE")
    seen = set()
    candidates = []
    for commit in commits[:6]:
        sha = str(commit.get("sha", "")) if isinstance(commit, dict) else ""
        if not SHA.fullmatch(sha):
            continue
        statuses = reader(base + "/commits/" + sha + "/statuses?per_page=50", github_token)
        if not isinstance(statuses, list):
            raise ValueError("INVALID_GITHUB_STATUSES_RESPONSE")
        for value in statuses[:50]:
            execution_id = owned_execution_id(value)
            if execution_id and execution_id not in seen:
                seen.add(execution_id)
                candidates.append((execution_id, sha))
    return candidates[:12]


def structured_quota(detail, execution_id):
    if not isinstance(detail, dict) or detail.get("status") not in (None, "SUCCESS"):
        return None
    data = detail.get("data")
    summary = data.get("pipelineExecutionSummary") if isinstance(data, dict) else None
    if not isinstance(summary, dict):
        return None
    required = {"planExecutionId": execution_id,
                "pipelineIdentifier": PIPELINE,
                "orgIdentifier": ORG, "projectIdentifier": PROJECT}
    if any(summary.get(k) != v for k, v in required.items()):
        return None
    failure = summary.get("failureInfo")
    if not isinstance(failure, dict):
        return None
    messages = failure.get("responseMessages")
    if not isinstance(messages, list):
        return None
    for entry in messages:
        if isinstance(entry, dict):
            code = entry.get("code")
            if isinstance(code, str) and code.strip().lower() in QUOTA_CODES:
                return code.strip().lower()
    return None


def check_and_cancel(execution_id, sha, api, oidc, *, controller=ledger,
                     sleep=time.sleep, on_terminal=None):
    """Only an exact owned, active execution with a structured quota signal.

    The claim precedes PUT AbortAll. On any uncertain status, do not retry
    cancellation or submit a replacement. The Vercel controller reports
    terminal under the same OIDC owner/generation.
    """
    code, detail = api.request("GET", api.status_url, api.headers)
    if code != 200:
        return "HARNESS_READ_UNVERIFIED"
    quota = structured_quota(detail, execution_id)
    if not quota:
        return "NO_STRUCTURED_QUOTA"
    if api.status(execution_id) != "RUNNING":
        return "NOT_ACTIVE_OR_IDENTITY_UNKNOWN"
    base = {"provider": "harness", "target": execution_id,
            "sha": sha, "code": quota}
    try:
        claimed = controller(oidc, {"phase": "claim", **base})
    except (HTTPError, URLError, OSError, ValueError):
        return "NEON_CLAIM_UNAVAILABLE"
    if claimed.get("code") != "CLAIMED" or not claimed.get("owner_token"):
        return "NOT_EXCLUSIVELY_OWNED"
    result = "CANCEL_UNCONFIRMED"
    try:
        # Reconfirm after the claim: a concurrent observer may have completed it.
        if api.status(execution_id) == "RUNNING" and api.cancel(execution_id):
            for attempt in range(3):
                state = api.status(execution_id)
                if state in ("CANCELLED", "FAILED", "EXPIRED"):
                    result = "CANCELLED_NO_INDEPENDENT_RESERVE"
                    break
                if state != "RUNNING":
                    break
                if attempt != 2:
                    sleep(2)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        pass
    try:
        report = controller(oidc, {"phase": "report", **base,
            "owner_token": claimed["owner_token"], "outcome": result})
    except (HTTPError, URLError, OSError, ValueError):
        return "NEON_REPORT_UNCERTAIN"
    if report.get("code") != "RECORDED":
        return "NEON_REPORT_UNCERTAIN"
    if result == "CANCELLED_NO_INDEPENDENT_RESERVE" and on_terminal:
        try:
            return on_terminal(oidc, base, claimed["owner_token"])
        except (HTTPError, URLError, OSError, ValueError):
            return "FALLBACK_UNCERTAIN"
    return result


# This is an exact source-code allowlist, not a generic CI-to-publisher route.
# This Harness stage only compiles/tests and never publishes or deploys.
PINNED_PIPELINE_BLOB = "bdbbd74b693d2f9fdd6c08b94cc03d8921ebce18"
PINNED_PIPELINE_PATH = (".harness/orgs/default/projects/default_project/"
    "pipelines/pipeline_UniversoAnthares_anthares_kwai_runner_build_9a3d.yaml")
FALLBACK_WORKFLOW = "harness-quota-rescue.yml"


def read_only_pipeline_verified(sha: str, github_token: str, reader=get_json) -> bool:
    """Prove source revision carries the reviewed no-publication Harness stage."""
    if not SHA.fullmatch(sha) or not github_token:
        return False
    url = ("https://api.github.com/repos/" + REPO + "/contents/" +
           PINNED_PIPELINE_PATH + "?ref=" + quote(sha, safe=""))
    try:
        doc = reader(url, github_token)
        return (isinstance(doc, dict) and doc.get("type") == "file" and
                doc.get("sha") == PINNED_PIPELINE_BLOB)
    except (HTTPError, URLError, OSError, ValueError):
        return False


def dispatch_one_pinned_ci(sha: str, execution_id: str, github_token: str,
                           *, request=None) -> bool:
    """Single GitHub dispatch attempt; an ambiguous response is never retried."""
    if not (SHA.fullmatch(sha) and re.fullmatch(r"[A-Za-z0-9_-]{16,64}", execution_id)
            and github_token):
        return False
    from urllib.request import Request, urlopen
    url = ("https://api.github.com/repos/" + REPO + "/actions/workflows/" +
           FALLBACK_WORKFLOW + "/dispatches")
    payload = json.dumps({"ref": "main", "inputs": {
        "source_sha": sha, "harness_execution_id": execution_id}}).encode()
    headers = {"Authorization": "Bearer " + github_token,
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "Content-Type": "application/json"}
    if request:
        return request(url, payload, headers) == 204
    with urlopen(Request(url, data=payload, headers=headers, method="POST"),
                 timeout=12) as response:
        return response.status == 204


def fenced_harness_fallback(oidc, event, owner_token, github_token, *,
                            controller=ledger, reader=get_json,
                            dispatch=dispatch_one_pinned_ci):
    """Reserve BEFORE one dispatch, acknowledge AFTER HTTP 204, never retry."""
    execution_id, sha = event["target"], event["sha"]
    if not read_only_pipeline_verified(sha, github_token, reader):
        return "CANCELLED_NO_INDEPENDENT_RESERVE"
    fields = {**event, "owner_token": owner_token,
              "pipeline_blob": PINNED_PIPELINE_BLOB}
    try:
        reserved = controller(oidc, {"phase": "reserve", **fields})
    except (HTTPError, URLError, OSError, ValueError):
        return "FALLBACK_RESERVE_UNCERTAIN"
    if reserved.get("code") != "FALLBACK_RESERVED":
        return "FALLBACK_RESERVE_REJECTED"
    try:
        accepted = dispatch(sha, execution_id, github_token)
    except (HTTPError, URLError, OSError, ValueError):
        return "FALLBACK_SUBMISSION_UNCERTAIN"
    if not accepted:
        return "FALLBACK_SUBMISSION_UNCERTAIN"
    try:
        receipt = controller(oidc, {"phase": "ack", **fields,
                                    "dispatch_status": "204"})
    except (HTTPError, URLError, OSError, ValueError):
        return "FALLBACK_ACK_UNCERTAIN"
    return ("FALLBACK_SUBMITTED" if receipt.get("code") == "FALLBACK_SUBMITTED"
            else "FALLBACK_ACK_UNCERTAIN")


def readonly_auth_probe(token: str, request=None) -> str:
    """One read-only authenticated GET on a known completed owned execution.

    Does NOT access local/browser secrets, mutate Harness, or touch Neon.
    Returns a status category only; never logs a key or response body.
    """
    if not token:
        return "NOT_CONFIGURED"
    known_id = "udezZluzS2KC0qbfKcwCng"  # Harness run #908, success
    from tools.ci_quota_provider_adapters import http_json
    api = HarnessPipelineRun(ACCOUNT, ORG, PROJECT, PIPELINE,
                             known_id, token,
                             request=request or http_json)
    try:
        result = api.status(known_id)
    except (HTTPError, URLError, OSError, ValueError):
        result = "UNKNOWN"
    if result == "SUCCEEDED":
        return "VERIFIED_OWNED_EXECUTION_908"
    return "UNVERIFIED_RESPONSE_OR_CREDENTIAL"


def main():
    if os.getenv("GITHUB_REPOSITORY") != REPO:
        print("HARNESS_QUOTA=UNAUTHORIZED_REPOSITORY")
        return 2
    if os.getenv("HARNESS_AUTH_PROBE_ONLY") == "true":
        verdict = readonly_auth_probe(os.getenv("HARNESS_API_KEY", ""))
        print("HARNESS_API_AUTH_READONLY="+verdict)
        return 0 if verdict in ("NOT_CONFIGURED", "VERIFIED_OWNED_EXECUTION_908") else 2
    if os.getenv("HARNESS_QUOTA_WATCH_ENABLED") != "true":
        print("HARNESS_QUOTA=SAFE_DISABLED")
        return 0
    key = os.getenv("HARNESS_API_KEY", "")
    if not key:
        print("HARNESS_QUOTA=MISSING_PROTECTED_SECRET")
        return 2
    try:
        executions = recent_owned_runs(os.getenv("GH_TOKEN", ""))
    except (HTTPError, URLError, OSError, ValueError):
        print("HARNESS_QUOTA=GITHUB_DISCOVERY_UNAVAILABLE")
        return 2
    if not executions:
        print("HARNESS_QUOTA=NO_RECENT_OWNED_RUNS")
        return 0
    # OIDC is fetched only when the explicit provider watch was enabled.
    oidc = None
    trouble = False
    for execution_id, sha in executions:
        api = HarnessPipelineRun(ACCOUNT, ORG, PROJECT, PIPELINE,
                                 execution_id, key)
        if oidc is None:
            try:
                oidc = get_oidc()
            except (HTTPError, URLError, OSError, ValueError):
                print("HARNESS_QUOTA=OIDC_UNAVAILABLE")
                return 2
        try:
            on_terminal = None
            if os.getenv("HARNESS_QUOTA_FALLBACK_ENABLED") == "true":
                on_terminal = lambda jwt, event, owner: fenced_harness_fallback(
                    jwt, event, owner, os.getenv("GH_TOKEN", ""))
            status = check_and_cancel(
                execution_id, sha, api, oidc, on_terminal=on_terminal)
        except (HTTPError, URLError, OSError, ValueError):
            status = "SOURCE_UNAVAILABLE"
        # Never print provider payloads, token, controller owner-token or URLs.
        print("HARNESS_QUOTA_RUN="+execution_id+" RESULT="+status)
        if status not in ("NO_STRUCTURED_QUOTA",
                          "NOT_ACTIVE_OR_IDENTITY_UNKNOWN",
                          "CANCELLED_NO_INDEPENDENT_RESERVE",
                          "FALLBACK_SUBMITTED"):
            trouble = True
    return 2 if trouble else 0


if __name__ == "__main__":
    sys.exit(main())
