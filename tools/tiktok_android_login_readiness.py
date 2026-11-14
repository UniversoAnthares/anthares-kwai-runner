#!/usr/bin/env python3
"""Monitor user-managed Google Play/TikTok installation without reading credentials.

All logs are boolean; no account names, e-mail, cookies or Android screenshot
are printed or stored. When Google and TikTok are both present, keep the GUI
available for another 120 s before checkpointing. Default window: 22 minutes.
"""
import os
import subprocess
import time
from pathlib import Path

ADB=Path(os.environ.get("ANDROID_HOME","/usr/local/lib/android/sdk"))/"platform-tools"/"adb"
TIME_LIMIT=int(os.environ.get("ANTHARES_LOGIN_WINDOW_SECONDS","1320"))
def run(*a):
    try:
        p=subprocess.run([str(ADB),"-s","emulator-5554",*a],
                         capture_output=True,text=True,timeout=16,check=False)
        return p.stdout if p.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):
        return ""

def check_google():
    data=run("shell","dumpsys","account")
    # This parsed result stays local; never export original account fields.
    low=data.lower()
    return "type=com.google" in low or "type: com.google" in low

def check_tiktok():
    return "package:" in run("shell","pm","path","com.zhiliaoapp.musically")

def main():
    t=time.monotonic()
    google=False;installed=False
    stable=0
    while time.monotonic()-t<TIME_LIMIT:
        g=check_google(); app=check_tiktok()
        if g and not google:print("TIKTOK_ANDROID_GOOGLE_ACCOUNT_PRESENT=1",flush=True)
        if app and not installed:print("TIKTOK_ANDROID_OFFICIAL_APP_INSTALLED=1",flush=True)
        google=google or g
        installed=installed or app
        stable=stable+1 if (g and app) else 0
        if stable>=4:
            print("TIKTOK_ANDROID_LOGIN_READY_FOR_CHECKPOINT=1",flush=True)
            time.sleep(120)
            break
        time.sleep(15)
    print("TIKTOK_ANDROID_GOOGLE_ACCOUNT_OBSERVED="+str(int(google)),flush=True)
    print("TIKTOK_ANDROID_TIKTOK_PACKAGE_OBSERVED="+str(int(installed)),flush=True)
    print("TIKTOK_ANDROID_LOGIN_WINDOW_FINISHED=1",flush=True)

if __name__=="__main__":
    main()
