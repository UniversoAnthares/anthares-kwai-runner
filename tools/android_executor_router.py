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
    providers = manifest.get("providers", {})
    for provider in cfg["priority"]:
        meta = providers.get(provider, {})
        if meta.get("android_eligible") is False:
            continue
        s = state.get(provider)
        if not isinstance(s, dict):
            continue
        if s.get("disabled") is True:
            continue
        if s.get("healthy") is not True or s.get("ready") is not True:
            continue
        if int(s.get("queue_seconds", 0) or 0) > limit:
            continue
        return provider
    return None


def main():
    manifest = load_manifest()
    selected = choose(manifest, load_state())
    print("ANDROID_EXECUTOR_PRIORITY=" + ",".join(manifest["android_execution"]["priority"]))
    print("GITHUB_ACTIONS_ANDROID=" + manifest["android_execution"]["github_actions"])
    if selected:
        print("ANDROID_EXECUTOR_SELECTED=" + selected)
        return 0
    print("ANDROID_EXECUTOR_SELECTED=NONE")
    return 3


if __name__ == "__main__":
    sys.exit(main())
