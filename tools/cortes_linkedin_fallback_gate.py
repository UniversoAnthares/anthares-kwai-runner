#!/usr/bin/env python3
"""Hosted LinkedIn personal standby: operate when the primary is unhealthy.

This read-only decision is advisory: Neon atomic leases, author identity,
daily quota and uncertain remote deliveries are the safety boundary.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import urllib.error
import urllib.request

REPO = "UniversoAnthares/anthares-kwai-runner"
PRIMARY = "cortes-linkedin-personal-fallback-cloud.yml"
HEALTH_MINUTES = 20


def need_standby(event: str, runs: list[dict], now: datetime) -> bool:
    if event in ("workflow_dispatch", "workflow_run"):
        return True
    if event != "schedule":
        return False
    cutoff = now - timedelta(minutes=HEALTH_MINUTES)
    for run in runs:
        if run.get("conclusion") != "success":
            continue
        if run.get("name") != "CORTES LinkedIn personal - primary hosted cloud publisher":
            continue
        try:
            updated = datetime.fromisoformat(str(run["updated_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        if updated.tzinfo is not None and updated >= cutoff:
            return False
    return True


def main() -> int:
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("RUNNER_ENVIRONMENT") != "github-hosted"):
        raise RuntimeError("STANDBY_CLOUD_ONLY")
    event = os.getenv("CORTES_STANDBY_EVENT", "")
    if event not in {"workflow_run", "workflow_dispatch", "schedule", "push"}:
        raise RuntimeError("STANDBY_UNEXPECTED_EVENT")
    if event in ("workflow_dispatch", "workflow_run"):
        run = True
    else:
        token = os.getenv("GITHUB_TOKEN") or ""
        if not token:
            raise RuntimeError("STANDBY_READONLY_GITHUB_TOKEN_REQUIRED")
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/workflows/{PRIMARY}/runs?per_page=12",
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "AntharesCortesLinkedInStandby/1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=18) as response:
                if response.status != 200:
                    raise RuntimeError("STANDBY_PRIMARY_HEALTH_HTTP")
                rows = json.load(response).get("workflow_runs") or []
            run = need_standby(event, rows, datetime.now(timezone.utc))
        except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError):
            # A broken health probe must NOT block redundancy.
            print("::warning::CORTES_STANDBY_PRIMARY_READBACK_UNAVAILABLE", flush=True)
            run = True
    outfile = os.getenv("GITHUB_OUTPUT")
    if not outfile:
        raise RuntimeError("STANDBY_GITHUB_OUTPUT_MISSING")
    with open(outfile, "a", encoding="utf-8") as output:
        output.write("run=" + ("true" if run else "false") + "\n")
    print("CORTES_PERSONAL_STANDBY_ACTIVATE=" + str(run).lower(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
