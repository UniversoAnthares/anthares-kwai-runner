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
    return json.loads(raw)


def choose(manifest, state):
    cfg = manifest["android_execution"]
    limit = int(cfg["failover"]["queue_threshold_seconds"])
    for provider in cfg["priority"]:
        s = state.get(provider, {})
        if s.get("disabled") is True:
            continue
        if s.get("healthy") is False:
            continue
        if s.get("ready") is False:
            continue
        queued = int(s.get("queue_seconds", 0) or 0)
        if queued > limit:
            continue
        return provider
    return None


def main():
    manifest = load_manifest()
    state = load_state()
    selected = choose(manifest, state)
    print("ANDROID_EXECUTOR_PRIORITY=" + ",".join(manifest["android_execution"]["priority"]))
    print("GITHUB_ACTIONS_ANDROID=" + manifest["android_execution"]["github_actions"])
    if selected:
        print("ANDROID_EXECUTOR_SELECTED=" + selected)
        return 0
    print("ANDROID_EXECUTOR_SELECTED=NONE")
    return 3


if __name__ == "__main__":
    sys.exit(main())
