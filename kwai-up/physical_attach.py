#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

SUPPORTED_PACKAGES = ("com.kwai.video", "kwai.lite.video")


def adb_candidates() -> list[Path]:
    out: list[Path] = []
    configured = os.getenv("KWAI_UP_ADB_BIN", "").strip()
    if configured:
        out.append(Path(configured).expanduser())
    found = shutil.which("adb")
    if found:
        out.append(Path(found))
    if os.name == "nt":
        out.extend([
            Path.home() / ".kwai-up" / "platform-tools" / "adb.exe",
            Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        ])
    return out


def find_adb() -> Path:
    for candidate in adb_candidates():
        if candidate.is_file():
            return candidate.resolve()
    raise SystemExit("KWAI_UP_PHYSICAL=NO_ADB")


def run(adb: Path, *args: str, serial: str = "", timeout: int = 30, check: bool = True) -> str:
    cmd = [str(adb)]
    if serial:
        cmd += ["-s", serial]
    cmd += list(args)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"adb rc={p.returncode}: {' '.join(args)} :: {p.stdout[-1000:]}")
    return p.stdout.strip()


def devices(adb: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    text = run(adb, "devices", "-l", check=False)
    for raw in text.splitlines()[1:]:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        rows.append((serial, state, line))
    return rows


def one_usb_device(adb: Path) -> str:
    rows = devices(adb)
    unauthorized = [r for r in rows if r[1] == "unauthorized"]
    if unauthorized:
        print("KWAI_UP_PHYSICAL=UNAUTHORIZED")
        print("KWAI_UP_USB_SERIAL=" + unauthorized[0][0])
        raise SystemExit(12)
    online = [r for r in rows if r[1] == "device" and ":" not in r[0]]
    if len(online) != 1:
        print(f"KWAI_UP_PHYSICAL=USB_DEVICE_COUNT:{len(online)}")
        for _, _, line in rows:
            print("ADB_DEVICE=" + line)
        raise SystemExit(11)
    return online[0][0]


def wifi_ip(adb: Path, serial: str) -> str:
    text = run(adb, "shell", "ip", "-f", "inet", "addr", "show", "wlan0", serial=serial, check=False)
    m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", text)
    if m:
        return m.group(1)
    text = run(adb, "shell", "ip", "route", serial=serial, check=False)
    m = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", text)
    if m:
        return m.group(1)
    raise SystemExit("KWAI_UP_PHYSICAL=NO_WIFI_IP")


def detect_package(adb: Path, serial: str) -> str:
    requested = os.getenv("KWAI_UP_PACKAGE", "").strip()
    candidates = (requested,) if requested else SUPPORTED_PACKAGES
    for package in candidates:
        if not package:
            continue
        pkg = run(adb, "shell", "pm", "path", package, serial=serial, check=False)
        if pkg.startswith("package:"):
            return package
    print("KWAI_UP_PHYSICAL=KWAI_NOT_INSTALLED")
    raise SystemExit(13)


def validate(adb: Path, serial: str) -> str:
    model = run(adb, "shell", "getprop", "ro.product.model", serial=serial)
    sdk = run(adb, "shell", "getprop", "ro.build.version.sdk", serial=serial)
    package = detect_package(adb, serial)
    print("KWAI_UP_PHYSICAL=READY")
    print("KWAI_UP_MODEL=" + model)
    print("KWAI_UP_SDK=" + sdk)
    print("KWAI_UP_ADB_SERIAL=" + serial)
    print("KWAI_UP_PACKAGE=" + package)
    return package


def attach_tcp(adb: Path, usb_serial: str, port: int) -> str:
    ip = wifi_ip(adb, usb_serial)
    out = run(adb, "tcpip", str(port), serial=usb_serial, check=False)
    if "restarting in TCP mode" not in out and "already" not in out.lower():
        raise RuntimeError("ADB_TCPIP_FAILED: " + out)
    endpoint = f"{ip}:{port}"
    time.sleep(2)
    out = run(adb, "connect", endpoint, check=False)
    if "connected to" not in out.lower() and "already connected" not in out.lower():
        raise RuntimeError("ADB_CONNECT_FAILED: " + out)
    run(adb, "shell", "true", serial=endpoint)
    return endpoint


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a dedicated physical Android for Kwai-up")
    parser.add_argument("mode", choices=["probe-usb", "attach-tcp", "validate"])
    parser.add_argument("--serial", default=os.getenv("KWAI_UP_ADB_SERIAL", ""))
    parser.add_argument("--port", type=int, default=int(os.getenv("KWAI_UP_ADB_PORT", "5555")))
    args = parser.parse_args()

    adb = find_adb()
    run(adb, "start-server", check=False)
    os.environ["PATH"] = str(adb.parent) + os.pathsep + os.environ.get("PATH", "")
    print("KWAI_UP_ADB_BIN=" + str(adb))

    if args.mode == "probe-usb":
        serial = one_usb_device(adb)
        validate(adb, serial)
        return 0

    if args.mode == "attach-tcp":
        usb_serial = one_usb_device(adb)
        validate(adb, usb_serial)
        endpoint = attach_tcp(adb, usb_serial, args.port)
        validate(adb, endpoint)
        print("KWAI_UP_TRANSPORT=ADB_TCP")
        return 0

    if not args.serial:
        raise SystemExit("KWAI_UP_PHYSICAL=MISSING_SERIAL")
    validate(adb, args.serial)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
