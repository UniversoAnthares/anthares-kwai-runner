#!/usr/bin/env python3
import os, re, subprocess, sys, time, xml.etree.ElementTree as ET
from pathlib import Path

MODE = sys.argv[1] if len(sys.argv) > 1 else "camera-probe"
EVIDENCE = Path(os.environ.get("EVIDENCE_DIR", "x-live-evidence"))
EVIDENCE.mkdir(parents=True, exist_ok=True)
VARIANT = int(os.environ.get("MATRIX_VARIANT", "1"))
ALLOW_PUBLIC = os.environ.get("ALLOW_PUBLIC_LIVE", "0") == "1"


def run(*args, timeout=30, check=False):
    p = subprocess.run(list(args), text=True, capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{p.stderr}")
    return p


def adb(*args, **kw):
    return run("adb", *args, **kw)


def dump(name="window"):
    adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
    adb("pull", "/sdcard/window.xml", str(EVIDENCE / f"{name}.xml"))
    try:
        return list(ET.parse(EVIDENCE / f"{name}.xml").iter("node"))
    except Exception:
        return []


def shot(name):
    with open(EVIDENCE / f"{name}.png", "wb") as f:
        p = subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, stderr=subprocess.DEVNULL, timeout=20)
        return p.returncode == 0


def text_of(n):
    return " ".join(filter(None, [n.get("text", ""), n.get("content-desc", ""), n.get("resource-id", "")]))


def center(bounds):
    nums = [int(x) for x in re.findall(r"\d+", bounds or "")]
    if len(nums) != 4:
        return None
    x1, y1, x2, y2 = nums
    return (x1 + x2) // 2, (y1 + y2) // 2


def click_pattern(pattern, nodes=None):
    nodes = nodes or dump("click-scan")
    rx = re.compile(pattern, re.I)
    for n in nodes:
        if rx.search(text_of(n)):
            c = center(n.get("bounds"))
            if c:
                adb("shell", "input", "tap", str(c[0]), str(c[1]))
                time.sleep(1.5)
                return True
    return False


def foreground():
    out = adb("shell", "dumpsys", "window", "windows").stdout
    m = re.search(r"mCurrentFocus=.*? ([A-Za-z0-9_.$]+)/(\S+)", out)
    return m.group(1) if m else ""


def ensure_boot():
    adb("wait-for-device", timeout=90, check=True)
    deadline = time.time() + 90
    while time.time() < deadline:
        if adb("shell", "getprop", "sys.boot_completed").stdout.strip() == "1":
            break
        time.sleep(2)
    else:
        raise RuntimeError("Android did not finish booting")
    adb("emu", "avd", "hostmicon")


def camera_probe():
    ensure_boot()
    adb("shell", "am", "start", "-a", "android.media.action.VIDEO_CAMERA")
    time.sleep(5)
    nodes = dump("camera-preview")
    shot("camera-preview")
    fg = foreground()
    labels = [text_of(n) for n in nodes if text_of(n)][:40]
    (EVIDENCE / "camera-state.txt").write_text(f"foreground={fg}\nlabels={labels}\n", encoding="utf-8")
    if not fg:
        raise RuntimeError("No foreground camera activity detected")
    print(f"CAMERA_PREVIEW_OK foreground={fg}")


def package_installed(pkg):
    return pkg in adb("shell", "pm", "list", "packages", pkg).stdout


def x_preview():
    ensure_boot()
    pkg = "com.twitter.android"
    if not package_installed(pkg):
        raise RuntimeError("X Android package com.twitter.android is not installed")
    adb("shell", "pm", "grant", pkg, "android.permission.CAMERA")
    adb("shell", "pm", "grant", pkg, "android.permission.RECORD_AUDIO")
    adb("shell", "monkey", "-p", pkg, "1")
    time.sleep(5)
    shot("x-home")
    nodes = dump("x-home")

    if not click_pattern(r"compose|create|criar|postar|post|new post|novo post", nodes):
        size = adb("shell", "wm", "size").stdout
        m = re.search(r"(\d+)x(\d+)", size)
        w, h = map(int, m.groups()) if m else (1080, 1920)
        xs = [0.90, 0.92, 0.88, 0.94, 0.86]
        ys = [0.88, 0.91, 0.84, 0.94, 0.80]
        adb("shell", "input", "tap", str(int(w * xs[VARIANT % len(xs)])), str(int(h * ys[(VARIANT // 5) % len(ys)])))
        time.sleep(2)

    nodes = dump("x-compose")
    shot("x-compose")
    click_pattern(r"camera|câmera|video|vídeo", nodes)
    time.sleep(2)
    nodes = dump("x-camera")
    shot("x-camera")
    click_pattern(r"^live$|ao vivo|transmitir ao vivo|go live", nodes)
    time.sleep(3)
    nodes = dump("x-live-preview")
    shot("x-live-preview")
    joined = "\n".join(text_of(n) for n in nodes if text_of(n))
    (EVIDENCE / "x-live-state.txt").write_text(joined, encoding="utf-8")

    live_markers = re.search(r"go live|ao vivo|transmitir|live|what.?s happening|o que está acontecendo", joined, re.I)
    if not live_markers:
        raise RuntimeError("X Live preview was not confirmed by UI markers")

    if MODE == "x-go-live":
        if not ALLOW_PUBLIC:
            raise RuntimeError("Public live start blocked: set ALLOW_PUBLIC_LIVE=1 explicitly")
        if not click_pattern(r"go live|entrar ao vivo|iniciar transmissão|start live", nodes):
            raise RuntimeError("Final Go Live control not found")
        time.sleep(5)
        shot("x-live-started")
        print("X_LIVE_STARTED")
    else:
        print("X_LIVE_PREVIEW_OK")


def x_stop_live():
    ensure_boot()
    nodes = dump("x-live-before-stop")
    shot("x-live-before-stop")
    if not click_pattern(r"^stop$|parar|end live|encerrar", nodes):
        raise RuntimeError("Live stop control not found")
    time.sleep(1.5)
    nodes = dump("x-live-stop-confirm")
    click_pattern(r"stop|parar|end|encerrar|confirmar|confirm", nodes)
    time.sleep(3)
    shot("x-live-stopped")
    print("X_LIVE_STOPPED")


if MODE == "camera-probe":
    camera_probe()
elif MODE in ("x-preview", "x-go-live"):
    x_preview()
elif MODE == "x-stop-live":
    x_stop_live()
else:
    raise SystemExit("usage: x_android_live_ui.py {camera-probe|x-preview|x-go-live|x-stop-live}")
