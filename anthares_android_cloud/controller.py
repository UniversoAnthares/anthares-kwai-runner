"""Android controller. Uses local Android SDK tools, no third-party Python dependencies."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def sdk_tool(name: str) -> str:
    root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not root:
        raise RuntimeError("ANDROID_SDK_ROOT or ANDROID_HOME is required")
    paths = {"adb": "platform-tools/adb", "emulator": "emulator/emulator", "avdmanager": "cmdline-tools/latest/bin/avdmanager"}
    candidate = Path(root) / paths[name]
    if not candidate.is_file():
        raise FileNotFoundError(str(candidate))
    return str(candidate)


def run(args: list[str], timeout: int = 30) -> str:
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=True)
    return result.stdout.strip()


def status() -> dict[str, str | bool]:
    devices = run([sdk_tool("adb"), "devices"])
    ready = [line.split()[0] for line in devices.splitlines()[1:] if line.endswith("\tdevice")]
    if not ready:
        return {"connected": False, "booted": False}
    device = ready[0]
    boot = run([sdk_tool("adb"), "-s", device, "shell", "getprop", "sys.boot_completed"])
    return {"connected": True, "booted": boot.strip() == "1", "serial": device}


def wait_boot(timeout_seconds: int = 480) -> dict[str, str | bool]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        current = status()
        if current["booted"]:
            return current
        time.sleep(5)
    raise TimeoutError("Android did not boot within deadline")


def main() -> None:
    parser = argparse.ArgumentParser(description="Anthares Android Cloud controller")
    parser.add_argument("command", choices=["status", "wait-boot"])
    parser.add_argument("--timeout", type=int, default=480)
    args = parser.parse_args()
    result = status() if args.command == "status" else wait_boot(args.timeout)
    print(json.dumps(result, sort_keys=True))
    if not result["booted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
