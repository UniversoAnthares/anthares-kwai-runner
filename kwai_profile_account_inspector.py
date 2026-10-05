#!/usr/bin/env python3
import subprocess,time,re,xml.etree.ElementTree as ET
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def snap(tag):
 adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
 with open(tag+".png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
 try:return ET.parse(f"{tag}.xml").getroot()
 except:return None
def ns(r): return list(r.iter("node")) if r is not None else []
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def center(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "")
 return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tap(n):
 p=center(n.attrib.get("bounds",""))
 if not p:return False
 adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
def clickid(s,r):
 for n in ns(r):
  if n.attrib.get("resource-id","").endswith(s): return tap(n)
 return False
# Proven gate traversal.
for i in range(30):
 r=snap(f"pr-{i}"); t=" ".join(lab(n) for n in ns(r))
 if "profile" in t and ("home" in t or "discover" in t or "inbox" in t): break
 if clickid("tiny_discovery_left_operation_btn",r): continue
 if clickid("tiny_discovery_dislike_button",r) or clickid("tiny_discovery_like_button",r): continue
 adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
else:
 print("RESULT=NO_MAIN_NAV");raise SystemExit(20)
# Strongest observed route: restart, then Profile.
adb("shell","am","force-stop","com.kwai.video");time.sleep(2)
adb("shell","monkey","-p","com.kwai.video","1");time.sleep(15)
r=snap("pr-restarted")
if not clickid("ll_profile",r):
 for n in ns(r):
  if lab(n)=="profile" and tap(n):break
time.sleep(5)
# Inspect profile, then try account/menu/settings candidates one at a time.
for step in range(6):
 r=snap(f"pr-profile-{step}")
 labels=[lab(n) for n in ns(r)]
 edits=[n for n in ns(r) if n.attrib.get("editable")=="true" or n.attrib.get("class","").endswith("EditText")]
 auth=[n for n in ns(r) if any(x in lab(n) for x in ("log in","login","sign in","entrar","phone","telefone","email","e-mail","account","conta"))]
 print(f"STEP={step} EDITABLES={len(edits)} AUTH={len(auth)}")
 if edits or auth:
  print("RESULT=LOGIN_CONTROL_FOUND")
  raise SystemExit(0)
 candidates=[]
 for n in ns(r):
  s=lab(n); rid=n.attrib.get("resource-id","").lower()
  if any(x in s for x in ("settings","setting","menu","more","options","configura","gear")) or any(x in rid for x in ("setting","menu","more","option","gear")):
   candidates.append(n)
 if candidates and tap(candidates[0]): continue
 # Try common top-right profile menu coordinate only after semantic inspection.
 if step==0:
  adb("shell","input","tap","1000","120");time.sleep(3);continue
 break
r=snap("pr-final"); print("FINAL_UI="+" ".join(lab(n) for n in ns(r))[:3000]);print("RESULT=PROFILE_OPEN_NO_LOGIN");raise SystemExit(21)
