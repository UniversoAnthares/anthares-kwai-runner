#!/usr/bin/env python3
"""Fail-closed Kwai Android executor with physical-primary/MEmu-standby routing.

This worker does not claim work. It accepts exactly one already-leased job through
KWAI_* environment variables, so the central queue/ledger remains authoritative.
It may switch from the physical device to MEmu only before an irreversible publish
request and only for executor/device failures.

The irreversible boundary is fenced by two externally configured queue callbacks:
ANTHARES_QUEUE_STARTED_COMMAND_JSON and ANTHARES_QUEUE_COMPLETE_COMMAND_JSON.
Each value must be a JSON argv array. No shell is used. Publication is impossible
unless the STARTED callback succeeds. After a verified publication, the job is
persisted locally as published_pending_ack before COMPLETE is attempted; a retry
will only retry COMPLETE and will never publish the same job again.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import android_executor_router as routing
from android_device_adapters import AndroidExecutorRouter

STATE_PATH = pathlib.Path(os.getenv("ANTHARES_ANDROID_HEALTH_STATE", str(ROOT / ".state" / "android-device-health.json")))
ACK_PATH = pathlib.Path(os.getenv("ANTHARES_ANDROID_ACK_STATE", str(ROOT / ".state" / "android-publish-ack.json")))
PHYSICAL_SAFE = ROOT / "kwai-up" / "kwai_up_safe.py"

DEVICE_PATTERNS = re.compile(
    r"(?:\badb\b|device offline|no devices?|transport|uiautomator|profile-tab-missing|"
    r"activity.*missing|control.*missing|not installed|package.*missing|timeout|timed out|"
    r"connection.*closed|broken pipe)", re.I
)
NON_FAILOVER_PATTERNS = re.compile(
    r"(?:policy|privacy|copyright|content|human-verification|captcha|verification|required|"
    r"auth-required|identity-unverified|account|ban|suspend|rate.?limit)", re.I
)
UNCERTAIN_PATTERNS = re.compile(
    r"(?:UNCERTAIN|PUBLISH_REQUESTED|COMMITTING|READY.*commit|post-request|publish.*clicked)", re.I
)


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name}-missing")
    return value


def load_json_file(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_json_file(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_health() -> dict:
    return load_json_file(STATE_PATH)


def save_health(value: dict) -> None:
    save_json_file(STATE_PATH, value)


def load_ack_state() -> dict:
    return load_json_file(ACK_PATH)


def save_ack_state(value: dict) -> None:
    save_json_file(ACK_PATH, value)


def merge_health(probes: dict, history: dict) -> dict:
    out = {}
    for key, probe in probes.items():
        row = dict(probe)
        old = history.get(key, {}) if isinstance(history.get(key), dict) else {}
        row["consecutive_failures"] = int(old.get("consecutive_failures", 0) or 0)
        row["last_failure_class"] = str(old.get("last_failure_class", "") or "")
        row["degraded"] = bool(old.get("degraded", False))
        out[key] = row
    return out


def record_result(history: dict, executor: str, success: bool, failure_class: str = "", detail: str = "") -> dict:
    row = history.setdefault(executor, {})
    if success:
        row.update({"consecutive_failures": 0, "last_failure_class": "", "degraded": False})
        row["last_success_at"] = int(time.time())
    else:
        count = int(row.get("consecutive_failures", 0) or 0) + 1
        row.update({"consecutive_failures": count, "last_failure_class": failure_class})
        if failure_class in routing.DEVICE_FAILURES and count >= 3:
            row["degraded"] = True
        row["last_failure_at"] = int(time.time())
        row["last_error"] = detail[-1200:]
    save_health(history)
    return history


def classify_failure(text: str, rc: int) -> str:
    if UNCERTAIN_PATTERNS.search(text):
        return "uncertain"
    if NON_FAILOVER_PATTERNS.search(text):
        return "platform"
    if DEVICE_PATTERNS.search(text) or rc in {70, 71, 72, 75, 79}:
        return "device"
    return "platform"


def download_media(url: str) -> pathlib.Path:
    target_dir = pathlib.Path(tempfile.mkdtemp(prefix="anthares-kwai-device-"))
    target = target_dir / "upload.mp4"
    req = urllib.request.Request(url, headers={"User-Agent": "AntharesDeviceFailover/1.0"})
    with urllib.request.urlopen(req, timeout=90) as src, target.open("wb") as dst:
        while True:
            block = src.read(1024 * 1024)
            if not block:
                break
            dst.write(block)
    if target.stat().st_size < 1024:
        raise RuntimeError("media-download-invalid")
    return target


def source_ms(name: str) -> int:
    raw = required(name)
    try:
        return int(round(float(raw) * 1000.0))
    except ValueError as exc:
        raise RuntimeError(f"{name}-invalid") from exc


def physical_env(media: pathlib.Path) -> dict:
    env = os.environ.copy()
    serial = required("ANTHARES_PHYSICAL_ADB_SERIAL")
    env.update({
        "KWAI_UP_JOB_ID": required("KWAI_QUEUE_JOB_ID"),
        "KWAI_UP_SOURCE_ID": required("KWAI_SOURCE_ID"),
        "KWAI_UP_START_MS": str(source_ms("KWAI_SOURCE_START")),
        "KWAI_UP_END_MS": str(source_ms("KWAI_SOURCE_END")),
        "KWAI_UP_MEDIA": str(media),
        "KWAI_UP_ADB_SERIAL": serial,
        "KWAI_UP_PACKAGE": os.getenv("ANTHARES_PHYSICAL_KWAI_PACKAGE", "kwai.lite.video"),
        "KWAI_UP_EXPECTED_ACCOUNT": os.getenv("KWAI_EXPECTED_ACCOUNT", "lucasrosalem"),
        "KWAI_UP_CAPTION": os.getenv("KWAI_VIDEO_TITLE", ""),
    })
    adb = os.getenv("ANTHARES_ADB", "").strip()
    if adb:
        env["PATH"] = str(pathlib.Path(adb).parent) + os.pathsep + env.get("PATH", "")
    return env


def run_process(args: list[str], env: dict, timeout: int = 420) -> tuple[int, str]:
    p = subprocess.run(args, cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
    out = p.stdout or ""
    if out:
        print(out, end="" if out.endswith("\n") else "\n", flush=True)
    return p.returncode, out


def callback_argv(kind: str) -> list[str]:
    name = f"ANTHARES_QUEUE_{kind.upper()}_COMMAND_JSON"
    raw = required(name)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name}-invalid-json") from exc
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise RuntimeError(f"{name}-must-be-json-argv")
    return value


def queue_callback(kind: str, executor: str) -> tuple[bool, str]:
    env = os.environ.copy()
    env["ANTHARES_SELECTED_EXECUTOR"] = executor
    env["ANTHARES_QUEUE_CALLBACK_KIND"] = kind
    try:
        rc, out = run_process(callback_argv(kind), env, timeout=60)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    return rc == 0, out


def mark_pending_ack(job_id: str, executor: str) -> None:
    state = load_ack_state()
    state[job_id] = {
        "state": "published_pending_ack",
        "executor": executor,
        "published_at": int(time.time()),
    }
    save_ack_state(state)


def mark_acknowledged(job_id: str) -> None:
    state = load_ack_state()
    row = state.setdefault(job_id, {})
    row["state"] = "completed_acknowledged"
    row["acknowledged_at"] = int(time.time())
    save_ack_state(state)


def retry_pending_ack(job_id: str) -> int | None:
    state = load_ack_state()
    row = state.get(job_id)
    if not isinstance(row, dict) or row.get("state") != "published_pending_ack":
        return None
    executor = str(row.get("executor") or "unknown")
    print(f"KWAI_DEVICE_STATE=PUBLISHED_PENDING_ACK EXECUTOR={executor}", flush=True)
    ok, detail = queue_callback("complete", executor)
    if ok:
        mark_acknowledged(job_id)
        print(f"KWAI_DEVICE_STATE=VERIFIED_ACK_REPAIRED EXECUTOR={executor}", flush=True)
        return 0
    print("KWAI_DEVICE_STATE=PUBLISHED_PENDING_ACK COMPLETE_CALLBACK_FAILED", flush=True)
    if detail:
        print(detail[-1200:], flush=True)
    return 91


def run_physical_prepare(media: pathlib.Path) -> tuple[bool, str, str, dict]:
    env = physical_env(media)
    rc, out = run_process([sys.executable, str(PHYSICAL_SAFE), "prepare"], env)
    if rc != 0 or "KWAI_UP_STATE=READY_TO_PUBLISH" not in out:
        return False, classify_failure(out, rc), out, env
    return True, "", out, env


def run_physical_commit(env: dict, prepare_out: str) -> tuple[bool, str, str]:
    rc, commit_out = run_process([sys.executable, str(PHYSICAL_SAFE), "commit"], env)
    combined = prepare_out + "\n" + commit_out
    if rc != 0 or "KWAI_UP_STATE=VERIFIED" not in commit_out:
        return False, "uncertain", combined
    return True, "", combined


def memu_publisher() -> pathlib.Path:
    raw = os.getenv("ANTHARES_MEMU_PUBLISHER_PATH", "").strip()
    if raw:
        return pathlib.Path(raw)
    return pathlib.Path(r"C:\Users\Lucas\anthares-clipper\fallback\memu\kwai_memu_publish.py")


def run_memu(media: pathlib.Path) -> tuple[bool, str, str]:
    publisher = memu_publisher()
    if not publisher.is_file():
        return False, "offline", f"MEmu publisher missing: {publisher}"
    env = os.environ.copy()
    env.update({
        "ATD_PUBLISH_MODE": "publish-local",
        "ATD_KWAI_MEDIA": str(media),
        "ATD_KWAI_CAPTION": os.getenv("KWAI_VIDEO_TITLE", ""),
    })
    if os.getenv("ANTHARES_MEMU_VM", "").strip():
        env["ATD_KWAI_VM"] = os.environ["ANTHARES_MEMU_VM"].strip()
    rc, out = run_process([sys.executable, str(publisher)], env, timeout=480)
    if rc == 0 and "KWAI_MEMU_PUBLISH=OK" in out:
        return True, "", out
    if re.search(r"toque em Publicar|publicação confirmada|após o toque|KWAI_MEMU_PUBLISH", out, re.I):
        return False, "uncertain", out
    return False, classify_failure(out, rc), out


def finalize_verified_publish(job_id: str, executor: str) -> int:
    mark_pending_ack(job_id, executor)
    ok, detail = queue_callback("complete", executor)
    if ok:
        mark_acknowledged(job_id)
        print(f"KWAI_DEVICE_STATE=VERIFIED EXECUTOR={executor}", flush=True)
        return 0
    print(f"KWAI_DEVICE_STATE=PUBLISHED_PENDING_ACK EXECUTOR={executor}", flush=True)
    if detail:
        print(detail[-1200:], flush=True)
    return 91


def main() -> int:
    job_id = required("KWAI_QUEUE_JOB_ID")
    repaired = retry_pending_ack(job_id)
    if repaired is not None:
        return repaired

    url = required("KWAI_VIDEO_URL")
    history = load_health()
    probes = AndroidExecutorRouter().status()
    state = merge_health(probes, history)
    manifest = routing.load_manifest()
    selected = routing.choose(manifest, state, workload="kwai_publish")
    print("KWAI_DEVICE_ROUTER_SELECTED=" + (selected or "NONE"), flush=True)
    if not selected:
        print("KWAI_DEVICE_STATE=QUEUED_NO_EXECUTOR", flush=True)
        return 75

    media = download_media(url)
    try:
        physical_env_data = None
        prepare_out = ""
        if selected == "physical_android":
            prepared, failure_class, detail, physical_env_data = run_physical_prepare(media)
            if not prepared:
                history = record_result(history, "physical_android", False, failure_class, detail)
                if failure_class == "uncertain":
                    print("KWAI_DEVICE_STATE=UNCERTAIN EXECUTOR=physical_android", flush=True)
                    return 90
                if failure_class not in routing.DEVICE_FAILURES:
                    print(f"KWAI_DEVICE_STATE=FAILED_NO_FAILOVER CLASS={failure_class}", flush=True)
                    return 80
                probes2 = AndroidExecutorRouter().status()
                state2 = merge_health(probes2, history)
                selected2 = routing.choose(manifest, state2, workload="kwai_publish")
                if selected2 != "memu_android":
                    print("KWAI_DEVICE_STATE=PHYSICAL_FAILED_MEMU_NOT_ELIGIBLE", flush=True)
                    return 81
                selected = selected2
            else:
                prepare_out = detail

        # Central STARTED is the fence immediately before any irreversible action.
        started, started_detail = queue_callback("started", selected)
        if not started:
            print(f"KWAI_DEVICE_STATE=START_FENCE_FAILED EXECUTOR={selected}", flush=True)
            if started_detail:
                print(started_detail[-1200:], flush=True)
            return 84

        if selected == "physical_android":
            ok, failure_class, detail = run_physical_commit(physical_env_data, prepare_out)
            history = record_result(history, "physical_android", ok, failure_class, detail)
            if not ok:
                print("KWAI_DEVICE_STATE=UNCERTAIN EXECUTOR=physical_android", flush=True)
                return 90
            return finalize_verified_publish(job_id, "physical_android")

        if selected == "memu_android":
            ok, failure_class, detail = run_memu(media)
            record_result(history, "memu_android", ok, failure_class, detail)
            if ok:
                rc = finalize_verified_publish(job_id, "memu_android")
                if rc == 0:
                    print("KWAI_DEVICE_FAILOVER=1", flush=True)
                return rc
            if failure_class == "uncertain":
                print("KWAI_DEVICE_STATE=UNCERTAIN EXECUTOR=memu_android", flush=True)
                return 90
            print(f"KWAI_DEVICE_STATE=FAILED EXECUTOR=memu_android CLASS={failure_class}", flush=True)
            return 82

        print(f"KWAI_DEVICE_STATE=DELEGATED_REMOTE EXECUTOR={selected}", flush=True)
        return 83
    finally:
        try:
            media.unlink(missing_ok=True)
            media.parent.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
