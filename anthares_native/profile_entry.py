#!/usr/bin/env python3
"""Open the exact Kwai profile tab at a nav-safe point.
Avoids the Android navigation strip by targeting the upper quarter of the widget.
"""
import json,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
PKG="com.kwai.video"; TARGET="id_home_bottom_tab_me"
def run(*a,timeout=12):
 p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
 return p.returncode,p.stdout
def main():
 out={"schema":"anthares.native.profile-entry.v1","found":False,"tapped":False,"kwai_after":False}
 rc,_=run("shell","uiautomator","dump","--compressed","/sdcard/anthares-profile.xml")
 if rc: Path("anthares-native-profile-entry.json").write_text(json.dumps(out)+"\n"); return 0
 rc,xml=run("exec-out","cat","/sdcard/anthares-profile.xml")
 if rc:return 0
 try:nodes=list(ET.fromstring(xml).iter("node"))
 except ET.ParseError:return 0
 node=next((n for n in nodes if (n.get("resource-id") or "").split("/")[-1]==TARGET),None)
 if node is None:return 0
 out["found"]=True
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",node.get("bounds") or "")
 if not m:return 0
 x1,y1,x2,y2=map(int,m.groups());x=(x1+x2)//2;y=y1+max(2,(y2-y1)//4)
 # Query physical size and clamp above Android's lower navigation region.
 _,size=run("shell","wm","size"); sm=re.search(r"(\d+)x(\d+)",size)
 if sm:y=min(y,int(sm.group(2))*88//100)
 rc,_=run("shell","input","tap",str(x),str(y))
 out["tapped"]=rc==0;time.sleep(4)
 _,win=run("shell","dumpsys","window","windows");out["kwai_after"]=PKG in win
 Path("anthares-native-profile-entry.json").write_text(json.dumps(out,sort_keys=True)+"\n")
 print("ANTHARES_PROFILE_ENTRY_FOUND="+("1" if out["found"] else "0"))
 print("ANTHARES_PROFILE_ENTRY_TAPPED="+("1" if out["tapped"] else "0"))
 print("ANTHARES_PROFILE_ENTRY_KWAI_AFTER="+("1" if out["kwai_after"] else "0"))
 return 0
if __name__=="__main__":raise SystemExit(main())
