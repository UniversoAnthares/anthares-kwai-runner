#!/usr/bin/env python3
"""Android device adapters used by the executor router.

Physical Android is always the primary device. MEmu is a warm standby only and is
never promoted unless the router explicitly selected it after physical-device
unavailability/degradation.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from typing import Callable, Optional


@dataclass
class ExecutorStatus:
    executor_id: str
    online: bool
    healthy: bool
    ready: bool
    authenticated: bool
    busy: bool = False
    queue_seconds: int = 0
    degraded: bool = False
    consecutive_failures: int = 0
    last_failure_class: str = ""
    adb_serial: str = ""
    boot_completed: bool = False
    package_installed: bool = False
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class AdbDeviceAdapter:
    executor_id = "android"
    default_package = "com.kwai.video"

    def __init__(self, serial: str, *, adb: str = "adb", package: str | None = None, run: Callable = subprocess.run):
        self.serial = (serial or "").strip()
        self.adb = adb
        self.package = (package or self.default_package).strip()
        self._run = run

    def _adb(self, *args: str, timeout: int = 15) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return self._run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

    def probe(self) -> ExecutorStatus:
        if not self.serial:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=False,
                healthy=False,
                ready=False,
                authenticated=False,
                adb_serial="",
                last_failure_class="offline",
                detail="adb serial not configured",
            )

        try:
            state = self._adb("get-state")
        except (OSError, subprocess.SubprocessError) as exc:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=False,
                healthy=False,
                ready=False,
                authenticated=False,
                adb_serial=self.serial,
                last_failure_class="transport",
                detail=str(exc),
            )

        online = state.returncode == 0 and state.stdout.strip() == "device"
        if not online:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=False,
                healthy=False,
                ready=False,
                authenticated=False,
                adb_serial=self.serial,
                last_failure_class="offline",
                detail=(state.stderr or state.stdout).strip(),
            )

        boot = self._adb("shell", "getprop", "sys.boot_completed")
        boot_completed = boot.returncode == 0 and boot.stdout.strip() == "1"
        if not boot_completed:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=True,
                healthy=False,
                ready=False,
                authenticated=False,
                adb_serial=self.serial,
                boot_completed=False,
                last_failure_class="boot",
                detail="android boot not completed",
            )

        package = self._adb("shell", "pm", "path", self.package)
        installed = package.returncode == 0 and "package:" in package.stdout
        if not installed:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=True,
                healthy=False,
                ready=False,
                authenticated=False,
                adb_serial=self.serial,
                boot_completed=True,
                package_installed=False,
                last_failure_class="device",
                detail=f"{self.package} not installed",
            )

        auth_env = os.environ.get(self.auth_env_name(), "").strip().lower()
        authenticated = auth_env in {"1", "true", "yes", "ready"}
        return ExecutorStatus(
            executor_id=self.executor_id,
            online=True,
            healthy=True,
            ready=authenticated,
            authenticated=authenticated,
            adb_serial=self.serial,
            boot_completed=True,
            package_installed=True,
            detail=(
                f"adb, boot and {self.package} ready"
                if authenticated
                else "device healthy; Kwai session not proven ready"
            ),
        )

    def auth_env_name(self) -> str:
        return "ANTHARES_ANDROID_AUTHENTICATED"


class PhysicalDeviceAdapter(AdbDeviceAdapter):
    executor_id = "physical_android"
    default_package = "kwai.lite.video"

    @classmethod
    def from_env(cls) -> "PhysicalDeviceAdapter":
        return cls(
            os.environ.get("ANTHARES_PHYSICAL_ADB_SERIAL", ""),
            adb=os.environ.get("ANTHARES_ADB", "adb"),
            package=os.environ.get("ANTHARES_PHYSICAL_KWAI_PACKAGE", cls.default_package),
        )

    def auth_env_name(self) -> str:
        return "ANTHARES_PHYSICAL_KWAI_AUTHENTICATED"


class MEmuAdapter(AdbDeviceAdapter):
    executor_id = "memu_android"
    default_package = "com.kwai.video"

    @classmethod
    def from_env(cls) -> "MEmuAdapter":
        return cls(
            os.environ.get("ANTHARES_MEMU_ADB_SERIAL", ""),
            adb=os.environ.get("ANTHARES_ADB", "adb"),
            package=os.environ.get("ANTHARES_MEMU_KWAI_PACKAGE", cls.default_package),
        )

    def auth_env_name(self) -> str:
        return "ANTHARES_MEMU_KWAI_AUTHENTICATED"


class AndroidExecutorRouter:
    """Build status for the central router without dispatching or leasing a job."""

    def __init__(self, physical: Optional[PhysicalDeviceAdapter] = None, memu: Optional[MEmuAdapter] = None):
        self.physical = physical or PhysicalDeviceAdapter.from_env()
        self.memu = memu or MEmuAdapter.from_env()

    def status(self) -> dict:
        return {
            self.physical.executor_id: self.physical.probe().to_dict(),
            self.memu.executor_id: self.memu.probe().to_dict(),
        }

    def status_json(self) -> str:
        return json.dumps(self.status(), separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    print(AndroidExecutorRouter().status_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
