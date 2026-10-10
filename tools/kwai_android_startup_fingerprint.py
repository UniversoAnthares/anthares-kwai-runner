#!/usr/bin/env python3
"""Minimal, privacy-safe Android startup evidence. No UI XML, logcat text, secrets or identifiers."""
import json
import re
import subprocess

PKG="com.kwai.video"
def adb(*args,timeout=7):
    try:
        p=subprocess.run(["adb",*args],capture_output=True,text=True,timeout=timeout,check=False)
        return p.stdout if p.returncode==0 else ""
    except (OSError,subprocess.SubprocessError):
        return ""

def summarize(packages, pid, focus, props, net, dumpsys):
    paths=[line.strip() for line in packages.splitlines() if line.startswith("package:")]
    abi=re.search(r"primaryCpuAbi=([\w-]+)",dumpsys)
    version=re.search(r"versionCode=(\d+)",dumpsys)
    return {
      "schema":"anthares.kwai.startup.v1",
      "package_present":bool(paths),
      "apk_split_count":len(paths),
      "app_running":bool(pid.strip()),
      "kwai_focused":PKG in focus,
      "android_boot_complete":props.strip()=="1",
      "network_connected":bool(re.search(r"(?i)state:\s*CONNECTED|state=CONNECTED|validated",net)),
      "cpu_abi":abi.group(1) if abi else "unknown",
      "version_code_present":bool(version),
      "android_error_dialog_visible":bool(re.search(r"(?i)Application Error|AppErrorDialog",focus)),
    }

def main():
    data=summarize(
        adb("shell","pm","path",PKG),
        adb("shell","pidof",PKG),
        adb("shell","dumpsys","window","windows"),
        adb("shell","getprop","sys.boot_completed"),
        adb("shell","dumpsys","connectivity"),
        adb("shell","dumpsys","package",PKG),
    )
    print("ANDROID_STARTUP_FINGERPRINT="+json.dumps(data,sort_keys=True))
if __name__=="__main__":main()
