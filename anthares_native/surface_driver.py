#!/usr/bin/env python3
import argparse, json, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path

PKG="com.kwai.video"

def adb(*args, timeout=15):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError("adb")
    return p.stdout

def snapshot(path="/sdcard/anthares.xml"):
    adb("shell","uiautomator","dump",path)
    xml=adb("exec-out","cat",path)
    return list(ET.fromstring(xml).iter("node"))

def rid(n): return (n.get("resource-id") or "").split("/")[-1].casefold()
def label(n): return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold()
def bounds(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds") or "")
    return tuple(map(int,m.groups())) if m else None

def center(n):
    b=bounds(n)
    if not b:return None
    x1,y1,x2,y2=b; return ((x1+x2)//2,(y1+y2)//2)
def tap(n):
    p=center(n)
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(3);return True

def foreground_kwai():
    try:
        w=adb("shell","dumpsys","window","windows")
        return PKG in w
    except Exception:return False

def auth_surface(ns):
    ids=[rid(n) for n in ns]
    strong={"login_container","login_content_container","platform_list","login_platform_expand_text","signin_fre_continue_button"}
    if any(x in strong for x in ids): return True
    loginish=[x for x in ids if any(k in x for k in ("login","signin","sign_in"))]
    editable=sum(1 for n in ns if (n.get("class") or "").endswith("EditText"))
    return len(set(loginish)) >= 2 or (editable >= 1 and len(loginish) >= 1)

def explicit_pick(ns):
    exact=("signin_fre_continue_button","login_platform_expand_text","tv_login","btn_login","tv_to_login","btn_to_login","ll_profile","tab_profile","btn_profile")
    byid={rid(n):n for n in ns}
    for k in exact:
        if k in byid:return byid[k],k
    for n in ns:
        r=rid(n)
        if any(k in r for k in ("login","signin","sign_in")) and n.get("clickable") == "true":
            return n,"id-login-like"
    wanted=("log in","login","sign in","entrar","fazer login","profile","perfil","me","eu")
    for n in ns:
        t=label(n)
        if t in wanted:return n,"semantic-exact"
        if any(x in t for x in ("log in","sign in","fazer login","entrar","perfil","profile")) and n.get("clickable") == "true":
            return n,"semantic-contained"
    return None,None

def bottom_profile_candidate(ns):
    # Last-resort bounded heuristic derived from the repeatedly observed Kwai
    # bottom navigation: only clickable nodes in the lower-right quarter.
    candidates=[]
    for n in ns:
        if n.get("clickable") != "true": continue
        b=bounds(n)
        if not b: continue
        x1,y1,x2,y2=b
        if x1 >= 700 and y1 >= 1300 and x2 <= 1200 and y2 <= 2400:
            area=max(1,(x2-x1)*(y2-y1)); candidates.append((x1,y1,area,n))
    if not candidates:return None,None
    candidates.sort(key=lambda z:(-z[0],-z[1],z[2]))
    return candidates[0][3],"bounded-bottom-right"

def safe_signature(ns):
    return tuple(sorted((rid(n),(n.get("class") or ""),n.get("clickable") or "") for n in ns))

def safe_ids(ns):
    out=[]
    for n in ns:
        r=rid(n)
        if r and re.fullmatch(r"[a-z0-9_]{1,64}",r): out.append(r)
    return sorted(set(out))[:40]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--attempts",type=int,default=18);ap.add_argument("--output",required=True);a=ap.parse_args()
    result={"schema":"anthares.native.surface.v2","auth_surface_reached":False,"steps":0,"last_action":"none","profile_fallback_used":False,"kwai_foreground":False,"safe_widget_ids":[]}
    seen={}
    for i in range(a.attempts):
        try: ns=snapshot()
        except Exception: break
        result["steps"]=i+1; result["kwai_foreground"]=foreground_kwai(); result["safe_widget_ids"]=safe_ids(ns)
        if auth_surface(ns): result["auth_surface_reached"]=True;result["last_action"]="detected";break
        sig=safe_signature(ns); seen[sig]=seen.get(sig,0)+1
        node,action=explicit_pick(ns)
        if node is None and result["kwai_foreground"] and not result["profile_fallback_used"]:
            node,action=bottom_profile_candidate(ns)
            if node is not None: result["profile_fallback_used"]=True
        if node is None:
            # One bounded recovery: relaunch Kwai, never traverse system/account UI.
            if seen[sig] >= 2: break
            try:
                adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(4)
            except Exception: break
            result["last_action"]="relaunch"
            continue
        if not tap(node): break
        result["last_action"]=action
        # Do not stop immediately on an identical tree: animated/native panels can
        # retain their previous hierarchy for one sampling interval.
        time.sleep(2)
    Path(a.output).write_text(json.dumps(result,sort_keys=True)+"\n")
    print("ANTHARES_SURFACE="+("AUTH" if result["auth_surface_reached"] else "UNREACHED"))
    print("ANTHARES_SURFACE_STEPS="+str(result["steps"]))
    print("ANTHARES_SURFACE_LAST_ACTION="+result["last_action"])
    print("ANTHARES_SURFACE_PROFILE_FALLBACK="+("1" if result["profile_fallback_used"] else "0"))
    print("ANTHARES_SURFACE_SAFE_IDS="+",".join(result["safe_widget_ids"]))
    raise SystemExit(0 if result["auth_surface_reached"] else 3)
if __name__=="__main__": main()
