#!/usr/bin/env python3
"""Resilient, bounded Kwai login-surface recovery.
Uses only explicit Kwai controls observed in prior QA. Never handles credentials,
CAPTCHA, verification challenges, or unknown-coordinate consent actions.
"""
import hashlib, os, re, subprocess, sys, time, xml.etree.ElementTree as ET
sys.path.insert(0, "tools")
from kwai_login_ui_locator import native_chooser_visible, email_form_visible

CAPTURE=os.environ.get("KWAI_CAPTURE_MODE","retry")
ROUTE=os.environ.get("KWAI_ROUTE_MODE","auto")
SETTLE=int(os.environ.get("KWAI_SETTLE_SECONDS","2"))


def run(*args, check=True, timeout=25):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=timeout,check=check)

def adb(*args):
    return run(*args).stdout

def dump_once(compressed=False):
    path="/sdcard/kwai-recover-v2.xml"
    cmd=["shell","uiautomator","dump"]
    if compressed: cmd.append("--compressed")
    cmd.append(path)
    run(*cmd,timeout=30)
    raw=adb("exec-out","cat",path)
    root=ET.fromstring(raw)
    return raw.decode("utf-8",errors="replace"), list(root.iter("node"))

def snap():
    attempts=[]
    if CAPTURE=="normal": attempts=[False,False,False]
    elif CAPTURE=="compressed": attempts=[True,True,True]
    else: attempts=[False,True,False,True,False,True]
    last=None
    for i,compressed in enumerate(attempts):
        try:
            return dump_once(compressed)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError) as e:
            last=e
            print(f"KWAI_V2_DUMP_RETRY={i+1} COMPRESSED={int(compressed)}")
            time.sleep(2)
    if CAPTURE=="relaunch":
        try:
            run("shell","am","force-stop","com.kwai.video",check=False)
            time.sleep(2)
            run("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1",check=False)
            time.sleep(8)
            for compressed in (False,True,False,True):
                try:return dump_once(compressed)
                except (subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError):time.sleep(2)
        except Exception:
            pass
    raise last or RuntimeError("ui dump unavailable")

def bounds(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds") or "")
    if not m:return None
    a,b,c,d=map(int,m.groups())
    return ((a+c)//2,(b+d)//2)

def tap(n,label):
    p=bounds(n)
    if not p:return False
    run("shell","input","tap",str(p[0]),str(p[1]),check=False)
    print("KWAI_V2_ACTION="+label)
    time.sleep(max(2,SETTLE))
    return True

def rid(n): return (n.get("resource-id") or "").split("/")[-1]
def tag(n): return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold()
def find_id(ns,*ids):
    want=set(ids)
    return next((n for n in ns if rid(n) in want),None)
def find_label(ns,*labels):
    want={x.casefold() for x in labels}
    return next((n for n in ns if tag(n) in want),None)

def choose(ns):
    # First-run interest chooser observed across failed QA runs.
    n=find_id(ns,"bt_interest_skip_top_right")
    if n and ROUTE in {"auto","interest-first","profile-first","login-first","direct-bottom"}:
        return tap(n,"skip_interest")

    # Kwai-owned first-run continuation only; no unknown consent/security taps.
    n=find_id(ns,"signin_fre_continue_button")
    if n:return tap(n,"signin_fre_continue")

    # Existing home builds expose a direct Log In radio/button.
    if ROUTE in {"auto","login-first","interest-first"}:
        n=find_id(ns,"irb_radioButton","tv_login","btn_login","tv_to_login","btn_to_login") or find_label(ns,"log in","login","sign in","entrar","fazer login","log in / sign up","log in or sign up")
        if n:return tap(n,"direct_login")

    # Stable bottom navigation ID observed in passing foreground runs.
    if ROUTE in {"auto","profile-first","direct-bottom","interest-first"}:
        n=find_id(ns,"id_home_bottom_tab_me","ll_profile","tab_profile","btn_profile")
        if n:return tap(n,"profile_tab")
        n=find_label(ns,"profile","perfil","me","eu")
        if n:return tap(n,"profile_label")

    # Once profile is visible, login may appear there.
    n=find_id(ns,"irb_radioButton","tv_login","btn_login","tv_to_login","btn_to_login") or find_label(ns,"log in","login","sign in","entrar","fazer login","log in / sign up","log in or sign up")
    if n:return tap(n,"profile_login")

    # Expand exact native login-platform selector.
    n=find_id(ns,"login_platform_expand_text")
    if n:return tap(n,"expand_login_platforms")
    return False

# Preflight: keep Android connectivity enabled without claiming Internet success.
run("shell","cmd","connectivity","airplane-mode","disable",check=False)
run("shell","svc","wifi","enable",check=False)
time.sleep(SETTLE)

seen={}
for step in range(30):
    try:
        xml,ns=snap()
    except Exception:
        print("KWAI_V2_UI_UNAVAILABLE")
        raise SystemExit(3)
    if email_form_visible(ns) or native_chooser_visible(ns,xml):
        print("KWAI_V2_LOGIN_SURFACE_READY")
        raise SystemExit(0)
    shape="|".join(sorted((n.get("resource-id") or "")+":"+(n.get("class") or "") for n in ns))
    digest=hashlib.sha256(shape.encode()).hexdigest()[:12]
    seen[digest]=seen.get(digest,0)+1
    ids=sorted({rid(n) for n in ns if rid(n)})
    print(f"KWAI_V2_STEP={step} SHAPE={digest} COUNT={seen[digest]} NODE_COUNT={len(ns)}")
    if not choose(ns):
        safe=[x for x in ids if re.fullmatch(r"[A-Za-z0-9_]{1,64}",x)]
        print("KWAI_V2_WIDGET_IDS="+",".join(safe[:80]))
        # Allow dynamic modules/network state to settle before declaring a loop.
        if seen[digest] < 3:
            time.sleep(max(3,SETTLE))
            continue
        print("KWAI_V2_NO_SAFE_ROUTE")
        break
    if seen[digest] >= 6:
        print("KWAI_V2_STATE_LOOP="+digest)
        break
print("KWAI_V2_LOGIN_SURFACE_NOT_REACHED")
raise SystemExit(3)
