#!/usr/bin/env python3
"""Read-only, credential-free first gate for a candidate cloud VPS running ReDroid.

This script never provisions resources, downloads images, modifies the host,
uses a physical Android device, or transmits machine-identifying information.
The output is only a preliminary *technical* acceptance gate. Provider
legitimacy, cost, tenancy isolation, binder loadability, and privileged
container execution need separate verification before installing Android.
"""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

MIN_CPUS = 2
MIN_MEMORY_MIB = 4096
MIN_DISK_FREE_GIB = 20
ALLOWED_ARCHES = {"aarch64", "arm64", "x86_64", "amd64"}
CONTAINER_VIRT = {"lxc", "lxc-libvirt", "docker", "podman", "openvz", "systemd-nspawn", "wsl"}


def _read(path):
    try:
        return Path(path).read_text(errors="replace")
    except (OSError, UnicodeError):
        return ""


def _command(*args):
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=3, check=False)
        return result.returncode, result.stdout.strip().lower()
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def binder_probe():
    devices = ("/dev/binder", "/dev/hwbinder", "/dev/vndbinder")
    if all(Path(p).exists() for p in devices):
        return "DEVICES_PRESENT"
    if Path("/dev/binderfs").exists():
        return "BINDERFS_PRESENT"
    if Path("/sys/module/binder_linux").exists():
        return "KERNEL_MODULE_LOADED"
    code, _ = _command("modinfo", "-n", "binder_linux")
    if code == 0:
        return "KERNEL_MODULE_FOUND"
    if "nodev\tbinder" in _read("/proc/filesystems"):
        return "BINDERFS_REGISTERED"
    kernel = platform.release()
    config = _read("/boot/config-" + kernel)
    if "CONFIG_ANDROID_BINDER_IPC=y" in config or "CONFIG_ANDROID_BINDER_IPC=m" in config:
        return "KERNEL_CONFIG_ENABLED"
    return "UNVERIFIED"


def virtualization():
    code, output = _command("systemd-detect-virt")
    return output if code == 0 and output else "unknown"


def snapshot():
    mem = 0
    for line in _read("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            try:
                mem = int(line.split()[1]) // 1024
            except (ValueError, IndexError):
                pass
            break
    try:
        disk = shutil.disk_usage("/").free / (1024**3)
    except OSError:
        disk = 0
    return {
        "arch": platform.machine().lower(),
        "cpus": os.cpu_count() or 0,
        "memory_mib": mem,
        "disk_free_gib": round(disk, 1),
        "root": hasattr(os, "geteuid") and os.geteuid() == 0,
        "virtualization": virtualization(),
        "binder_probe": binder_probe(),
        "docker_cli_installed": shutil.which("docker") is not None,
        "os": platform.system(),
    }


def assess(host):
    failures = []
    if host.get("os") != "Linux":
        failures.append("LINUX_REQUIRED")
    if host.get("arch") not in ALLOWED_ARCHES:
        failures.append("SUPPORTED_CPU_ARCH_REQUIRED")
    if host.get("cpus", 0) < MIN_CPUS:
        failures.append("INSUFFICIENT_VCPU")
    if host.get("memory_mib", 0) < MIN_MEMORY_MIB:
        failures.append("INSUFFICIENT_MEMORY")
    if host.get("disk_free_gib", 0) < MIN_DISK_FREE_GIB:
        failures.append("INSUFFICIENT_FREE_DISK")
    if not host.get("root"):
        failures.append("ROOT_REQUIRED")
    if host.get("virtualization") in CONTAINER_VIRT:
        failures.append("HOST_KERNEL_CONTROL_UNAVAILABLE_OR_UNPROVEN")

    if failures:
        status = "REJECTED"
    elif host.get("binder_probe") == "UNVERIFIED":
        status = "BINDER_PROOF_REQUIRED"
    else:
        status = "CANDIDATE_FOR_ISOLATED_INSTALL_TEST"

    return {
        "status": status,
        "failures": failures,
        "mandatory_unverified": [
            "PROVIDER_TRUST_AND_ZERO_COST",
            "PERSISTENCE_AFTER_REBOOT",
            "ACTUAL_PRIVILEGED_DOCKER_EXECUTION",
            "ACTUAL_BINDER_DEVICE_CREATION_AND_ANDROID_BOOT",
            "NO_PUBLIC_ADB",
            "KWAI_SESSION_AND_NEON_FENCED_FAILOVER",
        ],
    }


def main():
    host = snapshot()
    print(json.dumps({"host": host, "assessment": assess(host)},
                     ensure_ascii=False, sort_keys=True))
    return 0 if assess(host)["status"] == "CANDIDATE_FOR_ISOLATED_INSTALL_TEST" else 2


if __name__ == "__main__":
    raise SystemExit(main())
