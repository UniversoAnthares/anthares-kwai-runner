#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci-hub" / "executor-routing.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_state():
    raw = os.environ.get("ANTHARES_EXECUTOR_STATUS_JSON", "{}").strip() or "{}"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def choose(manifest, state, workload="manual_auth"):
    cfg = manifest["android_execution"]
    limit = int(cfg["failover"]["queue_threshold_seconds"])
    providers = manifest.get("providers", {})
    for provider in cfg["priority"]:
        meta = providers.get(provider, {})
        if meta.get("android_eligible") is False or meta.get("active") is False:
            continue
        if workload == "manual_auth" and meta.get("interactive_manual_auth") is False:
            continue
        s = state.get(provider)
        if not isinstance(s, dict):
            continue
        if s.get("disabled") is True:
            continue
        if s.get("healthy") is not True or s.get("ready") is not True:
            continue
        try:
            queue_seconds = int(s.get("queue_seconds", 0) or 0)
        except (TypeError, ValueError):
            continue
        if queue_seconds < 0 or queue_seconds > limit:
            continue
        return provider
    return None


def main():
    manifest = load_manifest()
    workload = os.environ.get("ANTHARES_EXECUTOR_WORKLOAD", "manual_auth").strip()
    if workload not in {"generic_android", "manual_auth"}:
        print("ANDROID_EXECUTOR_WORKLOAD=INVALID")
        return 2
    selected = choose(manifest, load_state(), workload=workload)
    print("ANDROID_EXECUTOR_PRIORITY=" + ",".join(manifest["android_execution"]["priority"]))
    print("ANDROID_EXECUTOR_WORKLOAD=" + workload)
    print("ANDROID_EXECUTOR_SELECTION_ONLY=1")
    print("ANDROID_EXECUTOR_DISPATCHED=0")
    print("GITHUB_ACTIONS_ANDROID=" + manifest["android_execution"]["github_actions"])
    if selected:
        print("ANDROID_EXECUTOR_SELECTED=" + selected)
        return 0
    print("ANDROID_EXECUTOR_SELECTED=NONE")
    return 3


if __name__ == "__main__":
    sys.exit(main())
