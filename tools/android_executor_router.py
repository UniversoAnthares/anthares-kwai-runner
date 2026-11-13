#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci-hub" / "executor-routing.json"

DEVICE_FAILURES = {"device", "transport", "adb", "timeout", "offline", "boot", "ui"}
NON_DEVICE_FAILURES = {"content", "policy", "platform"}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8-sig"))


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
    if state.get("disabled") is True or state.get("busy") is True or state.get("online") is False:
        return False
    if state.get("healthy") is not True or state.get("ready") is not True:
        return False
    if workload == "kwai_publish" and state.get("authenticated") is False:
        return False
    return _queue_ok(state, limit)



def _verified_cloud_cutover(cfg, state):
    """Require an explicit repository cutover plus the dual-account proofs.

    Runtime-supplied JSON can report readiness; it cannot authorize cutover.
    The repository configuration is the separate, default-off authority.
    """
    guard = cfg.get("cloud_cutover", {})
    if not isinstance(guard, dict) or guard.get("enabled") is not True:
        return False
    if not isinstance(state, dict):
        return False
    if (state.get("online") is not True or
            state.get("authenticated") is not True or
            state.get("healthy") is not True or
            state.get("ready") is not True):
        return False
    observed = state.get("observed_at_epoch")
    if isinstance(observed, bool) or not isinstance(observed, (int, float)):
        return False
    age = time.time() - float(observed)
    max_age = guard.get("max_heartbeat_age_seconds", 120)
    if (not isinstance(max_age, int) or max_age < 1 or max_age > 300 or
            not 0 <= age <= max_age):
        return False
    required = guard.get("required_proofs", [])
    accounts = guard.get("required_accounts", [])
    proof = state.get("proofs")
    checked = state.get("verified_accounts")
    if (not isinstance(required, list) or not required or
            not isinstance(accounts, list) or len(accounts) != 2 or
            not isinstance(proof, dict) or not isinstance(checked, list) or
            not all(isinstance(a, str) for a in checked) or
            len(set(checked)) != len(checked) or
            set(checked) != set(accounts)):
        return False
    return all(isinstance(key, str) and proof.get(key) is True for key in required)


def _primary_allows_memufailover(manifest, state):
    cfg = manifest["android_execution"]
    primary_name = cfg.get("primary_device", "physical_android")
    primary = state.get(primary_name)
    if not isinstance(primary, dict):
        return True

    # Fail over immediately on confirmed screen sleep; ADB connection is insufficient.
    if primary.get("ui_awake") is False:
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
        # Runtime status alone must never authorize the new cloud publisher.
        if provider == "cloud_android_verified" and not _verified_cloud_cutover(cfg, s):
            continue
        # After the cutover, never silently fall back to PC/physical Android.
        cutover = cfg.get("cloud_cutover", {})
        if (cutover.get("enabled") is True and
                cutover.get("disable_local_executors") is True and
                provider in {"physical_android", "memu_android"}):
            continue
        # A connected Android can still be unusable for publication when its UI
        # is asleep or uiautomator fails. Avoid reselecting it after a verified
        # string of pre-publication device failures.
        if workload == "kwai_publish" and provider == cfg.get("primary_device", "physical_android"):
            if isinstance(s, dict):
                failure_class = str(s.get("last_failure_class", "")).strip().lower()
                try:
                    failures = int(s.get("consecutive_failures", 0) or 0)
                except (ValueError, TypeError):
                    failures = 0
                threshold = int(cfg.get("failover", {}).get("failure_threshold", 3))
                if failure_class in DEVICE_FAILURES and (s.get("degraded") is True or failures >= threshold):
                    continue
        if provider == cfg.get("fallback_device", "memu_android"):
            if not _primary_allows_memufailover(manifest, state):
                continue
        if _provider_usable(provider, meta, s, workload, limit):
            return provider
    return None


def selection_reason(manifest, state, selected):
    cfg = manifest["android_execution"]
    if selected == "cloud_android_verified":
        return "verified_cloud_cutover"
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
