#!/usr/bin/env python3
"""Diagnose Google Play UI hydration in a disposable cloud Android emulator.

Click only an enabled, visible "Install/Instalar" control for the exact official
TikTok package page already opened by ACTION_VIEW. Never click sign-in,
guess coordinates, use alternate APK sources, or export screen/account contents.
"""
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ADB = os.getenv("ANDROID_ADB", "adb")
SERIAL = "emulator-5554"
PKG = "com.zhiliaoapp.musically"
REMOTE_XML = "/sdcard/tiktok-market.xml"
LOCAL_XML = Path("/tmp/tiktok-market.xml")
MAX_CHECKS = 18  # 90 seconds total for Play Store initial hydration
INSTALL_TIMEOUT_SEC = 90

SIGN_IN = re.compile(
    r"(?:^|\W)(?:sign in|log in|entrar|fazer login|iniciar sess[aã]o|"
    r"add account|adicionar conta|continuar com o google)(?:\W|$)", re.I
)
INSTALL = re.compile(r"^(?:install|instalar|instalar app|instalar aplicativo)$", re.I)

def adb(*parts, timeout=20):
    return subprocess.run([ADB, "-s", SERIAL, *parts], capture_output=True,
                          text=True, timeout=timeout, check=False)

def already_installed():
    done=adb("shell", "pm", "path", PKG, timeout=12)
    return done.returncode == 0 and "package:" in done.stdout

def read_nodes():
    adb("shell", "uiautomator", "dump", REMOTE_XML, timeout=25)
    dump=adb("exec-out", "cat", REMOTE_XML, timeout=12)
    if dump.returncode != 0 or not dump.stdout.strip().startswith("<?xml"):
        return []
    try: root=ET.fromstring(dump.stdout)
    except ET.ParseError: return []
    return [n.attrib for n in root.iter("node")]

def value(node):
    return " ".join(str(node.get(k) or "").strip() for k in ("text","content-desc")).strip()

def center(box):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", box or "")
    if not m: return None
    x1,y1,x2,y2=map(int,m.groups())
    if x1>=x2 or y1>=y2: return None
    return ((x1+x2)//2,(y1+y2)//2)

def classify(nodes):
    texts=[value(n) for n in nodes]
    labels=" ".join(texts).lower()
    sign_in=any(SIGN_IN.search(t) for t in texts)
    tiktok_visible=("tiktok" in labels)
    install_candidates=[]
    for node in nodes:
        label=value(node)
        if INSTALL.fullmatch(label) and node.get("enabled") == "true":
            pos=center(node.get("bounds"))
            if pos: install_candidates.append(pos)
    unavailable=any(q in labels for q in (
        "not available", "indisponível", "not compatible",
        "incompatible", "item not found", "não disponível"))
    return {
        "node_count":len(nodes),
        "signin":bool(sign_in),
        "tiktok_visible":tiktok_visible,
        "install_candidates":install_candidates,
        "unavailable":unavailable
    }

def run():
    if already_installed():
        print("TIKTOK_GOOGLE_PLAY_OUTCOME=ALREADY_INSTALLED",flush=True)
        return 0
    recent=None
    for attempt in range(1,MAX_CHECKS+1):
        nodes=read_nodes()
        d=classify(nodes)
        recent=d
        print(f"TIKTOK_GOOGLE_PLAY_POLL={attempt} "
              f"nodes={d['node_count']} tiktok={str(d['tiktok_visible']).lower()} "
              f"signin={str(d['signin']).lower()} "
              f"install={str(bool(d['install_candidates'])).lower()} "
              f"unavailable={str(d['unavailable']).lower()}",flush=True)
        if d["signin"] and not d["install_candidates"]:
            print("TIKTOK_GOOGLE_PLAY_OUTCOME=GOOGLE_ACCOUNT_REQUIRED",flush=True)
            return 0
        if d["unavailable"] and not d["install_candidates"]:
            print("TIKTOK_GOOGLE_PLAY_OUTCOME=APP_UNAVAILABLE_IN_STORE",flush=True)
            return 0
        if d["install_candidates"] and d["tiktok_visible"]:
            x,y=d["install_candidates"][0]
            clicked=adb("shell","input","tap",str(x),str(y),timeout=10)
            if clicked.returncode:
                print("TIKTOK_GOOGLE_PLAY_OUTCOME=INSTALL_TAP_FAILED",flush=True)
                return 1
            print("TIKTOK_GOOGLE_PLAY_INSTALL_CONTROL_CLICKED=1",flush=True)
            for _ in range(INSTALL_TIMEOUT_SEC//5):
                if already_installed():
                    print("TIKTOK_GOOGLE_PLAY_OUTCOME=OFFICIAL_APP_INSTALLED",flush=True)
                    return 0
                time.sleep(5)
            print("TIKTOK_GOOGLE_PLAY_OUTCOME=INSTALL_NOT_COMPLETED",flush=True)
            return 0
        time.sleep(5)
    if recent and recent["node_count"]==0:
        print("TIKTOK_GOOGLE_PLAY_OUTCOME=UI_DUMP_UNAVAILABLE",flush=True)
    else:
        print("TIKTOK_GOOGLE_PLAY_OUTCOME=INSTALL_CONTROL_NEVER_APPEARED",flush=True)
    return 0

if __name__=="__main__":
    try: sys.exit(run())
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("TIKTOK_GOOGLE_PLAY_OUTCOME=TRANSPORT_"+type(exc).__name__.upper(),flush=True)
        sys.exit(1)
