#!/usr/bin/env python3
import argparse, json, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path
PKG="com.kwai.video"
def adb(*args, timeout=15):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError("adb")
    return p.stdout
def snapshot(path="/sdcard/anthares.xml"):
    last=None
    for _ in range(6):
        try:
            # File-based dump is more stable on hosted emulators than /dev/tty.
            adb("shell","uiautomator","dump","--compressed",path,timeout=12)
            xml=adb("exec-out","cat",path,timeout=8)
            root=ET.fromstring(xml)
            nodes=list(root.iter("node"))
            if nodes:return nodes
        except Exception as exc:
            last=exc
        time.sleep(2)
    raise RuntimeError("uiautomator_snapshot_unavailable") from last
def fullrid(n): return (n.get("resource-id") or "").casefold()
def rid(n): return fullrid(n).split("/")[-1]
def label(n): return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold()
def bounds(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds") or ""); return tuple(map(int,m.groups())) if m else None
def center(n):
    b=bounds(n)
    if not b:return None
    x1,y1,x2,y2=b; return ((x1+x2)//2,(y1+y2)//2)
def tap(n):
    p=center(n)
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(3);return True
def foreground_kwai():
    try:return PKG in adb("shell","dumpsys","window","windows")
    except Exception:return False
def kwai_tree(ns): return any(PKG in fullrid(n) for n in ns)
def auth_surface(ns):
    ids=[rid(n) for n in ns]; strong={"login_container","login_content_container","platform_list","login_platform_expand_text","signin_fre_continue_button"}
    if any(x in strong for x in ids):return True
    loginish=[x for x in ids if any(k in x for k in ("login","signin","sign_in"))]
    editable=sum(1 for n in ns if (n.get("class") or "").endswith("EditText"))
    return len(set(loginish))>=2 or (editable>=1 and len(loginish)>=1)
def explicit_pick(ns):
    exact=("signin_fre_continue_button","login_platform_expand_text","tv_login","btn_login","tv_to_login","btn_to_login","id_home_bottom_tab_me","ll_profile","tab_profile","btn_profile")
    byid={rid(n):n for n in ns}
    for k in exact:
        if k in byid:return byid[k],k
    for n in ns:
        r=rid(n)
        if any(k in r for k in ("login","signin","sign_in")) and n.get("clickable")=="true":return n,"id-login-like"
    for n in ns:
        r=rid(n)
        if ("profile" in r or r.endswith("_me")) and not any(x in r for x in ("avatar","photo","header","title","edit","follow","setting","name","info")):
            b=bounds(n)
            if b:return n,"id-profile-like"
    wanted=("log in","login","sign in","entrar","fazer login","profile","perfil","me","eu")
    for n in ns:
        t=label(n)
        if t in wanted:return n,"semantic-exact"
        if any(x in t for x in ("log in","sign in","fazer login","entrar","perfil","profile")) and n.get("clickable")=="true":return n,"semantic-contained"
    return None,None
def bottom_profile_candidate(ns):
    if not kwai_tree(ns):return None,None
    bs=[bounds(n) for n in ns if bounds(n)]
    if not bs:return None,None
    width=max(b[2] for b in bs);height=max(b[3] for b in bs);candidates=[]
    for n in ns:
        if n.get("clickable")!="true":continue
        b=bounds(n)
        if not b:continue
        x1,y1,x2,y2=b;cx=(x1+x2)//2;cy=(y1+y2)//2
        if cx>=width*.72 and height*.76<=cy<=height*.94 and (x2-x1)<=width*.32:candidates.append((cx,cy,-((x2-x1)*(y2-y1)),n))
    if not candidates:return None,None
    candidates.sort(reverse=True,key=lambda z:(z[0],z[1],z[2]));return candidates[0][3],"bounded-kwai-bottom-right"
def safe_signature(ns): return tuple(sorted((rid(n),(n.get("class") or ""),n.get("clickable") or "") for n in ns))
def safe_ids(ns):
    out=[]
    for n in ns:
        r=rid(n)
        if r and re.fullmatch(r"[a-z0-9_]{1,64}",r):out.append(r)
    return sorted(set(out))[:60]
def relaunch():
    adb("shell","am","force-stop",PKG);time.sleep(1);adb("shell","monkey","-p",PKG,"1");time.sleep(5)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--attempts",type=int,default=18);ap.add_argument("--output",required=True);a=ap.parse_args()
    result={"schema":"anthares.native.surface.v4","auth_surface_reached":False,"steps":0,"last_action":"none","profile_fallback_used":False,"kwai_foreground":False,"kwai_tree":False,"safe_widget_ids":[],"snapshot_failures":0}
    seen={};relaunches=0
    for i in range(a.attempts):
        try:ns=snapshot()
        except Exception:
            result["snapshot_failures"]+=1
            if relaunches>=2:break
            try:relaunch();relaunches+=1;result["last_action"]="snapshot-relaunch";continue
            except Exception:break
        result["steps"]=i+1;result["kwai_foreground"]=foreground_kwai();result["kwai_tree"]=kwai_tree(ns);result["safe_widget_ids"]=safe_ids(ns)
        if auth_surface(ns):result["auth_surface_reached"]=True;result["last_action"]="detected";break
        sig=safe_signature(ns);seen[sig]=seen.get(sig,0)+1
        node,action=explicit_pick(ns)
        if node is None and result["kwai_foreground"] and result["kwai_tree"] and not result["profile_fallback_used"]:
            node,action=bottom_profile_candidate(ns)
            if node is not None:result["profile_fallback_used"]=True
        if node is None:
            if relaunches>=2 or seen[sig]>=3:break
            try:relaunch();relaunches+=1;result["last_action"]="fresh-relaunch";continue
            except Exception:break
        if not tap(node):break
        if action.startswith("bounded") and not foreground_kwai():
            try:relaunch();relaunches+=1;result["last_action"]="reject-profile-candidate";continue
            except Exception:break
        result["last_action"]=action;time.sleep(2)
    Path(a.output).write_text(json.dumps(result,sort_keys=True)+"\n")
    print("ANTHARES_SURFACE="+("AUTH" if result["auth_surface_reached"] else "UNREACHED"));print("ANTHARES_SURFACE_STEPS="+str(result["steps"]));print("ANTHARES_SURFACE_LAST_ACTION="+result["last_action"]);print("ANTHARES_SURFACE_PROFILE_FALLBACK="+("1" if result["profile_fallback_used"] else "0"));print("ANTHARES_SURFACE_KWAI_TREE="+("1" if result["kwai_tree"] else "0"));print("ANTHARES_SURFACE_SNAPSHOT_FAILURES="+str(result["snapshot_failures"]));print("ANTHARES_SURFACE_SAFE_IDS="+",".join(result["safe_widget_ids"]))
    raise SystemExit(0 if result["auth_surface_reached"] else 3)
if __name__=="__main__":main()
