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
 if "profile" in t and ("home" in t or "discover" in t):return "MAIN"
 if "choose like or dislike" in t:return "INTEREST"
 if "pixel launcher isn't responding" in t:return "LAUNCHER_ANR"
 return "OTHER"
adb("shell","pm","grant","com.kwai.video","android.permission.POST_NOTIFICATIONS")
last=None
for i in range(45):
 ns,t=snap();s=state(ns,t);print(f"FSM {i} STATE={s} UI={t[:500]}")
 if s=="MAIN":
  print("FSM_MAIN_REACHED");break
 if s=="PERMISSION":
  n=rid(ns,"permission_deny_button") or rid(ns,"permission_allow_button")
  if n:tap(n)
 elif s=="START":
  n=rid(ns,"tiny_discovery_left_operation_btn")
  if n:tap(n)
  ns2,t2=snap()
  if state(ns2,t2)=="START":
   adb("shell","am","force-stop","com.kwai.video");time.sleep(1);adb("shell","monkey","-p","com.kwai.video","1");time.sleep(7)
 elif s=="INTEREST":
  n=rid(ns,"tiny_discovery_dislike_button") or rid(ns,"tiny_discovery_like_button")
  if n:tap(n)
  else:adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
 elif s=="LAUNCHER_ANR":
  print("LAUNCHER_RECOVERY_BEGIN")
  n=rid(ns,"aerr_close") or rid(ns,"aerr_wait")
  if n:tap(n)
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
if n: tap(n);time.sleep(4)
ns,t=snap();print("POST_PROFILE_UI="+t[:1800]);print("POST_PROFILE_IDS="+" ".join(n.attrib.get("resource-id","") for n in ns)[:4000])
