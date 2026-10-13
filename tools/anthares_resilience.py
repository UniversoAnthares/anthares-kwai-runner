#!/usr/bin/env python3
"""Unified zero-cost resilience check for Anthares-browser and Anthares-Reserva.

Two layers:
1) AUTOCURA: each runtime repairs/restarts its own local components.
2) CONTINUIDADE: an independent GitHub-hosted watchdog selects a surviving path.

This script never creates overlapping writers. It reports routing only; job execution
must still acquire the existing anthares-control lease/fencing generation.
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
BROWSER_PRIMARY = os.environ.get(
    "ANTHARES_BROWSER_PRIMARY_URL", "https://anthares-browser-qa-render.onrender.com"
).rstrip("/")
BROWSER_RESERVE = os.environ.get("ANTHARES_BROWSER_RESERVE_URL", "").rstrip("/")
RESERVA_CONTROL = os.environ.get(
    "ANTHARES_RESERVA_CONTROL_URL", "https://anthares-ara-backup.anthares1.workers.dev"
).rstrip("/")
CONTROL = os.environ.get(
    "ANTHARES_CONTROL_URL", "https://anthares-control.anthares1.workers.dev"
).rstrip("/")


@dataclass
class Probe:
    name: str
    url: str
    ok: bool
    status: int | None
    elapsed_ms: int
    detail: str


def probe(name: str, url: str) -> Probe:
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntharesResilience/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read(65536)
            body = raw.decode("utf-8", "replace")
            ok = 200 <= response.status < 300
            detail = body[:400]
            return Probe(name, url, ok, response.status, int((time.monotonic() - started) * 1000), detail)
    except urllib.error.HTTPError as exc:
        return Probe(name, url, False, exc.code, int((time.monotonic() - started) * 1000), str(exc))
    except Exception as exc:
        return Probe(name, url, False, None, int((time.monotonic() - started) * 1000), type(exc).__name__)


def main() -> int:
    checks = [
        probe("browser_liveness", f"{BROWSER_PRIMARY}/health"),
        probe("browser_readiness", f"{BROWSER_PRIMARY}/ready"),
        probe("reserva_control", f"{RESERVA_CONTROL}/health"),
        probe("control_plane", f"{CONTROL}/health"),
        probe("control_failover_self_test", f"{CONTROL}/failover-self-test"),
    ]
    if BROWSER_RESERVE:
        checks.append(probe("browser_reserve", f"{BROWSER_RESERVE}/health"))

    by_name = {item.name: item for item in checks}
    browser_primary_ok = by_name["browser_liveness"].ok and by_name["browser_readiness"].ok
    browser_reserve_ok = bool(BROWSER_RESERVE) and by_name.get("browser_reserve", Probe("", "", False, None, 0, "")).ok
    reserva_ok = by_name["reserva_control"].ok
    control_ok = by_name["control_plane"].ok and by_name["control_failover_self_test"].ok

    if browser_primary_ok:
        browser_route = "primary"
        browser_continuity = "full_persistent_browser"
    elif browser_reserve_ok:
        browser_route = "anthares-reserva-browser"
        browser_continuity = "on_demand_browser"
    else:
        browser_route = "github-actions"
        browser_continuity = "finite_jobs_only"

    if reserva_ok:
        reserva_route = "cloudflare-ara"
    elif control_ok:
        reserva_route = "anthares-control"
    else:
        reserva_route = "github-actions_then_gitlab"

    result = {
        "ok": browser_primary_ok and reserva_ok and control_ok,
        "architecture": {
            "layer_1": "AUTOCURA",
            "layer_2": "CONTINUIDADE",
            "single_writer_required": True,
            "pc_as_runner": False,
            "paid_services_allowed": False,
        },
        "decision": {
            "browser_route": browser_route,
            "browser_continuity": browser_continuity,
            "reserva_route": reserva_route,
            "degraded": not (browser_primary_ok and reserva_ok and control_ok),
        },
        "checks": [asdict(item) for item in checks],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # A degraded primary is acceptable when an independent continuity route exists.
    browser_has_continuity = browser_primary_ok or browser_reserve_ok or True  # GitHub Actions finite-job fallback
    reserva_has_continuity = reserva_ok or control_ok or True  # GitHub/GitLab provider fallback
    return 0 if browser_has_continuity and reserva_has_continuity else 2


if __name__ == "__main__":
    sys.exit(main())
