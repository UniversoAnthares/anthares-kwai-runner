#!/usr/bin/env python3
"""Kwai profile-nav login probe.

Taps bottom-nav profile button when app is in kwai-pwa public feed,
then dumps and classifies the resulting screen to find login surface.
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ARTIFACT_DIR = Path("kwai-login-probe-artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run_adb(cmd: str) -> str:
    full = f"adb -s emulator-5554 {cmd}"
    p = subprocess.run(full, shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        return f"__ERROR__ {p.stderr.strip()}"
    return p.stdout.strip()


def dump_ui(suffix: str) -> str:
    out = ARTIFACT_DIR / f"ui-profile-{TIMESTAMP}-{suffix}.xml"
    p = subprocess.run("adb -s emulator-5554 shell uiautomator dump /sdcard/ui.xml", shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        return p.stderr.strip()
    time.sleep(1)
    subprocess.run("adb -s emulator-5554 pull /sdcard/ui.xml " + str(out), shell=True, text=True, capture_output=True)
    run_adb("shell rm /sdcard/ui.xml")
    try:
        return out.read_text(errors="ignore")
    except Exception:
        return "__ERROR__ unable to read dump"


def classify_screen(xml_text: str) -> str:
    low = xml_text.lower()
    if any(k in low for k in ["password", "phone", "login", "sign in", "entrar", "e-mail", "email"]):
        return "LOGIN"
    if any(k in low for k in ["settings", "logout", "sair", "perfil", "profile", "account"]):
        return "SETTINGS_OR_PROFILE"
    return "OTHER"


def main() -> None:
    steps = []
    wait = 3

    # Wait a bit to ensure feed is stable
    time.sleep(wait)

    # Dump initial feed state
    xml_before = dump_ui("feed-before")
    state_before = classify_screen(xml_before)
    steps.append({"step": "feed-before", "state": state_before})

    # Tap profile bottom-nav (right side)
    run_adb("shell input tap 900 1200")
    time.sleep(wait)

    xml_profile = dump_ui("profile-tapped")
    state_profile = classify_screen(xml_profile)
    steps.append({"step": "profile-tapped", "state": state_profile})

    # Swipe up once in case there are more options below the fold
    run_adb("shell input swipe 540 1600 540 800 400")
    time.sleep(wait)

    xml_swipe = dump_ui("profile-swiped")
    state_swipe = classify_screen(xml_swipe)
    steps.append({"step": "profile-swiped", "state": state_swipe})

    # Print structured result
    print(json.dumps(steps, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
