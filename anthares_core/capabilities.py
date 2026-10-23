#!/usr/bin/env python3
"""Inventory execution capabilities without conflating health, quota and provider identity."""
from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import datetime, timezone

RETIRED = {"render", "tinyfish", "circleci", "browserless"}


def _github_actions():
    detected = bool(os.getenv("GITHUB_ACTIONS"))
    repo = os.getenv("GITHUB_REPOSITORY")
    visibility = os.getenv("ANTHARES_GITHUB_REPO_VISIBILITY", "unknown").lower()
    quota_hint = os.getenv("ANTHARES_GITHUB_ACTIONS_QUOTA", "unknown").upper()
    return {
        "detected": detected,
        "available": detected and quota_hint != "BLOCKED_QUOTA",
        "runner_os": os.getenv("RUNNER_OS"),
        "runner_name": os.getenv("RUNNER_NAME"),
        "repo": repo,
        "visibility": visibility,
        "quota_state": quota_hint,
        "note": "Public and private Actions quotas must be evaluated independently.",
    }


def _gitlab_ci():
    detected = bool(os.getenv("GITLAB_CI"))
    quota_hint = os.getenv("ANTHARES_GITLAB_CI_QUOTA", "BLOCKED_QUOTA").upper()
    return {
        "detected": detected,
        "available": detected and quota_hint != "BLOCKED_QUOTA",
        "runner_id": os.getenv("CI_RUNNER_ID"),
        "runner_tags": os.getenv("CI_RUNNER_TAGS"),
        "quota_state": quota_hint,
        "note": "Current Anthares GitLab namespaces are blocked by ci_quota_exceeded until fresh proof.",
    }


def inventory():
    providers = {
        "anthares_remote": {
            "exclusive_remote_control": True,
            "health_probe": "fresh heartbeat + successful command round-trip",
            "available": None,
        },
        "anthares_browser": {
            "exclusive_browser_surface": True,
            "available": None,
            "note": "Internal infrastructure health is evaluated separately from browser product identity.",
        },
        "tinyfish_fetch": {
            "available": bool(os.getenv("TINYFISH_API_KEY")),
            "role": "public_url_read", "billable_execution": False,
            "note": "Free recurring daily quota; never a publication or browser-proof authority.",
        },
        "tinyfish_search": {
            "available": bool(os.getenv("TINYFISH_API_KEY")),
            "role": "public_research", "billable_execution": False,
            "note": "Free recurring quota; discovery must honor source curation.",
        },
        "github_actions": _github_actions(),
        "gitlab_ci": _gitlab_ci(),
        "cloudflare_workers": {
            "detected": bool(os.getenv("CF_PAGES") or os.getenv("CLOUDFLARE_ACCOUNT_ID")),
            "available": None,
            "note": "Workers, Workers Builds, Durable Objects and Browser Rendering have separate status/quota domains.",
        },
    }
    for name in sorted(RETIRED):
        providers[name] = {"available": False, "retired": True, "selectable": False}

    return {
        "schema": "anthares.core.capabilities.v2",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "os": platform.system(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "git": bool(shutil.which("git")),
            "adb": bool(shutil.which("adb")),
            "docker": bool(shutil.which("docker")),
        },
        "providers": providers,
        "policy": {
            "remote_control": ["anthares_remote"],
            "browser": ["anthares_browser"],
            "retired": sorted(RETIRED),
            "quota_blocked_is_not_down": True,
            "unknown_is_not_ready": True,
        },
        "limitations": [
            "Environment detection alone does not prove current provider health.",
            "Quota state must be refreshed from provider evidence before quota-sensitive execution.",
            "No retired provider may become eligible from environment detection.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), sort_keys=True, indent=2))
