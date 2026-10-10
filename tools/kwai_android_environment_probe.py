#!/usr/bin/env python3
"""Compare Android runtime compatibility using only bounded, nonidentifying fields."""
import json
import re
import subprocess

PROPS={
    "sdk":"ro.build.version.sdk",
    "abi":"ro.product.cpu.abi",
    "graphics":"ro.hardware.egl",
    "boot_completed":"sys.boot_completed",
}
SAFE={"sdk":re.compile(r"^[0-9]{1,2}$"),
      "abi":re.compile(r"^(x86_64|x86|arm64-v8a|armeabi-v7a)$"),
      "graphics":re.compile(r"^[a-zA-Z0-9_.-]{1,48}$"),
      "boot_completed":re.compile(r"^[01]$")}

def run(*args):
    try:
        return subprocess.run(["adb",*args],capture_output=True,text=True,timeout=8,check=True).stdout.strip()
    except (OSError,subprocess.SubprocessError):
        return ""

def sanitize(key,value):
    return value if SAFE[key].fullmatch(value) else "unknown"

def collect():
    props={key:sanitize(key,run("shell","getprop",prop)) for key,prop in PROPS.items()}
    package=run("shell","dumpsys","package","com.kwai.video")
    version=re.search(r"versionCode=(\d{1,12})",package)
    permissions=re.search(r"targetSdk=(\d{1,2})",package)
    graphics=run("shell","getprop","ro.kernel.qemu")
    return {
        "schema":"anthares.mobile.android-environment.v1",
        "properties":props,
        "app_version_code":version.group(1) if version else "unknown",
        "app_target_sdk":permissions.group(1) if permissions else "unknown",
        "emulator":graphics=="1",
        "package_installed":bool(run("shell","pm","path","com.kwai.video")),
        "app_process_running":bool(run("shell","pidof","com.kwai.video")),
    }

if __name__=="__main__":
    print(json.dumps(collect(),sort_keys=True))
