from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

PROGRAM_DATA = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "AntharesAndroidRuntime"
STATE_FILE = PROGRAM_DATA / "state.json"
EVENTS_FILE = PROGRAM_DATA / "events.jsonl"


class BackendState(str, Enum):
    UNKNOWN = "UNKNOWN"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    RUNNING_TRANSPORT_OFFLINE = "RUNNING_TRANSPORT_OFFLINE"
    ANDROID_BOOTING = "ANDROID_BOOTING"
    ANDROID_READY = "ANDROID_READY"
    APP_MISSING = "APP_MISSING"
    APP_STOPPED = "APP_STOPPED"
    APP_FOREGROUND = "APP_FOREGROUND"
    AUTH_UNKNOWN = "AUTH_UNKNOWN"
    AUTH_VALID = "AUTH_VALID"
    AUTH_INVALID = "AUTH_INVALID"
    DEGRADED = "DEGRADED"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"


@dataclass
class CommandResult:
    code: int
    stdout: str
    stderr: str
    duration_ms: int


@dataclass
class BackendSnapshot:
    backend: str
    process_running: bool
    vm_registered: bool
    vm_inaccessible: bool
    serial: Optional[str]
    transport_state: str
    android_boot_completed: bool
    state: str
    health_score: int
    kwai_package: Optional[str] = None
    foreground: Optional[str] = None


def run(cmd: list[str], timeout: float = 8.0) -> CommandResult:
    started = time.monotonic()
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return CommandResult(cp.returncode, cp.stdout or "", cp.stderr or "", int((time.monotonic() - started) * 1000))
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(124, out, err or "timeout", int((time.monotonic() - started) * 1000))


def parse_adb_devices(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            result[parts[0]] = parts[1]
    return result


def health_score(process_running: bool, transport: str, boot: bool, screenshot_ok: bool = False, package_ok: bool = False, ui_ok: bool = False) -> int:
    score = 0
    score += 15 if process_running else 0
    score += 25 if transport == "device" else (5 if transport == "offline" else 0)
    score += 25 if boot else 0
    score += 15 if screenshot_ok else 0
    score += 10 if package_ok else 0
    score += 10 if ui_ok else 0
    return min(100, score)


class AdbTransport:
    def __init__(self, adb: Path, serial: str):
        self.adb = adb
        self.serial = serial

    def _cmd(self, *args: str, timeout: float = 8.0) -> CommandResult:
        return run([str(self.adb), *args], timeout=timeout)

    def devices(self) -> dict[str, str]:
        return parse_adb_devices(self._cmd("devices", "-l").stdout)

    def state(self) -> str:
        return self.devices().get(self.serial, "missing")

    def shell(self, *args: str, timeout: float = 8.0) -> CommandResult:
        return self._cmd("-s", self.serial, "shell", *args, timeout=timeout)

    def recover(self) -> list[dict]:
        steps: list[dict] = []
        def step(name: str, args: list[str], wait: float = 0.0) -> None:
            r = self._cmd(*args, timeout=12)
            steps.append({"step": name, "code": r.code, "stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "state": self.state()})
            if wait:
                time.sleep(wait)

        if self.state() == "device":
            return [{"step": "already_healthy", "state": "device"}]
        step("disconnect", ["disconnect", self.serial], 0.5)
        step("connect", ["connect", self.serial], 1.0)
        if self.state() == "device":
            return steps
        step("kill_server", ["kill-server"], 0.5)
        step("start_server", ["start-server"], 0.5)
        step("reconnect_after_server", ["connect", self.serial], 1.0)
        return steps

    def wait_boot(self, deadline_seconds: float = 45) -> bool:
        deadline = time.monotonic() + deadline_seconds
        while time.monotonic() < deadline:
            if self.state() == "device":
                r = self.shell("getprop", "sys.boot_completed", timeout=4)
                if r.stdout.strip() == "1":
                    return True
            time.sleep(1.0)
        return False

    def screenshot(self, destination: Path) -> bool:
        destination.parent.mkdir(parents=True, exist_ok=True)
        cp = run([str(self.adb), "-s", self.serial, "exec-out", "screencap", "-p"], timeout=12)
        if cp.code != 0:
            return False
        data = cp.stdout.encode("latin1", errors="ignore") if isinstance(cp.stdout, str) else cp.stdout
        if not data.startswith(b"\x89PNG"):
            cp2 = subprocess.run([str(self.adb), "-s", self.serial, "exec-out", "screencap", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            data = cp2.stdout
        if not data.startswith(b"\x89PNG"):
            return False
        destination.write_bytes(data)
        return True


class MEmuAdapter:
    NAME = "memu4"
    VM_NAME = "MEmu_4"
    DEFAULT_SERIAL = "127.0.0.1:21543"

    def __init__(self):
        self.root = self._discover_root()
        self.adb_path = self.root / "adb.exe"
        self.memuc_path = self.root / "memuc.exe"
        hyperv = self.root.parent / "MEmuHyperv" / "MEmuManage.exe"
        self.manage_path = hyperv if hyperv.exists() else self.root / "MEmuManage.exe"
        self.serial = self._discover_serial() or self.DEFAULT_SERIAL
        self.transport = AdbTransport(self.adb_path, self.serial)

    @staticmethod
    def _discover_root() -> Path:
        candidates = [
            Path(r"D:\Program Files\Microvirt\MEmu"),
            Path(r"C:\Program Files\Microvirt\MEmu"),
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microvirt" / "MEmu",
        ]
        for root in candidates:
            if (root / "adb.exe").exists():
                return root
        raise FileNotFoundError("MEmu adb.exe not found")

    def _discover_serial(self) -> Optional[str]:
        if not self.adb_path.exists():
            return None
        devices = parse_adb_devices(run([str(self.adb_path), "devices", "-l"]).stdout)
        local = [s for s in devices if s.startswith("127.0.0.1:")]
        if self.DEFAULT_SERIAL in local:
            return self.DEFAULT_SERIAL
        return local[0] if local else None

    def _process_running(self) -> bool:
        r = run(["tasklist", "/FI", "IMAGENAME eq MEmuHeadless.exe", "/FO", "CSV", "/NH"])
        return "MEmuHeadless.exe" in r.stdout

    def _vm_info(self) -> tuple[bool, bool]:
        if not self.manage_path.exists():
            return False, False
        r = run([str(self.manage_path), "list", "vms"], timeout=8)
        registered = f'"{self.VM_NAME}"' in r.stdout
        inaccessible = '"<inaccessible>"' in r.stdout and "000000000004" in r.stdout
        return registered, inaccessible

    def kwai_package(self) -> Optional[str]:
        if self.transport.state() != "device":
            return None
        r = self.transport.shell("pm", "list", "packages")
        packages = [line.replace("package:", "").strip() for line in r.stdout.splitlines() if line.startswith("package:")]
        for pkg in packages:
            if "kwai" in pkg.lower() or "kuaishou" in pkg.lower():
                return pkg
        return None

    def foreground(self) -> Optional[str]:
        if self.transport.state() != "device":
            return None
        r = self.transport.shell("dumpsys", "window", "windows")
        for line in r.stdout.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                return line.strip()
        return None

    def dump_ui(self) -> str:
        if self.transport.state() != "device":
            return ""
        self.transport.shell("uiautomator", "dump", "/sdcard/window.xml", timeout=12)
        return self.transport.shell("cat", "/sdcard/window.xml", timeout=8).stdout

    def identity_signal(self, expected: str = "@lucasrosalem") -> dict:
        ui = self.dump_ui()
        text_hit = expected.lower() in ui.lower()
        return {"expected": expected, "ui_exact_match": text_hit, "foreground": self.foreground(), "package": self.kwai_package(), "auth_valid": bool(text_hit)}

    def launch_kwai(self) -> dict:
        pkg = self.kwai_package()
        if not pkg:
            return {"ok": False, "error": "APP_MISSING"}
        r = self.transport.shell("monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1", timeout=12)
        time.sleep(2)
        return {"ok": r.code == 0, "package": pkg, "foreground": self.foreground()}

    def snapshot(self) -> BackendSnapshot:
        proc = self._process_running()
        registered, inaccessible = self._vm_info()
        ts = self.transport.state() if self.adb_path.exists() else "missing"
        boot = False
        if ts == "device":
            boot = self.transport.shell("getprop", "sys.boot_completed", timeout=4).stdout.strip() == "1"
        if proc and ts == "offline":
            state = BackendState.RUNNING_TRANSPORT_OFFLINE.value
        elif ts == "device" and boot:
            state = BackendState.ANDROID_READY.value
        elif proc:
            state = BackendState.RUNNING.value
        else:
            state = BackendState.STOPPED.value
        pkg = self.kwai_package() if ts == "device" else None
        fg = self.foreground() if ts == "device" else None
        return BackendSnapshot(self.NAME, proc, registered, inaccessible, self.serial, ts, boot, state, health_score(proc, ts, boot, package_ok=bool(pkg)), pkg, fg)

    def recover_transport(self) -> dict:
        before = asdict(self.snapshot())
        steps = self.transport.recover()
        boot = self.transport.wait_boot(20) if self.transport.state() == "device" else False
        after = asdict(self.snapshot())
        return {"ok": after["transport_state"] == "device" and boot, "before": before, "steps": steps, "after": after}


class RuntimeManager:
    def __init__(self):
        PROGRAM_DATA.mkdir(parents=True, exist_ok=True)
        self.adapter = MEmuAdapter()

    def persist(self, payload: dict) -> None:
        STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with EVENTS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.time(), **payload}, ensure_ascii=False) + "\n")

    def status(self) -> dict:
        out = {"ok": True, **asdict(self.adapter.snapshot())}
        self.persist({"operation": "status", "result": out})
        return out

    def recover(self) -> dict:
        out = self.adapter.recover_transport()
        self.persist({"operation": "recover_transport", "result": out})
        return out

    def identity(self) -> dict:
        out = self.adapter.identity_signal()
        self.persist({"operation": "identity_kwai", "result": out})
        return out

    def launch_kwai(self) -> dict:
        out = self.adapter.launch_kwai()
        self.persist({"operation": "launch_kwai", "result": out})
        return out


def main(argv: Optional[Iterable[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="anthares-android")
    p.add_argument("command", choices=["status", "recover", "identity", "launch-kwai", "ui-dump"])
    p.add_argument("--json", action="store_true", default=True)
    ns = p.parse_args(list(argv) if argv is not None else None)
    manager = RuntimeManager()
    if ns.command == "status":
        result = manager.status()
    elif ns.command == "recover":
        result = manager.recover()
    elif ns.command == "identity":
        result = manager.identity()
    elif ns.command == "launch-kwai":
        result = manager.launch_kwai()
    else:
        result = {"ok": manager.adapter.transport.state() == "device", "ui": manager.adapter.dump_ui()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
