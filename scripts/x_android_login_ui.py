#!/usr/bin/env python3
import os, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path

USER = os.environ.get("X_ANDROID_USERNAME", "")
PASSWORD = os.environ.get("X_ANDROID_PASSWORD", "")
CHALLENGE = os.environ.get("X_ANDROID_CHALLENGE_ID", "")
OTP = os.environ.get("X_ANDROID_OTP", "")
OUT = Path(os.environ.get("EVIDENCE_DIR", "x-login-evidence"))
OUT.mkdir(parents=True, exist_ok=True)

if not USER or not PASSWORD:
    raise SystemExit("X_ANDROID_USERNAME and X_ANDROID_PASSWORD are required")


def run(*args, timeout=30):
    return subprocess.run(list(args), text=True, capture_output=True, timeout=timeout)


def adb(*args, timeout=30):
    return run("adb", *args, timeout=timeout)


def dump(name):
    adb("shell", "uiautomator", "dump", "/sdcard/w.xml")
    adb("pull", "/sdcard/w.xml", str(OUT / f"{name}.xml"))
    try:
        return list(ET.parse(OUT / f"{name}.xml").iter("node"))
    except Exception:
        return []


def shot(name):
    with open(OUT / f"{name}.png", "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, stderr=subprocess.DEVNULL, timeout=20)


def label(n):
    return " ".join([n.get("text", ""), n.get("content-desc", ""), n.get("resource-id", "")])


def center(n):
    nums = [int(x) for x in re.findall(r"\d+", n.get("bounds", ""))]
    return ((nums[0]+nums[2])//2, (nums[1]+nums[3])//2) if len(nums)==4 else None


def tap(rx, nodes):
    p = re.compile(rx, re.I)
    for n in nodes:
        if p.search(label(n)):
            c = center(n)
            if c:
                adb("shell", "input", "tap", str(c[0]), str(c[1])); time.sleep(1.5); return True
    return False


def edit_nodes(nodes):
    return [n for n in nodes if n.get("class", "").endswith("EditText") or re.search(r"edit|input", n.get("class", ""), re.I)]


def input_text(value, nodes, index=0):
    edits = edit_nodes(nodes)
    if len(edits) <= index:
        return False
    c = center(edits[index])
    if not c:
        return False
    adb("shell", "input", "tap", str(c[0]), str(c[1]))
    adb("shell", "input", "keyevent", "KEYCODE_MOVE_END")
    safe = value.replace("%", "%25").replace(" ", "%s")
    adb("shell", "input", "text", safe)
    time.sleep(0.7)
    return True


def joined(nodes):
    return "\n".join(label(n) for n in nodes if label(n).strip())

adb("wait-for-device", timeout=90)
adb("shell", "monkey", "-p", "com.twitter.android", "1")
time.sleep(5)

for step in range(12):
    nodes = dump(f"step-{step}")
    shot(f"step-{step}")
    text = joined(nodes)

    if re.search(r"home|timeline|for you|para você|following|seguindo", text, re.I) and not re.search(r"sign in|log in|entrar", text, re.I):
        print("X_ANDROID_LOGIN_OK")
        raise SystemExit(0)

    if tap(r"sign in|log in|entrar", nodes):
        continue

    low = text.lower()
    edits = edit_nodes(nodes)
    if edits:
        if re.search(r"password|senha", low):
            input_text(PASSWORD, nodes)
            tap(r"sign in|log in|entrar|next|avançar|continue|continuar", dump(f"password-{step}"))
            time.sleep(3)
            continue
        if re.search(r"code|verification|código|verificação|otp", low) and OTP:
            input_text(OTP, nodes)
            tap(r"next|verify|verificar|continue|continuar", dump(f"otp-{step}"))
            time.sleep(3)
            continue
        if re.search(r"phone|email|username|telefone|e-mail|usuário", low):
            value = CHALLENGE if CHALLENGE and re.search(r"confirm|verify|unusual|confirme|verifique|atividade", low) else USER
            input_text(value, nodes)
            tap(r"next|avançar|continue|continuar", dump(f"identity-{step}"))
            time.sleep(3)
            continue

    time.sleep(2)

nodes = dump("final")
shot("final")
text = joined(nodes)
if re.search(r"code|verification|código|verificação|otp", text, re.I):
    raise SystemExit("X_ANDROID_LOGIN_MFA_REQUIRED")
raise SystemExit("X_ANDROID_LOGIN_NOT_CONFIRMED")
