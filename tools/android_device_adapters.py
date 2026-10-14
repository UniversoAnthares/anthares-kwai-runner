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

KWAI_PACKAGE = os.environ.get("KWAI_ANDROID_PACKAGE", "com.kwai.video")


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
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class AdbDeviceAdapter:
    executor_id = "android"

    def __init__(self, serial: str, *, adb: str = "adb", run: Callable = subprocess.run):
        self.serial = (serial or "").strip()
        self.adb = adb
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

        package = self._adb("shell", "pm", "path", KWAI_PACKAGE)
        installed = package.returncode == 0 and "package:" in package.stdout
        if not installed:
            return ExecutorStatus(
                executor_id=self.executor_id,
                online=True,
                healthy=True,
                ready=False,
                authenticated=False,
                adb_serial=self.serial,
                last_failure_class="device",
                detail=f"{KWAI_PACKAGE} not installed",
            )

        # Authentication is intentionally fail-closed. A worker may set the explicit
        # per-device readiness bit only after its own Kwai identity/session probe.
        auth_env = os.environ.get(self.auth_env_name(), "").strip().lower()
        authenticated = auth_env in {"1", "true", "yes", "ready"}
        return ExecutorStatus(
            executor_id=self.executor_id,
            online=True,
            healthy=True,
            ready=authenticated,
            authenticated=authenticated,
            adb_serial=self.serial,
            detail="adb and Kwai package ready" if authenticated else "Kwai session not proven ready",
        )

    def auth_env_name(self) -> str:
        return "ANTHARES_ANDROID_AUTHENTICATED"


class PhysicalDeviceAdapter(AdbDeviceAdapter):
    executor_id = "physical_android"

    @classmethod
    def from_env(cls) -> "PhysicalDeviceAdapter":
        return cls(os.environ.get("ANTHARES_PHYSICAL_ADB_SERIAL", ""))

    def auth_env_name(self) -> str:
        return "ANTHARES_PHYSICAL_KWAI_AUTHENTICATED"


class MEmuAdapter(AdbDeviceAdapter):
    executor_id = "memu_android"

    @classmethod
    def from_env(cls) -> "MEmuAdapter":
        # MEmu commonly exposes a local ADB endpoint, but no port is guessed here.
        # The real serial must be supplied by deployment/configuration.
        return cls(os.environ.get("ANTHARES_MEMU_ADB_SERIAL", ""))

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
