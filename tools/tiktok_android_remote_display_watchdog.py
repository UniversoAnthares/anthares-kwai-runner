#!/usr/bin/env python3
"""Keep the *display* of a disposable cloud Android healthy while owner signs in.

Actions runner only. No screenshot, account text, tokens or credentials leave
the machine. Pixel counts and process state are emitted, never image contents.
Restart scrcpy/X11 window only; AVD and Google login state are preserved.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TITLE = "Android virtual Google Play"
SCRCPY = "/tmp/scrcpy-linux-x86_64-v3.3.4/scrcpy"
ADB = os.path.join(os.environ.get("ANDROID_HOME", "/usr/local/lib/android/sdk"), "platform-tools", "adb")
DURATION = int(os.environ.get("ANDROID_WATCHDOG_SECONDS", "2250"))
os.environ["DISPLAY"] = ":99"

def cmd(argv, timeout=15):
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, timeout=timeout, check=False)

def process_count(pattern):
    p = cmd(["pgrep", "-fc", pattern], 6)
    try:
        return int(p.stdout.strip() or "0")
    except ValueError:
        return 0

def windows():
    p = cmd(["xdotool", "search", "--name", TITLE], 8)
    if p.returncode:
        return []
    return [x for x in p.stdout.splitlines() if x.strip().isdigit()]

def expose_window():
    candidates = windows()
    if not candidates:
        return False
    for win in candidates:
        cmd(["xdotool", "windowmap", win], 7)
        cmd(["xdotool", "windowraise", win], 7)
        geom = cmd(["xdotool", "getwindowgeometry", "--shell", win], 8).stdout
        dims = dict(line.strip().split("=", 1) for line in geom.splitlines() if "=" in line)
        try:
            x = max(0, (1280 - int(dims.get("WIDTH", "400"))) // 2)
            y = max(0, (940 - int(dims.get("HEIGHT", "800"))) // 2)
            cmd(["xdotool", "windowmove", win, str(x), str(y)], 7)
        except ValueError:
            pass
    return True

def frame_black():
    from PIL import Image
    with tempfile.NamedTemporaryFile(suffix=".png", prefix="android-v6-", delete=False) as f:
        path = Path(f.name)
    try:
        shot = cmd(["scrot", "-o", str(path)], 12)
        if shot.returncode or path.stat().st_size < 500:
            return None
        with Image.open(path) as im:
            pixels = list(im.convert("RGB").resize((120, 88)).getdata())
        dark = sum(1 for r, g, b in pixels if max(r, g, b) < 28)
        return dark / max(1, len(pixels)) > .967
    except (OSError, ValueError):
        return None
    finally:
        path.unlink(missing_ok=True)

def launch_scrcpy():
    cmd(["pkill", "-x", "scrcpy"], 7)
    time.sleep(2)
    if not os.path.isfile(SCRCPY):
        raise RuntimeError("SCRCPY_BINARY_MISSING")
    log = open("/tmp/tiktok-scrcpy-v6-recovery.log", "ab", buffering=0)
    try:
        subprocess.Popen([
            SCRCPY, "-s", "emulator-5554", "--no-audio", "--stay-awake",
            "--max-size=1000", "--window-title=" + TITLE
        ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
           env=dict(os.environ))
    finally:
        log.close()
    time.sleep(6)
    return expose_window()

def main():
    deadline = time.monotonic() + DURATION
    dark_streak = 0
    recoveries = 0
    first_healthy = False
    while time.monotonic() < deadline:
        if process_count("cloudflared tunnel --no-autoupdate") == 0:
            raise RuntimeError("TUNNEL_PROCESS_LOST")
        adb = cmd([ADB, "-s", "emulator-5554", "get-state"], 8)
        if "device" not in adb.stdout:
            raise RuntimeError("ANDROID_ADB_DEVICE_LOST")
        # This does not click on Google consent or login screens.
        cmd([ADB, "-s", "emulator-5554", "shell", "svc", "power", "stayon", "true"], 8)
        cmd([ADB, "-s", "emulator-5554", "shell", "input", "keyevent", "KEYCODE_WAKEUP"], 8)
        mapped = expose_window()
        black = frame_black()
        healthy = mapped and black is False
        if healthy:
            dark_streak = 0
            if not first_healthy:
                print("ANDROID_REMOTE_V6_DISPLAY_VISIBLE=1", flush=True)
                first_healthy = True
        else:
            dark_streak += 1
            print("ANDROID_REMOTE_V6_DISPLAY_CHECK="
                  + ("WINDOW_MISSING" if not mapped else "BLACK_FRAME" if black else "FRAME_UNREADABLE"), flush=True)
        if dark_streak >= 3:
            recoveries += 1
            print("ANDROID_REMOTE_V6_SCRCPY_RESTART=" + str(recoveries), flush=True)
            if not launch_scrcpy():
                print("ANDROID_REMOTE_V6_WINDOW_RESTART_UNCONFIRMED=1", flush=True)
            dark_streak = 0
            if recoveries > 6 and not first_healthy:
                raise RuntimeError("DISPLAY_UNRECOVERABLE")
        time.sleep(10)
    if not first_healthy:
        raise RuntimeError("DISPLAY_NEVER_VISIBLE")
    print("ANDROID_REMOTE_V6_LOGIN_WINDOW_CLOSED=1", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        code = str(exc)
        if code not in {"TUNNEL_PROCESS_LOST", "ANDROID_ADB_DEVICE_LOST",
                        "DISPLAY_UNRECOVERABLE", "DISPLAY_NEVER_VISIBLE", "SCRCPY_BINARY_MISSING"}:
            code = "WATCHDOG_EXCEPTION_" + type(exc).__name__.upper()
        print("ANDROID_REMOTE_V6_WATCHDOG_FAILED=" + code, flush=True)
        sys.exit(1)
