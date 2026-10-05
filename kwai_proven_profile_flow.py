#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def dump(tag):
 adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
 try:return ET.parse(f"{tag}.xml").getroot()
 except:return None
def nodes(r): return list(r.iter("node")) if r is not None else []
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def center(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "")
 return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
# proven adaptive traversal
for i in range(20):
 r=dump(f"flow-{i}"); t=" ".join(lab(n) for n in nodes(r))
 if "profile" in t and ("home" in t or "discover" in t): break
 adb("shell","input","swipe","900","1100","120","1100","350"); time.sleep(1)
# proven stabilization
adb("shell","am","force-stop","com.kwai.video"); time.sleep(2)
adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1"); time.sleep(18)
r=dump("stable-feed"); t=" ".join(lab(n) for n in nodes(r)); print("STABLE_UI="+t[:1600])
# tap Profile by actual node bounds
hit=False
for n in nodes(r):
 if lab(n)=="profile" or " profile" in (" "+lab(n)):
  p=center(n.attrib.get("bounds"))
  if p: adb("shell","input","tap",str(p[0]),str(p[1])); hit=True; break
if not hit: adb("shell","input","tap","960","2200")
time.sleep(5)
r=dump("profile-page"); t=" ".join(lab(n) for n in nodes(r)); print("PROFILE_PAGE_UI="+t[:2500])
with open("profile-page.png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
