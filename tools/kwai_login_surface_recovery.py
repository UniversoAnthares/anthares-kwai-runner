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
    # Observed first-run experience (run 38082791155): after expanding
    # login platforms, Kwai launches its own FRE consent/continuation screen.
    # Advance only the exact native Continue control, never consent by
    # guessing coordinates or dismiss a security challenge.
    for n in ns:
        if (n.get("resource-id") or "").endswith("/signin_fre_continue_button") and tap(n):
            return "native_first_run_continue"
    # Prefer explicit login action before navigating into Profile.
    for n in ns:
        if tag(n) in ("log in","login","sign in","entrar","fazer login","log in / sign up","log in or sign up") and tap(n):
            return "login_label"
    for suffix in ("tv_login","btn_login","tv_to_login","btn_to_login"):
        for n in ns:
            if (n.get("resource-id") or "").endswith(suffix) and tap(n):return suffix
    # Observed live login surface exposes a collapsed platform selector without
    # an Email label (run 38081779193). Expand it before looking for the chooser.
    # Only exact Kwai login widget IDs are eligible, never arbitrary screen taps.
    for suffix in ("login_platform_expand_text",):
        for n in ns:
            if (n.get("resource-id") or "").endswith("/"+suffix) and tap(n):
                return "expand_native_login_platforms"
    for suffix in ("ll_profile","tab_profile","btn_profile"):
        for n in ns:
            if (n.get("resource-id") or "").endswith(suffix) and tap(n):
                return suffix
    for n in ns:
        if tag(n) in ("profile","perfil","me","eu") and tap(n):return "profile_label"
    return None
seen=set()
system_waits=0
app_relaunches=0
native_error_waits=0
for i in range(22):
    try:ns=snap()
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError):
        print("KWAI_RECOVERY_UI_UNAVAILABLE");raise SystemExit(3)
    # Android SetupWizard may display an asynchronous "minute_maid"
    # progress interstitial after the native first-run Continue action.
    # Wait for its completion without interacting with security dialogs.
    ids={(n.get("resource-id") or "").split("/")[-1] for n in ns}
    if "minute_maid" in ids and ("progress_bar_layout" in ids or "sud_layout_template_content" in ids):
        if system_waits >= 12:
            # The Google SetupWizard interstitial is not Kwai's login UI.
            # Capture only its Android package identity (no screen text).
            try:
                focus=adb("shell","dumpsys","window","windows").decode(errors="replace")
                m=re.search(r"mCurrentFocus[^\\n]*?([a-zA-Z][a-zA-Z0-9_.]+)/(?:[a-zA-Z0-9_.$]+)",focus)
                print("KWAI_RECOVERY_STALLED_FOREGROUND_PACKAGE="+(m.group(1) if m else "unknown"))
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
                print("KWAI_RECOVERY_STALLED_FOREGROUND_PACKAGE=unavailable")
            # A Google setup interstitial can stall indefinitely on an
            # ephemeral emulator. Return HOME and relaunch the *installed*
            # Kwai package once; never click through account/security UI.
            if app_relaunches:
                print("KWAI_RECOVERY_SYSTEM_SETUP_TIMEOUT");break
            app_relaunches+=1
            print("KWAI_RECOVERY_APP_RELAUNCH_AFTER_SETUP_STALL=1")
            try:
                adb("shell","input","keyevent","KEYCODE_HOME")
                time.sleep(2)
                adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
                time.sleep(6)
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
                print("KWAI_RECOVERY_APP_RELAUNCH_FAILED");break
            system_waits=0
            seen.clear()
            continue
        system_waits+=1
        print("KWAI_RECOVERY_SYSTEM_SETUP_WAIT="+str(system_waits))
        time.sleep(5)
        continue
    # Observed on real Android run 38086491351: the Kwai-owned alert
    # aerr_wait/aerr_close blocked every profile/login control. Wait only
    # once through the explicit app-owned wait action; never accept consent,
    # dismiss security challenges, or tap unknown geometry.
    if {"aerr_wait", "aerr_close"}.issubset(ids) and native_error_waits < 1:
        wait_nodes=[n for n in ns if (n.get("resource-id") or "").endswith("/aerr_wait")]
        if wait_nodes and tap(wait_nodes[0]):
            native_error_waits+=1
            print("KWAI_RECOVERY_NATIVE_ERROR_WAIT=1")
            time.sleep(6)
            continue
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
    if action is None:
        # Public widget identifiers only; never emit UI text or credential values.
        ids=sorted(set((n.get("resource-id") or "").split("/")[-1] for n in ns if n.get("resource-id")))
        safe=[x for x in ids if re.fullmatch(r"[a-zA-Z0-9_]{1,64}",x)]
        print("KWAI_RECOVERY_WIDGET_IDS="+",".join(safe[:65]))
        print("KWAI_RECOVERY_NODE_COUNT="+str(len(ns)))
        break
    time.sleep(1)
print("KWAI_RECOVERY_CHOOSER_NOT_REACHED")
raise SystemExit(3)
