#!/usr/bin/env python3
"""Inventory free remote executors using only non-secret CI environment metadata."""
import json
import os
import platform
import shutil
from datetime import datetime, timezone

def inventory():
    providers = {
        "github_actions": {"detected": bool(os.getenv("GITHUB_ACTIONS")), "available": bool(os.getenv("GITHUB_ACTIONS")),
            "runner_os": os.getenv("RUNNER_OS"), "runner_name": os.getenv("RUNNER_NAME"),
            "repo": os.getenv("GITHUB_REPOSITORY")},
        "gitlab_ci": {"detected": bool(os.getenv("GITLAB_CI")), "available": bool(os.getenv("GITLAB_CI")),
            "runner_id": os.getenv("CI_RUNNER_ID"), "runner_tags": os.getenv("CI_RUNNER_TAGS")},
        "render": {"detected": bool(os.getenv("RENDER")), "available": bool(os.getenv("RENDER")),
            "service_id": os.getenv("RENDER_SERVICE_ID")},
        "cloudflare": {"detected": bool(os.getenv("CF_PAGES") or os.getenv("CLOUDFLARE_ACCOUNT_ID")),
            "available": None, "note": "Configuration presence does not prove API access."}
    }
    return {
        "schema": "anthares.core.capabilities.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "host": {"os": platform.system(), "architecture": platform.machine(),
                 "python": platform.python_version(), "git": bool(shutil.which("git")),
                 "adb": bool(shutil.which("adb")), "docker": bool(shutil.which("docker"))},
        "providers": providers,
        "limitations": ["Detected CI environment is not a verified persistent executor.",
                        "Cloudflare API access must be checked separately without exposing tokens.",
                        "Free quotas and off-host storage are not established by this inventory."]
    }

if __name__ == "__main__":
    print(json.dumps(inventory(), sort_keys=True, indent=2))
