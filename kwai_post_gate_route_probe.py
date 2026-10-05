#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET,re
M=os.environ.get("ROUTE_MODE","parent-now")
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def dump(tag):
 adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
 try:return ET.parse(f"{tag}.xml").getroot()
 except:return None
def ns(r): return list(r.iter("node")) if r is not None else []
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def ctr(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or ""); return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tap(n):
 p=ctr(n.attrib.get("bounds"));
 if not p:return False
 adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
def clickid(s,r):
 for n in ns(r):
  if n.attrib.get("resource-id","").endswith(s):
   return tap(n)
 return False
def snap(tag):
 r=dump(tag)
 with open(tag+".png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
 return r
# Traverse all known onboarding gates deterministically.
for i in range(30):
 r=snap(f"postgate-{M}-{i}"); t=" ".join(lab(n) for n in ns(r))
 if "profile" in t and ("home" in t or "discover" in t or "inbox" in t): break
 if clickid("tiny_discovery_left_operation_btn",r): print("GATE=START_NOW"); continue
 if clickid("tiny_discovery_dislike_button",r) or clickid("tiny_discovery_like_button",r): continue
 adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
else:
 print("RESULT=NO_MAIN_NAV"); raise SystemExit(20)
# stabilize if requested
if "restart" in M:
 adb("shell","am","force-stop","com.kwai.video");time.sleep(2);adb("shell","monkey","-p","com.kwai.video","1");time.sleep(15);r=snap("postgate-restarted")
if "wait30" in M: time.sleep(30)
elif "wait15" in M: time.sleep(15)
elif "wait5" in M or M.endswith("-wait"): time.sleep(5)
if M=="parent-home-profile": adb("shell","input","tap","100","2200");time.sleep(2)
elif M=="parent-inbox-profile": adb("shell","input","tap","800","2200");time.sleep(2)
elif M=="parent-discover-profile": adb("shell","input","tap","350","2200");time.sleep(2)
elif M=="parent-back-parent": adb("shell","input","keyevent","4");time.sleep(2)
elif M=="parent-scroll-up": adb("shell","input","swipe","500","1700","500","500","300");time.sleep(2)
elif M=="parent-scroll-down": adb("shell","input","swipe","500","500","500","1700","300");time.sleep(2)
elif M=="parent-keyevent-menu": adb("shell","input","keyevent","82");time.sleep(2)
elif M=="parent-dump-activities": print(adb("shell","dumpsys","activity","activities"))
r=snap("postgate-before-profile")
if M=="parent-coordinate": adb("shell","input","tap","960","2200");time.sleep(4)
else:
 if not clickid("ll_profile",r):
  for n in ns(r):
   if lab(n)=="profile" and tap(n): break
 if M=="parent-twice":
  time.sleep(2); rr=snap("postgate-between"); clickid("ll_profile",rr)
time.sleep(5)
r=snap("postgate-final")
t=" ".join(lab(n) for n in ns(r))
edits=[n for n in ns(r) if n.attrib.get("editable")=="true" or n.attrib.get("class","").endswith("EditText")]
auth=[n for n in ns(r) if any(x in lab(n) for x in ("log in","login","sign in","entrar","phone","telefone","email","account","conta"))]
print("ROUTE_MODE="+M);print("EDITABLES="+str(len(edits)));print("AUTH_CANDIDATES="+str(len(auth)));print("FINAL_UI="+t[:3000])
