#!/usr/bin/env python3
import subprocess, time, xml.etree.ElementTree as ET, re, sys, os

def adb(*a):
    return subprocess.run(["adb", *a], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30).stdout

def dump(tag):
    adb("shell", "uiautomator", "dump", f"/sdcard/{tag}.xml")
    adb("pull", f"/sdcard/{tag}.xml", f"{tag}.xml")
    try:
        return ET.parse(f"{tag}.xml").getroot()
    except:
        return None

def nodes(r):
    return list(r.iter("node")) if r is not None else []

def lab(n):
    return (n.attrib.get("text", "") + " " + n.attrib.get("content-desc", "")).strip().lower()

def center(b):
    m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b or "")
    return ((int(m[1]) + int(m[3])) // 2, (int(m[2]) + int(m[4])) // 2) if m else None

def has_resource_downloading(r):
    t = " ".join(lab(n) for n in nodes(r))
    return "resource downloading" in t or "can't connect to server" in t

def has_main_nav(r):
    t = " ".join(lab(n) for n in nodes(r))
    return "profile" in t and ("home" in t or "discover" in t or "inbox" in t)

def has_login_control(r):
    t = " ".join(lab(n) for n in nodes(r))
    return any(k in t for k in ("log in", "login", "entrar", "sign in", "telefone", "phone", "email", "e-mail", "password", "senha"))

def tap_profile_semantically(r):
    for n in nodes(r):
        if lab(n) == "profile" or " profile" in (" " + lab(n)):
            p = center(n.attrib.get("bounds"))
            if p:
                adb("shell", "input", "tap", str(p[0]), str(p[1]))
                return True
    return False

# 1. Proven adaptive traversal to reach main nav
print("PHASE=ADAPTIVE_TRAVERSAL")
for i in range(20):
    r = dump(f"adaptive-{i}")
    t = " ".join(lab(n) for n in nodes(r))
    print(f"ADAPTIVE_{i}_UI={t[:1600]}")
    if has_main_nav(r):
        print("MAIN_NAV_REACHED")
        break
    adb("shell", "input", "swipe", "900", "1100", "120", "1100", "350")
    time.sleep(1)
else:
    print("CLASSIFICATION=UNEXPECTED_UI")
    print("REASON=Adaptive traversal did not reach main nav")
    sys.exit(1)

# 2. Detect resource downloading gate
r = dump("post-adaptive")
t = " ".join(lab(n) for n in nodes(r))
print(f"POST_ADAPTIVE_UI={t[:1600]}")

if not has_resource_downloading(r):
    print("NO_RESOURCE_GATE")
else:
    print("RESOURCE_DOWNLOADING_DETECTED")
    # 3. Wait for resource downloading to disappear with timeout and polling
    print("PHASE=WAIT_RESOURCE_GATE")
    timeout = 60
    interval = 3
    start = time.time()
    while time.time() - start < timeout:
        r = dump(f"gate-wait-{int(time.time()-start)}")
        t = " ".join(lab(n) for n in nodes(r))
        if not has_resource_downloading(r):
            print(f"RESOURCE_GATE_CLEARED_AFTER={int(time.time()-start)}s")
            print(f"GATE_CLEARED_UI={t[:1600]}")
            break
        print(f"WAITING_RESOURCE_GATE... ({int(time.time()-start)}s) UI={t[:200]}")
        time.sleep(interval)
    else:
        r = dump("gate-timeout")
        t = " ".join(lab(n) for n in nodes(r))
        print(f"RESOURCE_DOWNLOAD_TIMEOUT UI={t[:1600]}")
        print("CLASSIFICATION=RESOURCE_DOWNLOAD_TIMEOUT")
        sys.exit(1)

# 4. Capture XML+screenshot when download finishes
r = dump("post-gate")
t = " ".join(lab(n) for n in nodes(r))
print(f"POST_GATE_UI={t[:1600]}")
with open("post-gate.png", "wb") as f:
    subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, timeout=20)

# 5. Verify main nav still present
if not has_main_nav(r):
    print("MAIN_NAV_LOST_AFTER_GATE")
    print("CLASSIFICATION=UNEXPECTED_UI")
    sys.exit(1)

# 6. Tap Profile semantically
print("PHASE=TAP_PROFILE")
if not tap_profile_semantically(r):
    print("PROFILE_TAP_FAILED")
    print("CLASSIFICATION=UNEXPECTED_UI")
    sys.exit(1)
time.sleep(4)

# 7. Capture XML+screenshot after Profile tap
r = dump("profile-page")
t = " ".join(lab(n) for n in nodes(r))
print(f"PROFILE_PAGE_UI={t[:2500]}")
with open("profile-page.png", "wb") as f:
    subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, timeout=20)

# 8. Classify explicitly
if has_login_control(r):
    print("CLASSIFICATION=LOGIN_CONTROL_FOUND")
    sys.exit(0)
elif has_main_nav(r):
    print("CLASSIFICATION=PROFILE_OPEN_NO_LOGIN")
    sys.exit(0)
else:
    print("CLASSIFICATION=UNEXPECTED_UI")
    sys.exit(1)