"""Persistent filesystem restart proof for Anthares cloud publishers.

This module records only boot identifiers and timestamps. It never reads or writes
browser cookies, tokens, local storage or credentials.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

ALLOWED_PLATFORMS = {"tiktok", "kwai"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _boot_id() -> str:
    path = Path("/proc/sys/kernel/random/boot_id")
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    return f"pid-namespace-{os.getpid()}"


def persistent_root(value: str | Path | None = None) -> Path:
    raw = value or os.environ.get("ANTHARES_PERSISTENT_ROOT") or "/workspaces/.anthares-private"
    root = Path(raw).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    return root


def profile_dir(platform: str, root: str | Path | None = None) -> Path:
    platform = platform.lower().strip()
    if platform not in ALLOWED_PLATFORMS:
        raise ValueError("platform_invalid")
    target = persistent_root(root) / "browser-profiles" / platform
    target.mkdir(parents=True, exist_ok=True)
    try:
        target.chmod(0o700)
    except OSError:
        pass
    return target


def observe_restart(
    platform: str,
    *,
    root: str | Path | None = None,
    boot_id: str | None = None,
    observed_at: str | None = None,
) -> dict:
    platform = platform.lower().strip()
    if platform not in ALLOWED_PLATFORMS:
        raise ValueError("platform_invalid")
    current_boot = (boot_id or _boot_id()).strip()
    if not current_boot:
        raise ValueError("boot_id_required")
    now = observed_at or _utc_now()
    base = persistent_root(root)
    marker_dir = base / "persistence"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / f"{platform}.json"

    previous = None
    if marker.exists():
        previous = json.loads(marker.read_text(encoding="utf-8"))

    restart_count = int(previous.get("restart_count", 0)) if previous else 0
    first_observed_at = previous.get("first_observed_at", now) if previous else now
    first_boot_id = previous.get("first_boot_id", current_boot) if previous else current_boot
    previous_boot_id = previous.get("last_boot_id") if previous else None
    persistence_verified = bool(previous and previous_boot_id and previous_boot_id != current_boot)
    if persistence_verified:
        restart_count += 1

    row = {
        "platform": platform,
        "first_boot_id": first_boot_id,
        "last_boot_id": current_boot,
        "first_observed_at": first_observed_at,
        "last_observed_at": now,
        "restart_count": restart_count,
        "persistence_verified": persistence_verified or bool(previous and previous.get("persistence_verified")),
    }
    tmp = marker.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(row, sort_keys=True, indent=2), encoding="utf-8")
    tmp.replace(marker)
    return {
        "platform": platform,
        "profile_dir": str(profile_dir(platform, base)),
        "restart_count": row["restart_count"],
        "persistence_verified": row["persistence_verified"],
        "first_observed_at": row["first_observed_at"],
        "last_observed_at": row["last_observed_at"],
    }
