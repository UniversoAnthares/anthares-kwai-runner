"""Unattended Anthares worker preflight.

Persistent managed browser profiles are the primary authentication path. Session
Capsule remains a fallback for a single target platform. No session contents are
printed or written to readiness artifacts.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from persistent_publisher import decode_managed_profiles, require_platforms
from recovery import choose_executor
from session_capsule import decode_capsule


def _platform_from_domain(domain: str) -> str | None:
    value = (domain or "").lower()
    if value == "tiktok.com" or value.endswith(".tiktok.com"):
        return "tiktok"
    if value == "kwai.com" or value.endswith(".kwai.com"):
        return "kwai"
    return None


def readiness(
    *,
    managed_profiles_value: str | None = None,
    session_value: str | None = None,
    executors: list[dict],
    required_platforms: tuple[str, ...] = ("tiktok", "kwai"),
) -> dict:
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executor": None,
        "authentication": "blocked",
        "auth_mode": None,
        "authenticated_platforms": [],
        "ready": False,
        "blockers": [],
    }
    try:
        state["executor"] = choose_executor(executors)
    except RuntimeError as exc:
        state["blockers"].append(str(exc))

    managed_error = None
    if managed_profiles_value:
        try:
            proofs = decode_managed_profiles(managed_profiles_value)
            by_platform = require_platforms(proofs, required_platforms)
            state["authentication"] = "verified"
            state["auth_mode"] = "managed_profiles"
            state["authenticated_platforms"] = sorted(by_platform)
            state["profiles"] = {
                platform: {
                    "provider": proof.provider,
                    "profile_id": proof.profile_id,
                    "account_handle": proof.account_handle,
                    "checked_at": proof.checked_at,
                }
                for platform, proof in by_platform.items()
            }
        except RuntimeError as exc:
            managed_error = str(exc)

    if state["authentication"] != "verified" and session_value:
        try:
            capsule = decode_capsule(session_value)
            platform = _platform_from_domain(capsule["domain"])
            required = set(required_platforms)
            if platform is None:
                raise RuntimeError("session_capsule_platform_unknown")
            if required != {platform}:
                missing = ",".join(sorted(required - {platform}))
                raise RuntimeError(f"session_capsule_missing_platforms:{missing}")
            state["authentication"] = "verified"
            state["auth_mode"] = "session_capsule"
            state["authenticated_platforms"] = [platform]
            state["session_domain"] = capsule["domain"]
            state["session_expires_at"] = capsule["expires_at"]
        except RuntimeError as exc:
            state["blockers"].append(str(exc))

    if state["authentication"] != "verified":
        if managed_error:
            state["blockers"].append(managed_error)
        if not managed_profiles_value and not session_value:
            state["blockers"].append("authentication_proof_missing")

    state["ready"] = bool(state["executor"] and state["authentication"] == "verified")
    return state


def main() -> int:
    candidates = [
        {
            "name": os.environ.get("ANTHARES_EXECUTOR_NAME", "github-hosted"),
            "priority": 10,
            "healthy": os.environ.get("ANTHARES_EXECUTOR_HEALTHY", "1") == "1",
        }
    ]
    required = tuple(
        p.strip().lower()
        for p in os.environ.get("ANTHARES_REQUIRED_PLATFORMS", "tiktok,kwai").split(",")
        if p.strip()
    )
    state = readiness(
        managed_profiles_value=os.environ.get("ANTHARES_MANAGED_PROFILES_JSON"),
        session_value=os.environ.get("ANTHARES_SESSION_B64"),
        executors=candidates,
        required_platforms=required,
    )
    output = os.environ.get("ANTHARES_READINESS_OUTPUT", "anthares-readiness.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    print(json.dumps({
        "ready": state["ready"],
        "executor": state["executor"],
        "authentication": state["authentication"],
        "auth_mode": state["auth_mode"],
        "authenticated_platforms": state["authenticated_platforms"],
        "blockers": state["blockers"],
    }, ensure_ascii=False))
    return 0 if state["ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
