#!/usr/bin/env python3
"""Controlled cancel-first GitHub run smoke consumer. No publishing or fallback."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from ci_quota_cancel_first import LocalLedger, Route, cancel_first, is_quota
from ci_quota_provider_adapters import GitHubActionsRun, http_json

EXPECTED_NAME = "Anthares quota cancellation controlled smoke"


def main():
    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    event_file = os.getenv("GITHUB_EVENT_PATH", "")
    if not token or not repo or not event_file or "/" not in repo:
        print("QUOTA_CANCEL_CONSUMER=REQUIRED_AUTH_OR_EVENT_MISSING")
        return 2
    data = json.loads(Path(event_file).read_text(encoding="utf-8"))
    p = data.get("client_payload") or {}
    rid = str(p.get("run_id", ""))
    if p.get("mode") != "synthetic_smoke" or p.get("provider") != "github_actions":
        print("QUOTA_CANCEL_CONSUMER=EVENT_PROOF_UNSUPPORTED")
        return 2
    if p.get("repo") != repo or not rid.isdecimal() or not (1 <= len(rid) <= 22):
        print("QUOTA_CANCEL_CONSUMER=INVALID_RUN_IDENTITY")
        return 2
    if not is_quota(http_status=None, code=str(p.get("code", ""))):
        print("QUOTA_CANCEL_CONSUMER=NOT_QUOTA")
        return 2

    owner,name=repo.split("/",1)
    api=GitHubActionsRun(owner,name,int(rid),token)
    code, run=http_json("GET",api.url,api.headers)
    if code != 200 or run.get("name") != EXPECTED_NAME or (run.get("repository") or {}).get("full_name") != repo:
        print("QUOTA_CANCEL_CONSUMER=RUN_NOT_ALLOWLISTED")
        return 2
    if run.get("status") not in ("in_progress","queued","waiting","pending","requested"):
        print("QUOTA_CANCEL_CONSUMER=RUN_NOT_ACTIVE")
        return 2

    def poll(attempt):
        for _ in range(24):
            state=api.status(attempt)
            if state in ("CANCELLED","FAILED","SUCCEEDED"):
                return state
            time.sleep(3)
        return "UNKNOWN"

    with tempfile.TemporaryDirectory(prefix="quota-cancel-live-smoke-") as d:
        ledger=LocalLedger(Path(d)/"ledger.sqlite")
        try:
            response=cancel_first(
                ledger=ledger,task_id="gha-smoke-"+rid,attempt_id=rid,
                current=Route("github-actions-smoke","gha-test-free",True,True,True),
                candidates=[],http_status=None,provider_code=str(p["code"]),error_message="",
                cancel=api.cancel,status=poll,
                enqueue=lambda *args: (_ for _ in ()).throw(AssertionError("FORBIDDEN_FALLBACK")),
                side_effects_possible=False,
            )
        finally:
            ledger.close()
    print("QUOTA_CANCEL_CONSUMER_STATE="+response["state"])
    return 0 if response["state"]=="CANCELLED_NO_INDEPENDENT_RESERVE" else 2


if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        # Redacted: exception detail may contain remote URLs or provider metadata.
        print("QUOTA_CANCEL_CONSUMER_ERROR="+type(exc).__name__)
        sys.exit(2)
