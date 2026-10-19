#!/usr/bin/env python3
"""Ephemeral, project-scoped GitLab runner for an isolated Anthares Secrets smoke test."""
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://gitlab.com/api/v4"
PROJECT = "87307248"
BRANCH = "test/anthares-secrets-protected-runner-20261019"
STATE = pathlib.Path(os.environ["RUNNER_TEMP"]) / "anthares-gl-sm"
STATE.mkdir(exist_ok=True, mode=0o700)
TOKEN = os.environ["GITLAB_TOKEN"]


def call(method, route, params=None):
    data = urllib.parse.urlencode(params).encode() if params else None
    req = urllib.request.Request(API + route, headers={"PRIVATE-TOKEN": TOKEN,
                            "Accept": "application/json",
                            "Content-Type": "application/x-www-form-urlencoded"},
                            method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # Parse only the offending *field names*, never print API bodies,
        # authentication tokens, or arbitrary server-provided values.
        error_fields = []
        try:
            body = json.loads(exc.read(8192))
            safe_keys = {"runner_type", "project_id", "tag_list", "run_untagged",
                         "access_level", "locked", "maximum_timeout", "base"}
            if isinstance(body, dict):
                error_fields = sorted(k for k in body.keys() if k in safe_keys)
                if not error_fields:
                    msg = str(body.get("message", "")).lower()
                    for key in sorted(safe_keys):
                        if key in msg:
                            error_fields.append(key)
                    if "scope" in msg or "permission" in msg:
                        error_fields.append("permission")
        except (ValueError, TypeError, OSError):
            pass
        if route == "/user/runners":
            print("RUNNER_API_ERROR_FIELDS=" + (",".join(error_fields) or "unclassified"))
        return exc.code, {}


def create():
    status, _ = call("POST", "/projects/" + PROJECT + "/protected_branches",
                   {"name": BRANCH, "push_access_level": "40", "merge_access_level": "40"})
    if status not in (200, 201, 409):
        print("BRANCH_PROTECT_HTTP_" + str(status))
        sys.exit(2)
    status, result = call("GET", "/projects/" + PROJECT + "/repository/branches/" + urllib.parse.quote(BRANCH, safe=""))
    if status != 200 or not result.get("protected"):
        print("BRANCH_PROTECTION_NOT_PROVEN")
        sys.exit(2)
    status, runner = call("POST", "/user/runners", {
        "runner_type": "project_type",
        "project_id": PROJECT,
        "description": "anthares-secrets-temporary-github-hosted-20261019",
        "tag_list[]": "anthares-secrets-probe",
        "run_untagged": "false",
        "access_level": "ref_protected",
        "locked": "true",
        "maximum_timeout": "600"
    })
    if status not in (200, 201) or not runner.get("token"):
        print("RUNNER_CREATE_HTTP_" + str(status))
        sys.exit(2)
    (STATE / "runner_id").write_text(str(runner["id"]))
    tok = STATE / "runner_token"
    tok.write_text(runner["token"])
    tok.chmod(0o600)
    print("TEMPORARY_RUNNER_CREATED_ID=" + str(runner["id"]))


def run_pipeline():
    status, pipeline = call("POST", "/projects/" + PROJECT + "/pipeline", {"ref": BRANCH})
    if status not in (200, 201):
        print("ISOLATED_PIPELINE_CREATE_HTTP_" + str(status))
        sys.exit(2)
    pid = pipeline["id"]
    print(f"ISOLATED_PIPELINE_URL=https://gitlab.com/UniversoAnthares/anthares-kwai-runner/-/pipelines/{pid}")
    end = time.monotonic() + 220
    while time.monotonic() < end:
        code, jobs = call("GET", "/projects/" + PROJECT + "/pipelines/" + str(pid) + "/jobs?per_page=30")
        if code != 200 or not isinstance(jobs, list):
            print("PIPELINE_JOBS_QUERY_HTTP_" + str(code))
            sys.exit(2)
        relevant = [x for x in jobs if x.get("name") == "anthares_secrets_smoke"]
        if relevant:
            state = relevant[0]["status"]
            if state == "success":
                print("GITLAB_BITWARDEN_SECRET_READ=PROVEN")
                return
            if state in ("failed", "canceled", "skipped"):
                print("GITLAB_SECRET_JOB_" + state.upper())
                print("GITLAB_JOB_FAILURE_REASON=" + str(relevant[0].get("failure_reason", "unknown")))
                sys.exit(2)
        time.sleep(6)
    print("ISOLATED_PIPELINE_TIMED_OUT")
    sys.exit(2)


def cleanup():
    f = STATE / "runner_id"
    if not f.exists():
        print("NO_EPHEMERAL_RUNNER_TO_REMOVE")
        return
    runner_id = f.read_text().strip()
    status, _ = call("DELETE", "/runners/" + runner_id)
    if status in (200, 202, 204, 404):
        print("EPHEMERAL_RUNNER_REMOVED=" + runner_id)
    else:
        print("EPHEMERAL_RUNNER_CLEANUP_BLOCKED=" + runner_id + " HTTP_" + str(status))


if __name__ == "__main__":
    {"create": create, "pipeline": run_pipeline, "cleanup": cleanup}[sys.argv[1]]()
