#!/usr/bin/env python3
"""Deduplicated urgent QA notice for X pipeline infrastructure failures."""
import json
import os
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

REPO = "UniversoAnthares/anthares-kwai-runner"
TITLE = "[QA-P0][X] pipeline failure and recovery required"

def request(path, method="GET", obj=None):
    b = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/" + path, data=b, method=method,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "anthares-x-qa"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main():
    if not (os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"):
        raise RuntimeError("X_QA_NOTIFY_GITHUB_ONLY")
    now = datetime.now(ZoneInfo("America/Campo_Grande")).isoformat(timespec="seconds")
    origin = os.getenv("GITHUB_RUN_ID", "unknown")
    phase = os.getenv("X_QA_PHASE", "unknown")
    details = "At " + now + ", X pipeline phase " + phase + " failed in GitHub Actions run https://github.com/" + REPO + "/actions/runs/" + origin + ". Investigate source credentials/download, session, queue and fallbacks. No blind X retry."
    issues = request("issues?state=open&per_page=100")
    existing = next((i for i in issues if i.get("title") == TITLE), None)
    if existing:
        request("issues/" + str(existing["number"]) + "/comments", "POST", {"body": details})
        print("X_QA_P0_UPDATED_ISSUE=" + str(existing["number"]))
    else:
        issue = request("issues", "POST", {"title": TITLE, "body": details})
        print("X_QA_P0_CREATED_ISSUE=" + str(issue["number"]))

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("X_QA_P0_DELIVERY_FAILED=" + type(exc).__name__)
        sys.exit(2)
