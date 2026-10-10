#!/usr/bin/env python3
import argparse, json, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path

def adb(*args, timeout=15):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError("adb")
    return p.stdout

def snapshot(path="/sdcard/anthares.xml"):
    adb("shell","uiautomator","dump",path)
    xml=adb("exec-out","cat",path)
    return list(ET.fromstring(xml).iter("node"))

def rid(n): return (n.get("resource-id") or "").split("/")[-1]
def label(n): return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold()
def center(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds") or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2)
def tap(n):
    p=center(n)
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(3);return True

def auth_surface(ns):
    ids={rid(n) for n in ns}
    strong={"login_container","login_content_container","platform_list","login_platform_expand_text","signin_fre_continue_button"}
    return bool(ids & strong)

def pick(ns):
    exact_ids=("signin_fre_continue_button","login_platform_expand_text","tv_login","btn_login","tv_to_login","btn_to_login","ll_profile","tab_profile","btn_profile")
    ids={rid(n):n for n in ns}
    for k in exact_ids:
        if k in ids:return ids[k],k
    wanted={"log in","login","sign in","entrar","fazer login","profile","perfil","me","eu"}
    for n in ns:
        if label(n) in wanted:return n,"semantic"
    return None,None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--attempts",type=int,default=18);ap.add_argument("--output",required=True);a=ap.parse_args()
    result={"schema":"anthares.native.surface.v1","auth_surface_reached":False,"steps":0,"last_action":"none"}
    seen=set()
    for i in range(a.attempts):
        try: ns=snapshot()
        except Exception: break
        result["steps"]=i+1
        if auth_surface(ns):
            result["auth_surface_reached"]=True;result["last_action"]="detected";break
        shape=tuple(sorted((rid(n),n.get("class") or "") for n in ns))
        if shape in seen: break
        seen.add(shape)
        node,action=pick(ns)
        if node is None:
            adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(2)
            try:
                ns=snapshot()
                node,action=pick(ns)
            except Exception: node=None
        if node is None: break
        if not tap(node): break
        result["last_action"]=action
    Path(a.output).write_text(json.dumps(result,sort_keys=True)+"\n")
    print("ANTHARES_SURFACE="+("AUTH" if result["auth_surface_reached"] else "UNREACHED"))
    raise SystemExit(0 if result["auth_surface_reached"] else 3)
if __name__=="__main__": main()
