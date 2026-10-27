#!/usr/bin/env python3
"""Anthares GitLab quota watcher. CI validation only; never runs publishers/deploys."""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from ci_quota_provider_adapters import GitLabPipeline, ProviderUncertain

GITHUB_REPO = "UniversoAnthares/anthares-kwai-runner"
PROJECTS = (
    ("cortes", "87307248", "gitlab-quota-fallback.yml"),
    ("clipper", "87361774", "private-ci-quota-rescue.yml"),
    ("wordpress", "87361776", "private-ci-quota-rescue.yml"),
)
WINDOW_MINUTES = 90
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
GL_AUTH = os.environ.get("GITLAB_TOKEN", "")
GH_AUTH = os.environ.get("GH_TOKEN", "")


def api(url, token="", method="GET", payload=None, gl=False):
    headers = {"Accept": "application/json", "User-Agent": "Anthares-Quota-Failover/1"}
    if gl and token:
        headers["PRIVATE-TOKEN"] = token
    elif token:
        headers["Authorization"] = "Bearer " + token
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    raw = None if payload is None else json.dumps(payload).encode("utf-8")
    if raw is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=method)
    # A transient GitLab/GitHub timeout must not abort the other components.
    # Retry only safe idempotent reads; never repeat workflow dispatches.
    attempts = 2 if method == "GET" else 1
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read() or b"{}") if resp.status != 204 else {}
        except urllib.error.HTTPError as exc:
            if method == "GET" and attempt + 1 < attempts and exc.code in (429, 500, 502, 503, 504):
                time.sleep(1)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt + 1 >= attempts:
                raise
            time.sleep(1)
    raise RuntimeError("API_READ_RETRIES_EXHAUSTED")


def recent_qualifying_failure(project_id):
    url = ("https://gitlab.com/api/v4/projects/" + project_id +
           "/pipelines?ref=main&per_page=16&order_by=id&sort=desc")
    pipelines = api(url, GL_AUTH, gl=True)
    now = dt.datetime.now(dt.timezone.utc)
    for p in pipelines:
        stamp = dt.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
        if (now - stamp).total_seconds() > WINDOW_MINUTES * 60:
            break
        if (p.get("ref") != "main" or not p.get("sha") or
                p.get("status") not in
                ("failed","canceled","running","pending","created","preparing","waiting_for_resource")):
            continue
        jobs = api("https://gitlab.com/api/v4/projects/" + project_id +
                   "/pipelines/" + str(p["id"]) + "/jobs?per_page=100", GL_AUTH, gl=True)
        # Never infer quota from a generic failing job or a permission denial.
        if not isinstance(jobs,list) or len(jobs)>=100:
            continue  # incomplete job-page evidence: fail closed
        failed_quota = [j for j in jobs if j.get("failure_reason") == "ci_quota_exceeded"
                        and j.get("status") == "failed" and j.get("started_at") is None]
        if failed_quota:
            return {"id": p["id"], "sha": p["sha"], "count": len(failed_quota)}
    return None


def confirmed_terminal_before_reserve(project_id, event):
    """Cancel only the exact owned GitLab quota pipeline if still active.

    Existing FAILED/CANCELLED already are terminal; no active job is available
    to cancel after GitLab's own ci_quota_exceeded rejection. Never dispatch
    while an exact pipeline is still RUNNING, SUCCEEDED or UNKNOWN.
    """
    if not GL_AUTH or not str(event.get("id","")).isdigit():
        return False
    pipeline=GitLabPipeline(project_id,event["id"],GL_AUTH)
    state=pipeline.status(str(event["id"]))
    if state in ("FAILED","CANCELLED"):
        return True
    if state!="RUNNING":
        return False
    # Before canceling the entire pipeline, re-check its immutable identity
    # and every job. A pipeline containing unrelated active jobs is shared;
    # it must not be terminated on behalf of a quota-failed CI job.
    endpoint=("https://gitlab.com/api/v4/projects/" + str(project_id) +
              "/pipelines/" + str(event["id"]))
    identity=api(endpoint, GL_AUTH, gl=True)
    if (not isinstance(identity,dict) or identity.get("sha") != event.get("sha")
            or identity.get("ref") != "main" or
            identity.get("status") not in
            ("running","pending","created","preparing","waiting_for_resource")):
        return False
    jobs=api(endpoint+"/jobs?per_page=100", GL_AUTH, gl=True)
    if not isinstance(jobs,list) or len(jobs)>=100:
        return False
    confirmed_quota=any(
        j.get("failure_reason")=="ci_quota_exceeded" and
        j.get("status")=="failed" and j.get("started_at") is None
        for j in jobs)
    active_other=any(
        j.get("status") in
        ("running","pending","created","preparing","waiting_for_resource")
        for j in jobs)
    if not confirmed_quota or active_other:
        return False
    # Dry-run remains read-only even if a cancelable live quota appears.
    if DRY_RUN:
        print("DRY_RUN_CANCEL_WOULD_BE_REQUESTED",flush=True)
        return False
    # No other job is running; only now may this exact quota pipeline be
    # canceled. Never reissue an uncertain cancel within the same attempt.
    if not pipeline.cancel(str(event["id"])):
        return False
    return pipeline.status(str(event["id"])) in ("FAILED","CANCELLED")


def latest_runs(workflow):
    url = (f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/" +
           urllib.parse.quote(workflow) + "/runs?per_page=70")
    return api(url, GH_AUTH).get("workflow_runs", [])


def already_handled(component, workflow, sha, runs):
    key = f"quota-rescue-{component}-glsha-{sha}"
    if any(key in str(r.get("display_title", "")) for r in runs):
        return True
    # Additional limit: one attempt per component every 15 min, including in-progress.
    now = dt.datetime.now(dt.timezone.utc)
    for run in runs:
        if run.get("event") != "workflow_dispatch":
            continue
        if component != "cortes" and f"quota-rescue-{component}-" not in str(run.get("display_title", "")):
            continue
        if component == "cortes" and "quota-rescue-cortes-" not in str(run.get("display_title", "")):
            continue
        created = dt.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        if (now - created).total_seconds() < 900:
            return True
    return False


def reserve_quota_handoff(component, project_id, event):
    """Reserve exactly one GitLab quota successor across independently running hosts.

    Source pipeline cancellation/terminal check has already passed. A failed,
    ambiguous or duplicated Neon reservation must not dispatch a successor.
    """
    if DRY_RUN:
        return "DRY_RUN"
    controller=os.environ.get("ANTHARES_CI_QUOTA_LEDGER_URL", "")
    if not controller.startswith("https://") or not controller.endswith("/api/gitlab-reserve"):
        return "CONTROLLER_UNCONFIGURED"
    oidc_url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    oidc_access=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not (oidc_url and oidc_access and GL_AUTH):
        return "OIDC_OR_GITLAB_CREDENTIAL_UNAVAILABLE"
    sep="&" if "?" in oidc_url else "?"
    requested=oidc_url+sep+urllib.parse.urlencode(
        {"audience":"anthares-ci-quota-controller"})
    try:
        with urllib.request.urlopen(urllib.request.Request(
            requested, headers={"Authorization":"Bearer "+oidc_access}),
            timeout=10) as resp:
            identity=json.load(resp).get("value", "")
        if not identity:
            return "OIDC_UNAVAILABLE"
        body=json.dumps({"component":component,"project_id":str(project_id),
                         "pipeline_id":str(event["id"]),"sha":str(event["sha"])}).encode()
        with urllib.request.urlopen(urllib.request.Request(
            controller,data=body,method="POST",headers={
                "Authorization":"Bearer "+identity,
                "X-Gitlab-Token":GL_AUTH,
                "Content-Type":"application/json"}),timeout=25) as resp:
            receipt=json.load(resp)
        return "RESERVED" if (receipt.get("ok") is True and
              receipt.get("state")=="FALLBACK_RESERVED") else "UNCERTAIN"
    except urllib.error.HTTPError as exc:
        # 409 is an existing reservation or a rejected stale identity.
        # Both must block duplicate dispatch without exposing remote details.
        return "ALREADY_OR_INVALID" if exc.code in (400,401,403,409) else "UNAVAILABLE"
    except (urllib.error.URLError,OSError,TimeoutError,ValueError,KeyError):
        return "UNAVAILABLE"


def acknowledge_quota_dispatch(component, project_id, event):
    """Record a successful GitHub 204 dispatch without assuming post success."""
    url=os.environ.get("ANTHARES_CI_QUOTA_LEDGER_URL","")
    if not url.endswith("/api/gitlab-reserve"):
        return False
    destination=url.replace("/api/gitlab-reserve","/api/gitlab-ack")
    identity_url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    identity_access=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    watcher_run=os.environ.get("GITHUB_RUN_ID","")
    if not (identity_url and identity_access and watcher_run.isdecimal()):
        return False
    sep="&" if "?" in identity_url else "?"
    try:
        audience=identity_url+sep+urllib.parse.urlencode(
            {"audience":"anthares-ci-quota-controller"})
        with urllib.request.urlopen(urllib.request.Request(
            audience, headers={"Authorization":"Bearer "+identity_access}),
            timeout=10) as resp:
            identity=json.load(resp).get("value","")
        if not identity:
            return False
        body=json.dumps({"component":component,"project_id":str(project_id),
            "pipeline_id":str(event["id"]),"sha":str(event["sha"]),
            "watcher_run_id":watcher_run}).encode()
        with urllib.request.urlopen(urllib.request.Request(
            destination,data=body,method="POST",headers={
                "Authorization":"Bearer "+identity,
                "Content-Type":"application/json"}),timeout=20) as resp:
            reply=json.load(resp)
        return reply.get("ok") is True and reply.get("state")=="FALLBACK_SUBMITTED"
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,
            TimeoutError,ValueError,KeyError):
        return False


def dispatch(component, workflow, p):
    inputs = {"gitlab_pipeline_id": str(p["id"]), "gitlab_sha": p["sha"]}
    if workflow == "private-ci-quota-rescue.yml":
        inputs["component"] = component
    if DRY_RUN:
        print(f"DRY_RUN_DISPATCH {component} {workflow} pipeline={p['id']}")
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow}/dispatches"
    api(url, GH_AUTH, "POST", {"ref": "main", "inputs": inputs})
    print(f"DISPATCHED {component} pipeline={p['id']}")


def main():
    if not GL_AUTH or not GH_AUTH:
        print("WATCHER_BLOCKED: missing protected API credentials")
        return 1
    # Backups are QA-only. Cancel owned terminal-quota pipelines only after checking no other active jobs; never retry original CI jobs.
    runs_cache = {}
    errors = 0
    for component, project_id, workflow in PROJECTS:
        try:
            event = recent_qualifying_failure(project_id)
            if not event:
                print(f"{component}=NO_RECENT_MAIN_QUOTA_FAILURE")
                continue
            # Exact GitLab pipeline must be remotely terminal before any
            # independent QA dispatch. Missing/uncertain status fails closed.
            if not confirmed_terminal_before_reserve(project_id, event):
                print(f"{component}=CANCEL_UNCONFIRMED_NO_FALLBACK")
                errors += 1
                continue
            if workflow not in runs_cache:
                runs_cache[workflow] = latest_runs(workflow)
            if already_handled(component, workflow, event["sha"], runs_cache[workflow]):
                print(f"{component}=DEDUPED sha={event['sha'][:12]}")
                continue
            claim=reserve_quota_handoff(component, project_id, event)
            if claim != "RESERVED":
                print(f"{component}=SHARED_LEDGER_{claim}_NO_DISPATCH")
                if claim not in ("ALREADY_OR_INVALID", "DRY_RUN"):
                    errors += 1
                continue
            dispatch(component, workflow, event)
            if not acknowledge_quota_dispatch(component, project_id, event):
                print(f"{component}=DISPATCH_ACCEPTED_LEDGER_ACK_UNCERTAIN")
                errors += 1
            else:
                print(f"{component}=DISPATCH_ACCEPTED_LEDGER_ACKED")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, ProviderUncertain) as exc:
            # Never expose request URLs, response bodies, tokens or sensitive metadata.
            print(f"{component}=CONTROL_ERROR type={type(exc).__name__}")
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
