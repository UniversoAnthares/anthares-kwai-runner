#!/usr/bin/env python3
"""Kwai deep-link + exported-activity probe.

Non-credentialed probe to discover login surface via:
- Exported activities declared in the Manifest
- Deep links ikwai://login and variants
- Profile nav to settings/logout
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ARTIFACT_DIR = Path("kwai-login-probe-artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
RUN_ID = os_environ("GITHUB_RUN_ID", "local")

# Keep imports at top
import os as _os_mod

def os_environ(key: str, default: str = "") -> str:
    return _os_mod.environ.get(key, default)


def run_adb(cmd: str) -> str:
    full = f"adb -s emulator-5554 {cmd}"
    p = subprocess.run(full, shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        return f"__ERROR__ {p.stderr.strip()}"
    return p.stdout.strip()


def dump_manifest() -> str:
    return run_adb("shell pm dump com.kwai.video | head -n 400")


def search_manifest_login(manifest_dump: str) -> str:
    hits = []
    for line in manifest_dump.splitlines():
        low = line.lower()
        if any(k in low for k in [
            "ikwai://", "login", "auth", "account", "signin", "sign-in",
            "exported", "activity"
        ]):
            hits.append(line)
    return "\n".join(hits) if hits else "__NO_HITS__"


def list_activities() -> str:
    return run_adb("shell cmd package resolve-activity -c android.intent.category.LAUNCHER com.kwai.video || true")


def try_deep_link(uri: str) -> str:
    return run_adb(f"shell am start -a android.intent.action.VIEW -d '{uri}' com.kwai.video")


def try_activity(component: str) -> str:
    return run_adb(f"shell am start -n {component}")


def tap_center() -> str:
    return run_adb("shell input tap 540 1200")


def swipe_up() -> str:
    return run_adb("shell input swipe 540 1600 540 800 400")


def dump_ui(suffix: str) -> str:
    out = ARTIFACT_DIR / f"ui-deeplink-{TIMESTAMP}-{suffix}.xml"
    p = subprocess.run("adb -s emulator-5554 shell uiautomator dump /sdcard/ui.xml", shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        return p.stderr.strip()
    time.sleep(1)
    subprocess.run("adb -s emulator-5554 pull /sdcard/ui.xml " + str(out), shell=True, text=True, capture_output=True)
    run_adb("shell rm /sdcard/ui.xml")
    return out.read_text(errors="ignore")


def classify_screen(xml_text: str) -> str:
    low = xml_text.lower()
    if any(k in low for k in ["password", "phone", "login", "sign in", "entrar"]):
        return "LOGIN"
    if any(k in low for k in ["settings", "logout", "sair", "perfil"]):
        return "SETTINGS"
    return "OTHER"


def append_finding(markdown: str) -> None:
    findings_dir = Path("test-hub/findings")
    findings_dir.mkdir(parents=True, exist_ok=True)
    path = findings_dir / f"{TIMESTAMP}-kwai-deeplink-probe.md"
    path.write_text(markdown, encoding="utf-8")


def main() -> None:
    steps: list[dict] = []
    wait = 3

    # Step 1: manifest analysis
    manifest_dump = dump_manifest()
    steps.append({"step": "manifest-dump", "snippet": manifest_dump[:1000]})
    hits = search_manifest_login(manifest_dump)
    steps.append({"step": "manifest-hits", "hits": hits})
    time.sleep(wait)

    # Step 2: deep link ikwai://login
    dl = try_deep_link("ikwai://login")
    steps.append({"step": "deep-link-ikwai-login", "output": dl})
    time.sleep(wait)
    xml_after = dump_ui("after-ikwai-login")
    steps.append({"step": "ui-after-ikwai-login", "state": classify_screen(xml_after)})

    # Step 3: exported launcher activity and candidate auth activities
    launcher = list_activities()
    steps.append({"step": "launcher-activity", "output": launcher})
    time.sleep(wait)
    for comp in [
        "com.kwai.video/.ui.login.LoginActivity",
        "com.kwai.video/.ui.login.PhoneLoginActivity",
        "com.kwai.video/.ui.login.SignInActivity",
        "com.kwai.video/.ui.login.AuthActivity",
        "com.kwai.video/.ui.profile.ProfileActivity",
        "com.kwai.video/.ui.settings.SettingsActivity",
        "com.kwai.video/.account.AccountActivity",
    ]:
        res = try_activity(comp)
        steps.append({"step": f"activity-{comp}", "output": res})
        time.sleep(wait)

    # Step 4: bottom nav profile
    run_adb("shell input tap 900 1200")
    time.sleep(wait)
    xml_profile = dump_ui("profile-nav")
    steps.append({"step": "profile-nav", "state": classify_screen(xml_profile)})

    # Step 5: swipe and try to find settings/logout
    swipe_up()
    time.sleep(wait)
    run_adb("shell input tap 500 1500")
    time.sleep(wait)
    xml_post_swipe = dump_ui("post-swipe-profile")
    steps.append({"step": "post-swipe-profile", "state": classify_screen(xml_post_swipe)})

    run_id_display = os_environ("GITHUB_RUN_ID", "local")
    md = "\n".join([
        f"# Kwai deeplink + exported-activity probe\nSTATUS: PARTIAL\nAREA: kwai-login\nDATE: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\nRUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/{run_id_display}\n",
        "## Steps",
        "\n".join([f"- {s['step']}: {s.get('state', s.get('hits', s.get('output', '')))}" for s in steps]),
        "## Full steps",
        json.dumps(steps, ensure_ascii=False, indent=2),
    ])
    append_finding(md)

    print(json.dumps(steps, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
