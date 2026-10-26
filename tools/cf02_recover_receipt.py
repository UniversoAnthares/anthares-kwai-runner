#!/usr/bin/env python3
"""Safely recover a REAL historical Cloudflare deployment receipt.

This does NOT deploy a Worker, publish media, modify queues, or invoke cleanup.
It attests only a pinned production run whose deploy/cleanup/health steps passed,
whose independent receipt step failed with GitHub HTTP409.
"""
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "UniversoAnthares/anthares-kwai-runner"
SOURCE_RUN_ID = 40283336472
SOURCE_HEAD_SHA = "26ae1bdb3ba1095ab8b0230893134053804b4709"
WORKFLOW_PATH = ".github/workflows/cloudflare-central-deploy.yml"
RECEIPT_PATH = ".github/cloudflare-cortes-status.json"
HEALTH_URL = "https://anthares-control.anthares1.workers.dev/health"
REQUIRED_STEPS = (
    "Deploy exact controller to Cloudflare",
    "Remove old Kwai queue entries without touching CORTES or uncertain publications",
    "Verify public health and physical Android routing",
    "Verify protected TikTok session endpoint remains closed to unauthenticated callers",
)
FAIL_RECEIPT_STEP = "Save deployment receipt for CORTES queue recovery"


def require(condition, message):
    if not condition:
        raise RuntimeError("CF02_FAIL_CLOSED: " + message)


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward the short-lived GitHub bearer token to a log-blob host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            old_origin = urllib.parse.urlsplit(req.full_url).netloc.lower()
            new_origin = urllib.parse.urlsplit(newurl).netloc.lower()
            if new_origin != old_origin:
                for name in ("Authorization", "X-GitHub-Api-Version"):
                    redirected.remove_header(name)
        return redirected


HTTP_OPENER = urllib.request.build_opener(SafeRedirect())


def request(url, token=None, method="GET", payload=None, timeout=20):
    headers = {"User-Agent": "AntharesCF02HistoricalReceiptRecovery",
               "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = "Bearer " + token
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    return HTTP_OPENER.open(
        urllib.request.Request(url, headers=headers, data=data, method=method),
        timeout=timeout,
    )


def api_json(url, token, method="GET", payload=None):
    with request(url, token, method, payload) as response:
        return json.load(response)


def marker(log_text, name):
    # Match actual GitHub timestamped output line, not echoed shell source.
    match = re.search(
        r"(?m)^\d{4}-\d{2}-\d{2}T[^\r\n ]+\s+"
        + re.escape(name)
        + r"=([^\r\n]+)\r?$", log_text
    )
    require(match is not None, "original_log_marker_missing:" + name)
    return match.group(1).strip()


def verify_original(run, jobs, log_text):
    require(run.get("id") == SOURCE_RUN_ID, "wrong_original_run")
    require(run.get("head_sha") == SOURCE_HEAD_SHA, "unexpected_original_source_sha")
    require(run.get("event") == "workflow_dispatch", "wrong_original_event")
    require(run.get("status") == "completed" and run.get("conclusion") == "failure",
            "original_run_not_failed_on_receipt")
    require(str(run.get("path", "")).endswith(WORKFLOW_PATH),
            "original_run_wrong_workflow")
    job = next((j for j in jobs if j.get("name") == "deploy"), None)
    require(job is not None and job.get("conclusion") == "failure",
            "original_deploy_job_unavailable")
    steps = {s.get("name"): s.get("conclusion") for s in job.get("steps", [])}
    for name in REQUIRED_STEPS:
        require(steps.get(name) == "success", "original_step_unverified:" + name)
    require(steps.get(FAIL_RECEIPT_STEP) == "failure",
            "original_receipt_failure_missing")
    require(marker(log_text, "WRANGLER_DEPLOY_OK") == "1",
            "wrangler_deploy_evidence_missing")
    require(marker(log_text, "CONTROL_HEALTH_OK") == "1",
            "control_health_evidence_missing")
    removed = int(marker(log_text, "CORTES_LEGACY_CLEANUP_REMOVED"))
    protected = int(marker(log_text, "CORTES_LEGACY_CLEANUP_PROTECTED"))
    require("HTTP Error 409: Conflict" in log_text, "original_cas_409_missing")
    require(removed >= 0 and protected >= 0, "invalid_queue_evidence")
    return {"source_job_id": job["id"], "source_head_sha": run["head_sha"],
            "source_run_completed_at": run.get("updated_at"),
            "removed_count": removed, "protected_count_at_source": protected}


def verify_live_health(health):
    require(health.get("ok") is True, "controller_unhealthy")
    require(health.get("service") == "anthares-control", "controller_service_mismatch")
    require(health.get("version") == "2026-10-17-physical-android-v18",
            "controller_version_changed")
    require(health.get("persistent_state") is True and
            health.get("queue_bound") is True and health.get("pc_fallback") is False,
            "controller_state_or_queue_not_ready")
    return health


def utc_parse(s):
    if not s:
        return None
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def safe_prior_receipt(raw, source_run_finished):
    if not raw:
        return None
    previous = json.loads(raw)
    # Never replace evidence for a different, newer production deployment.
    if previous.get("source_workflow_run_id") == SOURCE_RUN_ID:
        return "same_source"
    prior_time = utc_parse(previous.get("checked_at_utc"))
    source_time = utc_parse(source_run_finished)
    require(prior_time is not None and source_time is not None,
            "cannot_order_prior_vs_original_deploy")
    require(prior_time <= source_time, "newer_production_receipt_exists")
    return "older"


def write_cas(receipt_url, token, receipt, source_run_finished):
    encoded = (json.dumps(receipt, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    encoded64 = base64.b64encode(encoded).decode("ascii")
    for attempt in range(3):
        current = api_json(receipt_url + "?ref=main", token)
        sha = current.get("sha")
        require(isinstance(sha, str) and len(sha) == 40, "receipt_sha_not_valid")
        old = base64.b64decode(current.get("content", ""))
        state = safe_prior_receipt(old, source_run_finished)
        if state == "same_source":
            old_json = json.loads(old)
            require(old_json.get("control_healthy") is True and
                    old_json.get("receipt_mode") == "verified_historical_recovery",
                    "existing_recovered_receipt_invalid")
            return {"status": "ALREADY_RECOVERED", "sha": sha, "body": old}
        body = {"message": "CF02 recover VERIFIED historical production deploy receipt [skip ci]",
                "branch": "main", "sha": sha, "content": encoded64}
        try:
            api_json(receipt_url, token, "PUT", body)
            saved = api_json(receipt_url + "?ref=main", token)
            back = base64.b64decode(saved.get("content", ""))
            require(back == encoded, "production_receipt_readback_mismatch")
            return {"status": "SAVED", "sha": saved.get("sha"), "body": back}
        except urllib.error.HTTPError as error:
            if error.code != 409 or attempt == 2:
                raise
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("CF02_CAS_RETRIES_EXHAUSTED")


def main():
    require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY,
            "github_repository_unexpected")
    require(os.environ.get("GITHUB_REF") == "refs/heads/main",
            "ref_not_production_main")
    require(os.environ.get("GITHUB_EVENT_NAME") in ("push", "workflow_dispatch"),
            "event_not_authorized")
    token = os.environ.get("GH_TOKEN", "")
    require(bool(token), "github_token_missing")
    base = "https://api.github.com/repos/" + REPOSITORY
    run = api_json(base + "/actions/runs/" + str(SOURCE_RUN_ID), token)
    print("CF02_ORIGINAL_RUN_API_READ_OK=1", flush=True)
    jobs = api_json(base + "/actions/runs/" + str(SOURCE_RUN_ID) +
                    "/jobs?per_page=100", token).get("jobs", [])
    print("CF02_ORIGINAL_JOBS_API_READ_OK=1", flush=True)
    job = next((j for j in jobs if j.get("name") == "deploy"), None)
    require(job is not None and isinstance(job.get("id"), int), "original_job_id_missing")
    with request(base + "/actions/jobs/" + str(job["id"]) + "/logs", token,
                 timeout=25) as response:
        log_text = response.read().decode("utf-8", errors="replace")
    print("CF02_ORIGINAL_LOGS_FETCHED_OK=1", flush=True)
    evidence = verify_original(run, jobs, log_text)
    print("CF02_ORIGINAL_DEPLOY_EVIDENCE_OK=1", flush=True)
    with request(HEALTH_URL, timeout=15) as response:
        health = verify_live_health(json.load(response))
    print("CF02_CURRENT_PRODUCTION_HEALTH_OK=1", flush=True)
    receipt = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "deploy_outcome": "success",
        "control_version": health["version"],
        "control_healthy": True,
        "cleanup_outcome": "success",
        "queue_error": None,
        "removed_count": evidence["removed_count"],
        "receipt_mode": "verified_historical_recovery",
        "source_workflow_run_id": SOURCE_RUN_ID,
        "source_job_id": evidence["source_job_id"],
        "source_head_sha": evidence["source_head_sha"],
        "source_run_conclusion": "failure_only_in_receipt_step",
        "source_run_completed_at": evidence["source_run_completed_at"],
        "protected_count_at_source": evidence["protected_count_at_source"],
        "live_health_observed_at": health.get("ts"),
        "recovery_execution_sha": os.environ.get("GITHUB_SHA"),
        "cloudflare_deploy_in_recovery": False,
        "queue_mutation_in_recovery": False,
        "current_queue_states_verified": False
    }
    saved = write_cas(base + "/contents/" + RECEIPT_PATH, token, receipt,
                      evidence["source_run_completed_at"])
    require(json.loads(saved["body"]).get("source_workflow_run_id") == SOURCE_RUN_ID,
            "wrong_recovered_source")
    print("CF02_PRODUCTION_RECEIPT_" + saved["status"] + "=1")
    print("CF02_RECEIPT_READBACK_SHA=" + str(saved["sha"]))
    print("CF02_SOURCE_PRODUCTION_RUN=" + str(SOURCE_RUN_ID))
    print("CF02_RECOVERY_DEPLOY_PERFORMED=0")
    print("CF02_RECOVERY_QUEUE_MUTATION=0")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("CF02_RECEIPT_RECOVERY_FAILED=" + str(e), file=sys.stderr)
        sys.exit(1)
