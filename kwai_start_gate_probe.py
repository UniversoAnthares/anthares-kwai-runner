#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET,re,hashlib
M=os.environ.get("GATE_MODE","node")
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def dump(tag):
 adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); out=adb("shell","cat",f"/sdcard/{tag}.xml")
 try:return ET.fromstring(out),out
 except:return None,out
def ns(r): return list(r.iter("node")) if r is not None else []
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def ctr(b):
 m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or ""); return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tapxy(p):
 if p: adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2)
def startnode(r):
 for n in ns(r):
  if n.attrib.get("resource-id","").endswith("tiny_discovery_left_operation_btn") or lab(n)=="start now": return n
def main(t): return "profile" in t and ("home" in t or "discover" in t or "inbox" in t)
# reach final gate using known interest controls/swipes
for i in range(24):
 r,x=dump("pre"); t=" ".join(lab(n) for n in ns(r))
 if main(t): print("ALREADY_MAIN=1"); raise SystemExit(0)
 s=startnode(r)
 if s: break
 hit=False
 for n in ns(r):
  if n.attrib.get("resource-id","").endswith(("tiny_discovery_dislike_button","tiny_discovery_like_button")):
   tapxy(ctr(n.attrib.get("bounds")));hit=True;break
 if not hit: adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
else: print("NO_START_GATE=1");raise SystemExit(20)
before=hashlib.sha256(x.encode()).hexdigest(); p=ctr(s.attrib.get("bounds")); print("START_BOUNDS="+str(p))
if M=="node": tapxy(p)
elif M=="double": tapxy(p);tapxy(p)
elif M=="long": 
 if p: adb("shell","input","swipe",str(p[0]),str(p[1]),str(p[0]),str(p[1]),"800");time.sleep(3)
elif M=="enter": adb("shell","input","keyevent","66");time.sleep(3)
elif M=="dpad": adb("shell","input","keyevent","23");time.sleep(3)
elif M=="tab-enter": adb("shell","input","keyevent","61");adb("shell","input","keyevent","66");time.sleep(3)
elif M=="center": adb("shell","input","tap","540","2050");time.sleep(3)
elif M=="low-center": adb("shell","input","tap","540","2180");time.sleep(3)
elif M=="high-center": adb("shell","input","tap","540","1900");time.sleep(3)
elif M=="back": adb("shell","input","keyevent","4");time.sleep(3)
elif M=="restart": adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","1");time.sleep(15)
elif M=="tap-restart": tapxy(p);adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","1");time.sleep(15)
elif M=="wait5-tap": time.sleep(5);tapxy(p)
elif M=="wait15-tap": time.sleep(15);tapxy(p)
elif M=="wait30-tap": time.sleep(30);tapxy(p)
elif M=="swipe-left": adb("shell","input","swipe","900","1100","100","1100","300");time.sleep(3)
elif M=="swipe-up": adb("shell","input","swipe","540","1800","540","500","300");time.sleep(3)
elif M=="swipe-down": adb("shell","input","swipe","540","500","540","1800","300");time.sleep(3)
elif M=="tap-back-tap": tapxy(p);adb("shell","input","keyevent","4");time.sleep(2);r2,_=dump("mid");tapxy(ctr(startnode(r2).attrib.get("bounds")) if startnode(r2) is not None else p)
elif M=="tap-wait10": tapxy(p);time.sleep(10)
r2,y=dump("after"); t2=" ".join(lab(n) for n in ns(r2)); after=hashlib.sha256(y.encode()).hexdigest()
print("GATE_MODE="+M);print("XML_CHANGED="+str(before!=after));print("START_STILL="+str(startnode(r2) is not None));print("MAIN_NAV="+str(main(t2)));print("AFTER_UI="+t2[:1800])
