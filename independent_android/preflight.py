#!/usr/bin/env python3
"""Anthares-owned Android runtime preflight. Never handles credentials or user data."""
import json, os, subprocess, sys
def run(*args, timeout=25):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    return p.returncode,p.stdout.strip()
def main():
    checks={}
    checks["kvm_present"]=os.path.exists("/dev/kvm")
    checks["adb_available"]=run("bash","-lc","command -v adb")[0]==0
    checks["emulator_available"]=run("bash","-lc","command -v emulator")[0]==0
    if checks["adb_available"]:
        rc,devices=run("adb","devices")
        checks["android_connected"]=rc==0 and any("\tdevice" in line for line in devices.splitlines()[1:])
        if checks["android_connected"]:
            rc,pkg=run("adb","shell","pm","path","com.kwai.video")
            checks["kwai_installed"]=rc==0 and pkg.startswith("package:")
            rc,boot=run("adb","shell","getprop","sys.boot_completed")
            checks["android_booted"]=rc==0 and boot=="1"
    print("ANTHARES_ANDROID_PREFLIGHT="+json.dumps(checks,sort_keys=True))
    return 0 if checks.get("android_connected") and checks.get("android_booted") else 3
if __name__=="__main__":sys.exit(main())
