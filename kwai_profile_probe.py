#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET,re
mode=os.environ.get("PROFILE_MODE","profile-text")
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20).stdout
def dump(tag):
    adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
    try:return ET.parse(f"{tag}.xml").getroot()
    except:return None
def nodes(root): return list(root.iter("node")) if root is not None else []
def label(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def center(b):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "")
    return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tap_node(n):
    p=center(n.attrib.get("bounds")); 
    if p: adb("shell","input","tap",str(p[0]),str(p[1])); time.sleep(2); return True
    return False
# Proven adaptive traversal: advance cards until bottom navigation/feed appears.
for i in range(12):
    r=dump(f"stage-{i}"); t=" ".join(label(n) for n in nodes(r))
    if "profile" in t and ("home" in t or "discover" in t): break
    adb("shell","input","swipe","850","1100","180","1100","250"); time.sleep(1)
r=dump("before-profile")
if mode=="profile-text":
    for n in nodes(r):
        if "profile" in label(n) and tap_node(n): break
elif mode=="profile-coordinate": adb("shell","input","tap","960","2200"); time.sleep(3)
elif mode=="me-coordinate": adb("shell","input","tap","970","2140"); time.sleep(3)
elif mode=="back-then-profile":
    adb("shell","input","keyevent","4"); time.sleep(1); adb("shell","input","tap","960","2200"); time.sleep(3)
elif mode=="profile-twice":
    adb("shell","input","tap","960","2200"); time.sleep(2); adb("shell","input","tap","960","2200"); time.sleep(2)
elif mode=="profile-deeplink": adb("shell","am","start","-a","android.intent.action.VIEW","-d","kwai://profile","com.kwai.video"); time.sleep(3)
elif mode=="login-deeplink": adb("shell","am","start","-a","android.intent.action.VIEW","-d","kwai://login","com.kwai.video"); time.sleep(3)
elif mode=="inbox": adb("shell","input","tap","800","2200"); time.sleep(3)
elif mode=="discover": adb("shell","input","tap","300","2200"); time.sleep(3)
elif mode=="inspect-profile":
    print(adb("shell","dumpsys","activity","activities"))
r=dump("after-"+mode); t=" ".join(label(n) for n in nodes(r))
print("PROFILE_MODE="+mode); print("PROFILE_UI="+t[:2500])
with open("profile-"+mode+".png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
