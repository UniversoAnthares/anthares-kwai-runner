#!/usr/bin/env python3
"""Fail-closed resilience check for Anthares-browser and Anthares Remote.

Active architecture after Cloudflare quota exhaustion:
- Anthares-browser: persistent primary browser plus an optional persistent reserve.
- Anthares Remote: private GitHub/GitLab issue queues; no Render/Cloudflare runtime.
- GitHub Actions: finite-job watchdog/executor only, never a persistent browser.

An on-demand browser or finite CI runner is not counted as equivalent persistent
browser continuity. This script deliberately reports that gap instead of masking it.
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
QUEUE_PROVIDER = os.environ.get("ANTHARES_REMOTE_QUEUE_PROVIDER", "github-private-issues").strip()
QUEUE_E2E_PROVEN = os.environ.get("ANTHARES_REMOTE_QUEUE_E2E_PROVEN", "0") == "1"


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
        req = urllib.request.Request(url, headers={"User-Agent": "AntharesResilience/2.0"})
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
        return [Probe(f"{prefix}_liveness", "", False, None, 0, "disabled"), Probe(f"{prefix}_readiness", "", False, None, 0, "disabled")]
    return [probe(f"{prefix}_liveness", f"{origin}/health"), probe(f"{prefix}_readiness", f"{origin}/ready")]


def main() -> int:
    checks = browser_pair("browser_primary", BROWSER_PRIMARY) + browser_pair("browser_reserve", BROWSER_RESERVE)
    by_name = {item.name: item for item in checks}
    primary_ok = bool(BROWSER_PRIMARY) and by_name["browser_primary_liveness"].ok and by_name["browser_primary_readiness"].ok
    reserve_ok = bool(BROWSER_RESERVE) and by_name["browser_reserve_liveness"].ok and by_name["browser_reserve_readiness"].ok

    if primary_ok:
        browser_route = "primary"
    elif reserve_ok:
        browser_route = "persistent-reserve"
    else:
        browser_route = "none-equivalent"

    queue_transport_ok = QUEUE_E2E_PROVEN and QUEUE_PROVIDER in {"github-private-issues", "gitlab-private-issues", "github+gitlab-private-issues"}
    continuity_ok = (primary_ok or reserve_ok) and queue_transport_ok

    result = {
        "ok": continuity_ok,
        "continuity_ok": continuity_ok,
        "architecture": {
            "layer_1": "AUTOCURA",
            "layer_2": "CONTINUIDADE",
            "single_writer_required": True,
            "pc_as_ci_runner": False,
            "paid_services_allowed": False,
            "render_required_for_remote": False,
            "cloudflare_required": False,
            "github_actions_role": "finite_jobs_only",
        },
        "remote_control": {
            "route": QUEUE_PROVIDER,
            "e2e_proven": QUEUE_E2E_PROVEN,
            "render_required": False,
            "cloudflare_required": False,
        },
        "decision": {
            "browser_route": browser_route,
            "browser_primary_ok": primary_ok,
            "browser_persistent_reserve_ok": reserve_ok,
            "browser_equivalent_continuity": primary_ok or reserve_ok,
            "browser_redundancy_complete": primary_ok and reserve_ok,
            "degraded": not continuity_ok or not (primary_ok and reserve_ok),
        },
        "checks": [asdict(item) for item in checks],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if continuity_ok else 2


if __name__ == "__main__":
    sys.exit(main())
