#!/usr/bin/env python3
"""Anthares GitLab quota watcher. CI validation only; never runs publishers/deploys."""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

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
    with urllib.request.urlopen(req, timeout=18) as resp:
        return json.loads(resp.read() or b"{}") if resp.status != 204 else {}


def recent_qualifying_failure(project_id):
    url = ("https://gitlab.com/api/v4/projects/" + project_id +
           "/pipelines?status=failed&ref=main&per_page=8&order_by=id&sort=desc")
    pipelines = api(url, GL_AUTH, gl=True)
    now = dt.datetime.now(dt.timezone.utc)
    for p in pipelines:
        stamp = dt.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
        if (now - stamp).total_seconds() > WINDOW_MINUTES * 60:
            break
        if p.get("ref") != "main" or not p.get("sha"):
            continue
        jobs = api("https://gitlab.com/api/v4/projects/" + project_id +
                   "/pipelines/" + str(p["id"]) + "/jobs?per_page=100", GL_AUTH, gl=True)
        failed_quota = [j for j in jobs if j.get("failure_reason") == "ci_quota_exceeded"
                        and j.get("started_at") is None]
        if failed_quota:
            return {"id": p["id"], "sha": p["sha"], "count": len(failed_quota)}
    return None


def latest_runs(workflow):
    url = (f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/" +
           urllib.parse.quote(workflow) + "/runs?per_page=70")
    return api(url, GH_AUTH).get("workflow_runs", [])


def already_handled(component, workflow, sha, runs):
    key = f"glsha-{component}-{sha[:12]}"
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
    # Backups are QA-only. Do not retry failed GitLab pipelines or modify source/queues.
    runs_cache = {}
    errors = 0
    for component, project_id, workflow in PROJECTS:
        try:
            event = recent_qualifying_failure(project_id)
            if not event:
                print(f"{component}=NO_RECENT_MAIN_QUOTA_FAILURE")
                continue
            if workflow not in runs_cache:
                runs_cache[workflow] = latest_runs(workflow)
            if already_handled(component, workflow, event["sha"], runs_cache[workflow]):
                print(f"{component}=DEDUPED sha={event['sha'][:12]}")
                continue
            dispatch(component, workflow, event)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError) as exc:
            # Never expose request URLs, response bodies, tokens or sensitive metadata.
            print(f"{component}=CONTROL_ERROR type={type(exc).__name__}")
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
