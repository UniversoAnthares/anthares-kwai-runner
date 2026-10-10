#!/usr/bin/env python3
"""Bounded, privacy-safe recovery from Kwai feed/profile to native login chooser.
Never dumps UI text or captures credential screens. Exit 0 only if native chooser
or credential form is independently visible; exit 3 on unresolved state.
"""
import hashlib, re, subprocess, sys, time, xml.etree.ElementTree as ET
sys.path.insert(0,"tools")
from kwai_login_ui_locator import native_chooser_visible, email_form_visible

def adb(*args):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=18,check=True).stdout
def snap():
    adb("shell","uiautomator","dump","/sdcard/kwai-recover.xml")
    return list(ET.fromstring(adb("exec-out","cat","/sdcard/kwai-recover.xml")).iter("node"))
def coords(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds") or "")
    if not m:return None
    a,b,c,d=map(int,m.groups());return ((a+c)//2,(b+d)//2)
def tap(n):
    p=coords(n)
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
def tag(n):
    return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold()
def select(ns):
    # Prefer explicit login action before navigating into Profile.
    for n in ns:
        if tag(n) in ("log in","login","sign in","entrar","fazer login","log in / sign up","log in or sign up") and tap(n):
            return "login_label"
    for suffix in ("tv_login","btn_login","tv_to_login","btn_to_login"):
        for n in ns:
            if (n.get("resource-id") or "").endswith(suffix) and tap(n):return suffix
    for suffix in ("ll_profile","tab_profile","btn_profile"):
        for n in ns:
            if (n.get("resource-id") or "").endswith(suffix) and tap(n):
                return suffix
    for n in ns:
        if tag(n) in ("profile","perfil","me","eu") and tap(n):return "profile_label"
    return None
seen=set()
for i in range(8):
    try:ns=snap()
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError):
        print("KWAI_RECOVERY_UI_UNAVAILABLE");raise SystemExit(3)
    if email_form_visible(ns) or native_chooser_visible(ns):
        print("KWAI_RECOVERY_LOGIN_SURFACE_READY");raise SystemExit(0)
    # Fingerprint only resource IDs/classes, never personal data or screen text.
    shape="|".join(sorted((n.get("resource-id") or "")+":"+(n.get("class") or "") for n in ns))
    digest=hashlib.sha256(shape.encode()).hexdigest()[:12]
    if digest in seen:
        print("KWAI_RECOVERY_STATE_LOOP="+digest);break
    seen.add(digest)
    action=select(ns)
    print("KWAI_RECOVERY_STEP="+str(i)+" ACTION="+str(action)+" SHAPE="+digest)
    if action is None:break
    time.sleep(1)
print("KWAI_RECOVERY_CHOOSER_NOT_REACHED")
raise SystemExit(3)
