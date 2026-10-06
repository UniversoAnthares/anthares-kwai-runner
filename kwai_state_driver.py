#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re,os
def adb(*a):return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20).stdout
def snap():
 adb("shell","uiautomator","dump","/sdcard/s.xml");x=adb("shell","cat","/sdcard/s.xml")
 try:r=ET.fromstring(x)
 except:return [],""
 ns=list(r.iter("node")); t=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower() for n in ns);return ns,t
def ctr(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "");return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tap(n):
 p=ctr(n.attrib.get("bounds")); 
 if p: adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
def rid(ns,s):
 for n in ns:
  if n.attrib.get("resource-id","").endswith(s):return n
def state(ns,t):
 if "permissioncontroller" in " ".join(n.attrib.get("resource-id","") for n in ns):return "PERMISSION"
 if "start now" in t or "you’re all set" in t or "you're all set" in t:return "START"
 if "resource downloading" in t:return "RESOURCE_LOADING"
 if "profile" in t and ("home" in t or "discover" in t):return "MAIN"
 if "choose like or dislike" in t:return "INTEREST"
 if "select your interests" in t and ("skip" in t or "selected and continue" in t):return "INTEREST_SELECT"
 if "pixel launcher isn't responding" in t:return "LAUNCHER_ANR"
 return "OTHER"
adb("shell","pm","grant","com.kwai.video","android.permission.POST_NOTIFICATIONS")
last=None
for i in range(45):
 ns,t=snap();s=state(ns,t);print(f"FSM {i} STATE={s} UI={t[:500]}")
 if s=="MAIN":
  print("FSM_MAIN_REACHED");break
 if s=="PERMISSION":
  n=rid(ns,"permission_deny_button")
  if n is None: n=rid(ns,"permission_allow_button")
  if n is not None:tap(n)
 elif s=="START":
  n=rid(ns,"tiny_discovery_left_operation_btn")
  if n is not None:tap(n)
  ns2,t2=snap()
  if state(ns2,t2)=="START":
   adb("shell","am","force-stop","com.kwai.video");time.sleep(1);adb("shell","monkey","-p","com.kwai.video","1");time.sleep(7)
 elif s=="INTEREST":
  n=rid(ns,"tiny_discovery_dislike_button")
  if n is None: n=rid(ns,"tiny_discovery_like_button")
  if n is not None:tap(n)
  else:adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
 elif s=="INTEREST_SELECT":
  n=None
  for x in ns:
   label=(x.attrib.get("text","")+" "+x.attrib.get("content-desc","")).strip().lower()
   if label=="skip" or label.startswith("skip "):
    n=x;break
  if n is not None and ctr(n.attrib.get("bounds")): tap(n)
  else:
   print("INTEREST_SELECT_SKIP_NOT_FOUND")
   adb("shell","input","tap","90","250");time.sleep(3)
 elif s=="RESOURCE_LOADING":
  print("RESOURCE_LOADING_WAIT")
  for _ in range(30):
   time.sleep(3);ns2,t2=snap()
   if "resource downloading" not in t2:
    print("RESOURCE_LOADING_CLEARED");break
  else:
   print("RESOURCE_LOADING_TIMEOUT");raise SystemExit(21)
 elif s=="LAUNCHER_ANR":
  print("LAUNCHER_RECOVERY_BEGIN")
  n=rid(ns,"aerr_close")
  if n is None: n=rid(ns,"aerr_wait")
  if n is not None:tap(n)
  adb("shell","input","keyevent","3");time.sleep(4)
  nsr,tr=snap(); print("LAUNCHER_AFTER_HOME="+state(nsr,tr))
  adb("shell","am","force-stop","com.kwai.video");time.sleep(1)
  adb("shell","monkey","-p","com.kwai.video","1");time.sleep(7)
  nsr,tr=snap(); print("LAUNCHER_RECOVERY_STATE="+state(nsr,tr))
 else:
  adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
else:
 print("FSM_TIMEOUT");raise SystemExit(20)
# stabilize main and inspect real clickable Profile parent
adb("shell","am","force-stop","com.kwai.video");time.sleep(1);adb("shell","monkey","-p","com.kwai.video","1");time.sleep(12)
ns,t=snap(); n=rid(ns,"ll_profile"); print("PROFILE_PARENT="+str(bool(n)))
if n is not None: tap(n);time.sleep(4)
ns,t=snap();print("POST_PROFILE_UI="+t[:1800]);print("POST_PROFILE_IDS="+" ".join(n.attrib.get("resource-id","") for n in ns)[:4000])
