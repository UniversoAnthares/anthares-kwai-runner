#!/usr/bin/env python3
"""Force Kwai login surface by clearing cached app data after vault install.

v2: after PARTIAL run 37638909906, clear-data is proven to drop cached MAIN and
land on INTEREST onboarding. This version advances INTEREST/START/PERMISSION
before declaring failure on missing login surface.

No credentials. No publication.
"""
import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET


def adb(*a, timeout=30):
    return subprocess.run(
        ["adb", *a],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    ).stdout


def dump():
    target = "/sdcard/kwai-clear-probe.xml"
    for _ in range(3):
        adb("shell", "uiautomator", "dump", target)
        raw = adb("shell", "cat", target)
        if raw.strip().startswith("<"):
            try:
                return ET.fromstring(raw)
            except Exception:
                pass
        time.sleep(1)
    return None


def nodes(root):
    return list(root.iter("node")) if root is not None else []


def node_info(n):
    return {
        "text": n.attrib.get("text", ""),
        "content_desc": n.attrib.get("content-desc", ""),
        "class": n.attrib.get("class", ""),
        "resource_id": n.attrib.get("resource-id", ""),
        "clickable": n.attrib.get("clickable", ""),
        "editable": n.attrib.get("editable", ""),
        "bounds": n.attrib.get("bounds", ""),
    }


def label_of(n):
    return (n.attrib.get("text", "") + " " + n.attrib.get("content-desc", "")).strip().lower()


def rid(ns, suffix):
    for n in ns:
        if n.attrib.get("resource-id", "").endswith(suffix):
            return n
    return None


def state_from_text(t):
    t = t.lower()
    if any(k in t for k in ("welcome to kwai", "continue with google", "use facebook")):
        return "LOGIN_SURFACE"
    if any(k in t for k in ("log in", "sign in", "entrar")) and (
        "phone" in t or "telefone" in t or "email" in t or "google" in t or "facebook" in t
    ):
        return "LOGIN_SURFACE"
    if "choose like or dislike" in t:
        return "INTEREST"
    if "select your interests" in t:
        return "INTEREST_SELECT"
    if "profile" in t and ("home" in t or "discover" in t or "inbox" in t):
        return "MAIN"
    if "resource downloading" in t or "hang in there" in t or "skip the preparation" in t:
        return "RESOURCE_LOADING"
    if "send you notifications" in t or "allow kwai" in t:
        return "PERMISSION"
    if "start now" in t or "you're all set" in t or "tudo pronto" in t:
        return "START"
    return "OTHER"


def snapshot(tag):
    root = dump()
    ns = nodes(root)
    txt = " ".join(label_of(n) for n in ns)
    s = state_from_text(txt)
    editables = [
        node_info(n)
        for n in ns
        if n.attrib.get("editable") == "true" or n.attrib.get("class", "").endswith("EditText")
    ]
    login_like = [
        node_info(n)
        for n in ns
        if any(
            k in label_of(n)
            for k in (
                "log in",
                "login",
                "sign in",
                "entrar",
                "phone",
                "telefone",
                "email",
                "e-mail",
                "password",
                "senha",
                "continue with google",
                "use facebook",
                "welcome to kwai",
                "verification",
            )
        )
    ]
    out = {
        "label": tag,
        "state": s,
        "text_preview": txt[:800],
        "editable_count": len(editables),
        "login_like_count": len(login_like),
        "editables": editables[:8],
        "login_like": login_like[:12],
        "kwai_ctx": any("com.kwai.video" in (n.attrib.get("resource-id") or "") for n in ns),
    }
    print(
        f"[CLEAR] {tag} state={s} edit={len(editables)} login_like={len(login_like)} kwai={out['kwai_ctx']}"
    )
    return out


def tap_node(n):
    b = n.attrib.get("bounds", "")
    m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b or "")
    if not m:
        return False
    x1, y1, x2, y2 = map(int, m.groups())
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
    time.sleep(1.5)
    return True


def tap_matching(words):
    root = dump()
    for n in nodes(root):
        if any(w in label_of(n) for w in words) and n.attrib.get("clickable") == "true":
            if tap_node(n):
                return True
    return False


def advance_onboarding(s, ns):
    if s == "PERMISSION":
        n = rid(ns, "permission_deny_button") or rid(ns, "permission_allow_button")
        if n is not None and tap_node(n):
            return True
        return tap_matching(("allow", "don’t allow", "dont allow", "permitir", "negar"))
    if s == "START":
        return tap_matching(("start now", "começar agora", "iniciar agora"))
    if s == "INTEREST":
        n = rid(ns, "tiny_discovery_dislike_button") or rid(ns, "tiny_discovery_like_button")
        if n is not None and tap_node(n):
            return True
        # swipe through interest cards if buttons not found
        adb("shell", "input", "swipe", "850", "1100", "180", "1100", "250")
        time.sleep(1)
        return True
    if s == "INTEREST_SELECT":
        if tap_matching(("skip", "pular")):
            return True
        adb("shell", "input", "tap", "90", "250")
        time.sleep(2)
        return True
    if s == "RESOURCE_LOADING":
        if tap_matching(("yes, skip", "yes skip", "skip", "pular", "hide")):
            return True
        n = rid(ns, "btn_cancel")
        if n is not None and tap_node(n):
            return True
        time.sleep(3)
        return True
    return False


# Phase 0: launch once (may be cached MAIN)
adb("shell", "am", "force-stop", "com.kwai.video")
time.sleep(1)
adb("shell", "monkey", "-p", "com.kwai.video", "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(10)

log = []
log.append(snapshot("pre-clear"))

print("[CLEAR] executing pm clear com.kwai.video")
clear_out = adb("shell", "pm", "clear", "com.kwai.video", timeout=60)
print("[CLEAR] pm_clear_out=" + clear_out.strip()[:200])
time.sleep(2)

adb("shell", "monkey", "-p", "com.kwai.video", "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(12)

found_surface = False
for i in range(24):
    root = dump()
    ns = nodes(root)
    s = snapshot(f"post-clear-{i}")
    log.append(s)
    if s["state"] == "LOGIN_SURFACE" or s["editable_count"] > 0:
        found_surface = True
        break
    if s["login_like_count"] > 0 and s["kwai_ctx"]:
        # login-like labels on Kwai tree count as surface exposure
        found_surface = True
        break
    if not s["kwai_ctx"]:
        # dismiss launcher permission or relaunch
        advance_onboarding(s["state"], ns)
        adb("shell", "am", "start", "-n", "com.kwai.video/com.yxcorp.gifshow.tiny.TinyLaunchActivity")
        time.sleep(5)
        continue
    if s["state"] in ("PERMISSION", "START", "INTEREST", "INTEREST_SELECT", "RESOURCE_LOADING"):
        advance_onboarding(s["state"], ns)
        time.sleep(1.5)
        continue
    if s["state"] == "MAIN":
        # cleared session reached MAIN without login surface — still a useful signal
        print("[CLEAR] reached MAIN after clear without login surface")
        break
    adb("shell", "input", "swipe", "850", "1100", "180", "1100", "250")
    time.sleep(1.2)

out_path = os.path.join(os.getcwd(), "kwai-clear-data-probe-log.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print(f"[CLEAR] log saved to {out_path}")

observed = [e for e in log if e.get("text_preview") or e.get("editables") or e.get("login_like")]
if not observed:
    print("[CLEAR] TEST_VALIDITY=INVALID no UI tree was read")
    raise SystemExit(3)

print(f"[CLEAR] TEST_VALIDITY=OK snapshots={len(log)} observed={len(observed)}")
if found_surface:
    print("[CLEAR] LOGIN_SURFACE_FORCED=1")
    print("[CLEAR] SUCCESS_SIGNAL=LOGIN_SURFACE_FORCED")
    raise SystemExit(0)

print("[CLEAR] LOGIN_SURFACE_FORCED=0")
print("[CLEAR] FAILURE_SIGNAL=NO_LOGIN_AFTER_CLEAR")
raise SystemExit(21)
