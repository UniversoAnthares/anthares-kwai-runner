#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET,re
mode=os.environ["ROUTE_MODE"]
def adb(*a):return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20).stdout
def dump():
 adb("shell","uiautomator","dump","/sdcard/r.xml");adb("pull","/sdcard/r.xml","/tmp/r.xml")
 try:return ET.parse("/tmp/r.xml").getroot()
 except:return None
def ns(r):return list(r.iter("node")) if r is not None else []
def lab(n):return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()
def ctr(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "");return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tapid(s):
 r=dump()
 for n in ns(r):
  if n.attrib.get("resource-id","").endswith(s):
   p=ctr(n.attrib.get("bounds")); 
   if p: adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(3);return True
 return False
for i in range(24):
 r=dump();t=" ".join(lab(n) for n in ns(r))
 if "pixel launcher isn't responding" in t:
  tapid("aerr_wait" if mode=="launcher-wait" else "aerr_close");time.sleep(2)
  if mode=="launcher-close-relaunch":
   adb("shell","monkey","-p","com.kwai.video","1");time.sleep(5)
  continue
 if "start now" in t:
  tapid("tiny_discovery_left_operation_btn");time.sleep(4)
  if mode=="start-now-restart":
   adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","1");time.sleep(8)
  continue
 if "profile" in t and ("home" in t or "discover" in t):break
 adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(.8)
adb("shell","am","force-stop","com.kwai.video");time.sleep(2);adb("shell","monkey","-p","com.kwai.video","1");time.sleep(15)
if mode=="parent-wait10":time.sleep(10)
if mode=="parent-wait30":time.sleep(30)
if mode=="profile-id-restart":
 adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","1");time.sleep(10)
tapid("ll_profile")
if mode=="module-wait60":time.sleep(60)
if mode=="module-hide-reopen":
 time.sleep(20);tapid("btn_cancel");time.sleep(2);tapid("ll_profile");time.sleep(20)
if mode=="parent-restart":
 adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","1");time.sleep(10);tapid("ll_profile")
elif mode=="parent-twice":tapid("ll_profile")
elif mode=="parent-back-parent":adb("shell","input","keyevent","4");time.sleep(2);tapid("ll_profile")
elif mode=="parent-scroll":adb("shell","input","swipe","500","1800","500","600","300");time.sleep(3)
elif mode=="parent-resource-wait":time.sleep(30)
r=dump();t=" ".join(lab(n) for n in ns(r));ids=" ".join(n.attrib.get("resource-id","") for n in ns(r));ed=sum(1 for n in ns(r) if n.attrib.get("editable")=="true" or n.attrib.get("class","").endswith("EditText"))
print("ROUTE_MODE="+mode);print("FINAL_UI="+t[:3000]);print("EDITABLE_COUNT="+str(ed));print("IDS="+ids[:5000])
