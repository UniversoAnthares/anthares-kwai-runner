#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci-hub" / "executor-routing.json"

DEVICE_FAILURES = {"device", "transport", "adb", "timeout", "offline", "boot", "ui"}
NON_DEVICE_FAILURES = {"content", "policy", "platform"}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_state():
    raw = os.environ.get("ANTHARES_EXECUTOR_STATUS_JSON", "{}").strip() or "{}"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _queue_ok(state, limit):
    try:
        queue_seconds = int(state.get("queue_seconds", 0) or 0)
    except (TypeError, ValueError):
        return False
    return 0 <= queue_seconds <= limit


def _provider_usable(provider, meta, state, workload, limit):
    if meta.get("android_eligible") is False or meta.get("active") is False:
        return False
    if workload == "manual_auth" and meta.get("interactive_manual_auth") is False:
        return False
    if not isinstance(state, dict):
        return False
    if state.get("disabled") is True or state.get("busy") is True:
        return False
    if state.get("healthy") is not True or state.get("ready") is not True:
        return False
    if workload == "kwai_publish" and state.get("authenticated") is False:
        return False
    return _queue_ok(state, limit)


def _primary_allows_memufailover(manifest, state):
    cfg = manifest["android_execution"]
    primary_name = cfg.get("primary_device", "physical_android")
    primary = state.get(primary_name)
    if not isinstance(primary, dict):
        return True

    failure_class = str(primary.get("last_failure_class", "")).strip().lower()
    if failure_class in NON_DEVICE_FAILURES:
        return False

    # Explicitly offline/unavailable primary is an immediate failover condition.
    if primary.get("disabled") is True or primary.get("online") is False:
        return True
    if primary.get("ready") is False and primary.get("healthy") is False and not failure_class:
        return True

    # Device/ADB/UI failures open the circuit only after the configured threshold.
    if failure_class in DEVICE_FAILURES:
        threshold = int(cfg.get("failover", {}).get("failure_threshold", 3))
        try:
            failures = int(primary.get("consecutive_failures", 0) or 0)
        except (TypeError, ValueError):
            return False
        return primary.get("degraded") is True or failures >= threshold

    return primary.get("degraded") is True


def choose(manifest, state, workload="manual_auth"):
    cfg = manifest["android_execution"]
    limit = int(cfg["failover"]["queue_threshold_seconds"])
    providers = manifest.get("providers", {})
    for provider in cfg["priority"]:
        meta = providers.get(provider, {})
        s = state.get(provider)
        if provider == cfg.get("fallback_device", "memu_android"):
            if not _primary_allows_memufailover(manifest, state):
                continue
        if _provider_usable(provider, meta, s, workload, limit):
            return provider
    return None


def selection_reason(manifest, state, selected):
    cfg = manifest["android_execution"]
    if selected == cfg.get("primary_device"):
        return "primary_physical_device"
    if selected == cfg.get("fallback_device"):
        return "physical_unavailable_or_degraded"
    if selected:
        return "secondary_remote_executor"
    return "no_healthy_executor"


def main():
    manifest = load_manifest()
    workload = os.environ.get("ANTHARES_EXECUTOR_WORKLOAD", "manual_auth").strip()
    if workload not in {"generic_android", "manual_auth", "kwai_publish"}:
        print("ANDROID_EXECUTOR_WORKLOAD=INVALID")
        return 2
    state = load_state()
    selected = choose(manifest, state, workload=workload)
    print("ANDROID_EXECUTOR_PRIORITY=" + ",".join(manifest["android_execution"]["priority"]))
    print("ANDROID_EXECUTOR_WORKLOAD=" + workload)
    print("ANDROID_EXECUTOR_SELECTION_ONLY=1")
    print("ANDROID_EXECUTOR_DISPATCHED=0")
    print("ANDROID_EXECUTOR_PRIMARY=" + manifest["android_execution"].get("primary_device", ""))
    print("ANDROID_EXECUTOR_FALLBACK=" + manifest["android_execution"].get("fallback_device", ""))
    print("GITHUB_ACTIONS_ANDROID=" + manifest["android_execution"]["github_actions"])
    if selected:
        print("ANDROID_EXECUTOR_SELECTED=" + selected)
        print("ANDROID_EXECUTOR_REASON=" + selection_reason(manifest, state, selected))
        return 0
    print("ANDROID_EXECUTOR_SELECTED=NONE")
    print("ANDROID_EXECUTOR_REASON=no_healthy_executor")
    return 3


if __name__ == "__main__":
    sys.exit(main())
