"""Unattended Anthares worker preflight.

This module deliberately does not publish by itself. It verifies the conditions an
unattended publisher must satisfy and emits machine-readable readiness without ever
printing session contents.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from recovery import choose_executor
from session_capsule import decode_capsule


def readiness(*, session_value: str | None, executors: list[dict]) -> dict:
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executor": None,
        "session": "blocked",
        "ready": False,
        "blockers": [],
    }
    try:
        state["executor"] = choose_executor(executors)
    except RuntimeError as exc:
        state["blockers"].append(str(exc))

    try:
        capsule = decode_capsule(session_value)
        state["session"] = "verified"
        state["session_domain"] = capsule["domain"]
        state["session_expires_at"] = capsule["expires_at"]
    except RuntimeError as exc:
        state["blockers"].append(str(exc))

    state["ready"] = bool(state["executor"] and state["session"] == "verified")
    return state


def main() -> int:
    candidates = [
        {
            "name": os.environ.get("ANTHARES_EXECUTOR_NAME", "github-hosted"),
            "priority": 10,
            "healthy": os.environ.get("ANTHARES_EXECUTOR_HEALTHY", "1") == "1",
        }
    ]
    state = readiness(
        session_value=os.environ.get("ANTHARES_SESSION_B64"),
        executors=candidates,
    )
    output = os.environ.get("ANTHARES_READINESS_OUTPUT", "anthares-readiness.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    print(json.dumps({
        "ready": state["ready"],
        "executor": state["executor"],
        "session": state["session"],
        "blockers": state["blockers"],
    }, ensure_ascii=False))
    return 0 if state["ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
