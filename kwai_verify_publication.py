#!/usr/bin/env python3
import os, re, subprocess, sys, time, xml.etree.ElementTree as ET
TITLE=os.environ.get("KWAI_VIDEO_TITLE","").strip().lower()
def adb(*a):
    return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout
def dump():
    adb("shell","uiautomator","dump","/sdcard/verify.xml"); adb("pull","/sdcard/verify.xml","/tmp/verify.xml")
    root=ET.parse("/tmp/verify.xml").getroot()
    return " ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower() for n in root.iter("node"))
# Navigate to profile.
for _ in range(4):
    try:
        t=dump()
        root=ET.parse("/tmp/verify.xml").getroot()
        for n in root.iter("node"):
            s=(n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()
            if "profile" in s or "perfil" in s:
                m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.attrib.get("bounds",""))
                if m:
                    x1,y1,x2,y2=map(int,m.groups()); adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2)); time.sleep(3)
                break
        break
    except Exception: time.sleep(1)
for _ in range(12):
    try:t=dump()
    except Exception: time.sleep(2); continue
    needle=" ".join(TITLE.split())[:40]
    if needle and needle in " ".join(t.split()):
        print("KWAI_PUBLICATION_TITLE_VERIFIED"); sys.exit(0)
    # A profile grid after successful publish is useful only when the app exposes a fresh-success marker.
    if any(k in t for k in ("published","publicado","just now","agora")):
        print("KWAI_PUBLICATION_MARKER_VERIFIED"); sys.exit(0)
    time.sleep(3)
print("KWAI_PUBLICATION_UNVERIFIED"); sys.exit(1)
