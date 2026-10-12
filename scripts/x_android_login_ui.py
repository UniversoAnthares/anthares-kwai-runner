#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PKG = "com.twitter.android"
USER = (os.environ.get("X_ANDROID_USERNAME") or "lucasrosalem").strip()
PASSWORD = os.environ.get("X_ANDROID_PASSWORD", "")
CHALLENGE = os.environ.get("X_ANDROID_CHALLENGE_ID", "").strip()
OTP = os.environ.get("X_ANDROID_OTP", "").strip()
OUT = Path(os.environ.get("EVIDENCE_DIR", "x-login-evidence"))
VARIANT = int(os.environ.get("X_LOGIN_VARIANT", "1"))
WAIT = float(os.environ.get("X_LOGIN_WAIT", "4"))
LAUNCH_MODE = int(os.environ.get("X_LOGIN_LAUNCH_MODE", str((VARIANT - 1) % 4)))
INPUT_BACKEND = os.environ.get("X_LOGIN_INPUT_BACKEND", "adb").strip().lower()
OUT.mkdir(parents=True, exist_ok=True)

if not PASSWORD:
    print("VERDICT=BLOCKED_MISSING_X_ANDROID_PASSWORD")
    raise SystemExit(90)


def run(*args, timeout=30):
    return subprocess.run(list(args), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def adb(*args, timeout=30, check=False):
    p = run("adb", *args, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(p.stdout[-1200:])
    return p


def write(name, value):
    (OUT / name).write_text(str(value), encoding="utf-8")


def shot(name):
    try:
        with open(OUT / f"{name}.png", "wb") as f:
            subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, stderr=subprocess.DEVNULL, timeout=20)
    except Exception:
        pass


def dump(name):
    remote = f"/sdcard/x-login-{VARIANT}.xml"
    try:
        adb("shell", "uiautomator", "dump", remote, timeout=15)
        adb("pull", remote, str(OUT / f"{name}.xml"), timeout=15)
        return list(ET.parse(OUT / f"{name}.xml").iter("node"))
    except Exception as exc:
        write(f"{name}-dump-error.txt", type(exc).__name__)
        return []


def label(n):
    return " ".join([
        n.get("text", ""),
        n.get("content-desc", ""),
        n.get("resource-id", ""),
        n.get("class", ""),
    ]).strip()


def joined(nodes):
    return "\n".join(label(n) for n in nodes if label(n))


def center(n):
    nums = [int(x) for x in re.findall(r"\d+", n.get("bounds", ""))]
    if len(nums) != 4:
        return None
    return ((nums[0] + nums[2]) // 2, (nums[1] + nums[3]) // 2)


def tap_node(n):
    c = center(n)
    if not c:
        return False
    adb("shell", "input", "tap", str(c[0]), str(c[1]))
    time.sleep(1.0)
    return True


def tap_pattern(nodes, pattern):
    rx = re.compile(pattern, re.I)
    for n in nodes:
        if rx.search(label(n)) and tap_node(n):
            return True
    return False


def edit_nodes(nodes):
    return [
        n for n in nodes
        if n.get("class", "").endswith("EditText")
        or re.search(r"edit|input", n.get("class", ""), re.I)
    ]


def adb_input_text(value):
    safe = value.replace("%", "%25").replace(" ", "%s")
    p = adb("shell", "input", "text", safe, timeout=20)
    return p.returncode == 0


def u2_input_text(value):
    try:
        import uiautomator2 as u2
        d = u2.connect()
        focused = d(focused=True)
        if not focused.exists:
            return False
        focused.set_text(value)
        return True
    except Exception as exc:
        write("u2-input-error.txt", f"{type(exc).__name__}: {str(exc)[:300]}")
        return False


def input_text(value, nodes, index=0):
    edits = edit_nodes(nodes)
    if not edits:
        return False
    index = max(0, min(index, len(edits) - 1))
    if not tap_node(edits[index]):
        return False
    adb("shell", "input", "keyevent", "KEYCODE_MOVE_END")
    ok = False
    if INPUT_BACKEND == "u2":
        ok = u2_input_text(value)
    if not ok:
        ok = adb_input_text(value)
    time.sleep(0.8)
    return ok


def foreground_package():
    p = adb("shell", "dumpsys", "window", "windows", timeout=15)
    text = p.stdout or ""
    return PKG in text


def process_alive():
    p = adb("shell", "pidof", PKG, timeout=10)
    return p.returncode == 0 and bool((p.stdout or "").strip())


def signed_in(nodes):
    text = joined(nodes).lower()
    auth_gate = re.search(
        r"sign in|log in|login|entrar|create account|criar conta|phone.*email.*username|"
        r"telefone.*e-?mail.*usu|forgot password|esqueceu.*senha|password|senha",
        text,
        re.I,
    )
    groups = [
        r"\bhome\b|\binício\b|\binicio\b",
        r"\bsearch\b|\bexplore\b|\bpesquisar\b|\bexplorar\b",
        r"notification|notifica",
        r"message|mensage",
        r"\bprofile\b|\bperfil\b",
        r"compose|\bpost\b|publicar",
    ]
    hits = sum(bool(re.search(g, text, re.I)) for g in groups)
    return hits >= 2 and not auth_gate, hits


def classify_blocker(nodes):
    text = joined(nodes)
    patterns = [
        ("MFA_REQUIRED", r"two.factor|authentication code|verification code|código de autenticação|código de verificação|\botp\b"),
        ("CAPTCHA_OR_CHALLENGE", r"captcha|arkose|prove you.?re human|prove that you.?re human|verify you.?re human"),
        ("IDENTITY_CONFIRMATION_REQUIRED", r"unusual activity|suspicious|confirm.*email|confirm.*phone|verify.*email|verify.*phone|confirme.*e-?mail|confirme.*telefone"),
        ("BAD_CREDENTIALS", r"incorrect password|wrong password|invalid password|senha incorreta|password you entered|could not log you in"),
        ("ACCOUNT_LOCKED_OR_SUSPENDED", r"account.*locked|account.*suspended|conta.*bloqueada|conta.*suspensa"),
        ("RATE_LIMITED", r"too many attempts|try again later|muitas tentativas|tente novamente mais tarde"),
        ("APP_UPDATE_REQUIRED", r"update.*app|update x|atualiz.*aplicativo|atualiz.*x"),
    ]
    for verdict, rx in patterns:
        if re.search(rx, text, re.I):
            return verdict
    return "LOGIN_NOT_CONFIRMED"


def launch():
    adb("shell", "am", "force-stop", PKG)
    time.sleep(0.5)
    if LAUNCH_MODE == 0:
        adb("shell", "monkey", "-p", PKG, "1")
    elif LAUNCH_MODE == 1:
        p = adb("shell", "cmd", "package", "resolve-activity", "--brief", PKG)
        activity = (p.stdout or "").strip().splitlines()[-1:] or [""]
        if activity[0] and "/" in activity[0]:
            adb("shell", "am", "start", "-W", "-n", activity[0])
        else:
            adb("shell", "monkey", "-p", PKG, "1")
    elif LAUNCH_MODE == 2:
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    else:
        adb("shell", "am", "start", "-W", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-p", PKG)
    time.sleep(WAIT)


write("context.txt", f"variant={VARIANT}\nwait={WAIT}\nlaunch_mode={LAUNCH_MODE}\ninput_backend={INPUT_BACKEND}\nusername={USER}\n")
adb("wait-for-device", timeout=90, check=True)
launch()

last_nodes = []
for step in range(18):
    nodes = dump(f"step-{step:02d}")
    last_nodes = nodes
    shot(f"step-{step:02d}")
    text = joined(nodes)

    ok, hits = signed_in(nodes)
    write(f"step-{step:02d}-state.txt", f"success_marker_groups={hits}\nforeground={int(foreground_package())}\nprocess_alive={int(process_alive())}\n")
    if ok and foreground_package() and process_alive():
        write("verdict.txt", "X_ANDROID_AUTHENTICATED\n")
        print("VERDICT=X_ANDROID_AUTHENTICATED")
        raise SystemExit(0)

    # Dismiss common post-login prompts so the navigation bar can become visible.
    if tap_pattern(nodes, r"not now|maybe later|skip|agora não|agora nao|pular|mais tarde"):
        time.sleep(1.5)
        continue

    blocker = classify_blocker(nodes)
    if blocker in {"CAPTCHA_OR_CHALLENGE", "BAD_CREDENTIALS", "ACCOUNT_LOCKED_OR_SUSPENDED", "RATE_LIMITED", "APP_UPDATE_REQUIRED"}:
        write("verdict.txt", blocker + "\n")
        print(f"VERDICT={blocker}")
        raise SystemExit(50)

    if blocker == "MFA_REQUIRED" and not OTP:
        write("verdict.txt", blocker + "\n")
        print(f"VERDICT={blocker}")
        raise SystemExit(51)

    if blocker == "IDENTITY_CONFIRMATION_REQUIRED" and not CHALLENGE:
        write("verdict.txt", blocker + "\n")
        print(f"VERDICT={blocker}")
        raise SystemExit(52)

    if tap_pattern(nodes, r"sign in|log in|entrar|already have.*account|já tenho.*conta|ja tenho.*conta"):
        time.sleep(WAIT)
        continue

    low = text.lower()
    edits = edit_nodes(nodes)
    if edits:
        if re.search(r"password|senha", low):
            if input_text(PASSWORD, nodes, 0):
                nodes2 = dump(f"password-{step:02d}")
                tap_pattern(nodes2, r"sign in|log in|entrar|next|continue|avançar|continuar")
                time.sleep(WAIT)
                continue
        if re.search(r"code|verification|código|verificação|otp", low) and OTP:
            if input_text(OTP, nodes, 0):
                nodes2 = dump(f"otp-{step:02d}")
                tap_pattern(nodes2, r"next|verify|continue|avançar|verificar|continuar")
                time.sleep(WAIT)
                continue
        if re.search(r"phone|email|username|telefone|e-?mail|usuário|usuario", low):
            value = USER
            if CHALLENGE and re.search(r"confirm|verify|unusual|confirme|verifique|atividade", low):
                value = CHALLENGE
            # Alternate first/last visible edit field across variants.
            index = 0 if VARIANT % 2 else len(edits) - 1
            if input_text(value, nodes, index):
                nodes2 = dump(f"identity-{step:02d}")
                tap_pattern(nodes2, r"next|continue|avançar|seguinte|continuar")
                time.sleep(WAIT)
                continue

    time.sleep(max(1.0, WAIT / 2.0))

nodes = dump("final") or last_nodes
shot("final")
ok, hits = signed_in(nodes)
write("final-state.txt", f"success_marker_groups={hits}\nforeground={int(foreground_package())}\nprocess_alive={int(process_alive())}\n")
if ok and foreground_package() and process_alive():
    write("verdict.txt", "X_ANDROID_AUTHENTICATED\n")
    print("VERDICT=X_ANDROID_AUTHENTICATED")
    raise SystemExit(0)

verdict = classify_blocker(nodes)
write("verdict.txt", verdict + "\n")
print(f"VERDICT={verdict}")
raise SystemExit(59)
