#!/usr/bin/env python3
"""Fail-closed resilience check for Anthares Browser and Anthares Remote.

Operational invariants:
- Anthares Remote is the only remote-control surface.
- Anthares Browser is the only browser-automation surface.
- Browserless, TinyFish paid Agent/Browser, Render and CircleCI are never browser fallbacks.
- TinyFish Search/Fetch are allowed only for public, read-only pages.
- External infrastructure may support Anthares internals only when its own health and quota are eligible.

When ANTHARES_RESILIENCE_REPORT_ONLY=1, missing external runtime evidence is reported
without turning a finite CI policy watchdog red. Real runtime verification remains a
separate per-round requirement and must never be fabricated inside GitHub Actions.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

TIMEOUT = float(os.environ.get("ANTHARES_HEALTH_TIMEOUT", "8"))
BROWSER_PRIMARY = os.environ.get("ANTHARES_BROWSER_PRIMARY_URL", "").rstrip("/")
BROWSER_RESERVE = os.environ.get("ANTHARES_BROWSER_PERSISTENT_RESERVE_URL", "").rstrip("/")
REMOTE_HEARTBEAT_FRESH = os.environ.get("ANTHARES_REMOTE_HEARTBEAT_FRESH", "0") == "1"
REMOTE_COMMAND_ROUNDTRIP = os.environ.get("ANTHARES_REMOTE_COMMAND_ROUNDTRIP", "0") == "1"
REPORT_ONLY = os.environ.get("ANTHARES_RESILIENCE_REPORT_ONLY", "0") == "1"


@dataclass
class Probe:
    name: str
    url: str
    ok: bool
    status: int | None
    elapsed_ms: int
    detail: str


def probe(name: str, url: str) -> Probe:
    if not url:
        return Probe(name, "", False, None, 0, "disabled")
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntharesResilience/3.1"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read(65536)
            body = raw.decode("utf-8", "replace")
            ok = 200 <= response.status < 300
            return Probe(name, url, ok, response.status, int((time.monotonic() - started) * 1000), body[:400])
    except urllib.error.HTTPError as exc:
        return Probe(name, url, False, exc.code, int((time.monotonic() - started) * 1000), str(exc))
    except Exception as exc:
        return Probe(name, url, False, None, int((time.monotonic() - started) * 1000), type(exc).__name__)


def browser_pair(prefix: str, origin: str) -> list[Probe]:
    if not origin:
        return [
            Probe(f"{prefix}_liveness", "", False, None, 0, "disabled"),
            Probe(f"{prefix}_readiness", "", False, None, 0, "disabled"),
        ]
    return [
        probe(f"{prefix}_liveness", f"{origin}/health"),
        probe(f"{prefix}_readiness", f"{origin}/ready"),
    ]


def main() -> int:
    checks = browser_pair("browser_primary", BROWSER_PRIMARY) + browser_pair("browser_reserve", BROWSER_RESERVE)
    by_name = {item.name: item for item in checks}
    primary_ok = bool(BROWSER_PRIMARY) and by_name["browser_primary_liveness"].ok and by_name["browser_primary_readiness"].ok
    reserve_ok = bool(BROWSER_RESERVE) and by_name["browser_reserve_liveness"].ok and by_name["browser_reserve_readiness"].ok
    remote_ok = REMOTE_HEARTBEAT_FRESH and REMOTE_COMMAND_ROUNDTRIP

    if primary_ok:
        browser_route = "anthares-browser-primary"
    elif reserve_ok:
        browser_route = "anthares-browser-persistent-reserve"
    else:
        browser_route = "anthares-browser-unavailable"

    continuity_ok = (primary_ok or reserve_ok) and remote_ok
    runtime_evidence_complete = bool(BROWSER_PRIMARY or BROWSER_RESERVE) and (
        REMOTE_HEARTBEAT_FRESH or REMOTE_COMMAND_ROUNDTRIP
    )
    result = {
        "ok": continuity_ok,
        "continuity_ok": continuity_ok,
        "report_only": REPORT_ONLY,
        "runtime_evidence_complete": runtime_evidence_complete,
        "architecture": {
            "single_writer_required": True,
            "remote_control_surface": "anthares-remote",
            "browser_surface": "anthares-browser",
            "other_remote_allowed": False,
            "browserless_allowed": False,
            "tinyfish_allowed": False,
            "tinyfish_public_fetch_allowed": bool(os.getenv("TINYFISH_API_KEY")),
            "tinyfish_public_search_allowed": bool(os.getenv("TINYFISH_API_KEY")),
            "render_allowed": False,
            "circleci_allowed": False,
            "paid_services_allowed_without_owner_decision": False,
        },
        "remote_control": {
            "route": "anthares-remote",
            "heartbeat_fresh": REMOTE_HEARTBEAT_FRESH,
            "command_roundtrip": REMOTE_COMMAND_ROUNDTRIP,
            "healthy": remote_ok,
        },
        "decision": {
            "browser_route": browser_route,
            "browser_primary_ok": primary_ok,
            "browser_persistent_reserve_ok": reserve_ok,
            "browser_equivalent_continuity": primary_ok or reserve_ok,
            "browser_redundancy_complete": primary_ok and reserve_ok,
            "remote_ok": remote_ok,
            "degraded": not continuity_ok or not (primary_ok and reserve_ok),
        },
        "checks": [asdict(item) for item in checks],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if REPORT_ONLY:
        return 0
    return 0 if continuity_ok else 2


if __name__ == "__main__":
    sys.exit(main())
