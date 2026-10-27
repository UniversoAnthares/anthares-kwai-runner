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
                     sleep=time.sleep):
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
    return result if report.get("code") == "RECORDED" else "NEON_REPORT_UNCERTAIN"


def main():
    if os.getenv("GITHUB_REPOSITORY") != REPO:
        print("HARNESS_QUOTA=UNAUTHORIZED_REPOSITORY")
        return 2
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
            status = check_and_cancel(execution_id, sha, api, oidc)
        except (HTTPError, URLError, OSError, ValueError):
            status = "SOURCE_UNAVAILABLE"
        # Never print provider payloads, token, controller owner-token or URLs.
        print("HARNESS_QUOTA_RUN="+execution_id+" RESULT="+status)
        if status not in ("NO_STRUCTURED_QUOTA",
                          "NOT_ACTIVE_OR_IDENTITY_UNKNOWN",
                          "CANCELLED_NO_INDEPENDENT_RESERVE"):
            trouble = True
    return 2 if trouble else 0


if __name__ == "__main__":
    sys.exit(main())
