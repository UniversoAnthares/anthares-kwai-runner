#!/usr/bin/env python3
"""Anthares-owned native entry resolver for Kwai login surfaces.
Uses Android package-manager-resolvable VIEW intents first, then an exact nav-safe
Kwai profile-tab entry. No credentials, no bypass, no legacy helpers.
"""
import json, subprocess, time
from pathlib import Path
PKG="com.kwai.video"
URIS=("kwai://login","kwai://account/login","kwai://account/signin","kwai://signin")
def run(*args,timeout=12):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    return p.returncode,p.stdout.strip()
def main():
    out={"schema":"anthares.native.direct-entry.v2","resolved":False,"started":False,"route_index":-1,"profile_fallback":False}
    for i,uri in enumerate(URIS):
        rc,res=run("shell","cmd","package","resolve-activity","--brief","-a","android.intent.action.VIEW","-d",uri)
        if rc or PKG not in res:continue
        out["resolved"]=True;out["route_index"]=i
        rc,_=run("shell","am","start","-W","-a","android.intent.action.VIEW","-d",uri,"-p",PKG,timeout=20)
        if rc==0:
            out["started"]=True;time.sleep(4);break
    if not out["started"]:
        p=subprocess.run(["python3","-m","anthares_native.profile_entry"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=25)
        out["profile_fallback"]=True
        for line in p.stdout.splitlines():
            if line.startswith("ANTHARES_PROFILE_ENTRY_"):print(line)
    Path("anthares-native-direct-entry.json").write_text(json.dumps(out,sort_keys=True)+"\n")
    print("ANTHARES_DIRECT_ENTRY_RESOLVED="+("1" if out["resolved"] else "0"));print("ANTHARES_DIRECT_ENTRY_STARTED="+("1" if out["started"] else "0"));print("ANTHARES_DIRECT_ENTRY_PROFILE_FALLBACK="+("1" if out["profile_fallback"] else "0"))
    return 0
if __name__=="__main__":raise SystemExit(main())
