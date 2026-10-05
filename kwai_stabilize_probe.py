#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET,re
mode=os.environ.get("STABILIZE_MODE","wait30")
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def dump(tag):
    adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
    try:return ET.parse(f"{tag}.xml").getroot()
    except:return None
def text(r): return " ".join(((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()) for n in (r.iter("node") if r is not None else []))
def snap(tag):
    r=dump(tag)
    with open(tag+".png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
    return text(r)
# advance onboarding with repeated horizontal gestures; stop only when nav appears
for i in range(20):
    t=snap(f"advance-{i}")
    if "profile" in t and ("home" in t or "discover" in t): break
    adb("shell","input","swipe","900","1100","120","1100","350"); time.sleep(1)
if mode.startswith("wait"):
    sec=int(mode[4:]); time.sleep(sec)
elif mode=="wifi-reset":
    adb("shell","svc","wifi","disable"); time.sleep(2); adb("shell","svc","wifi","enable"); time.sleep(12)
elif mode=="airplane-cycle":
    adb("shell","cmd","connectivity","airplane-mode","enable"); time.sleep(2); adb("shell","cmd","connectivity","airplane-mode","disable"); time.sleep(12)
elif mode=="restart-after-nav":
    adb("shell","am","force-stop","com.kwai.video"); time.sleep(2); adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1"); time.sleep(15)
elif mode=="network-check":
    print(adb("shell","ping","-c","2","8.8.8.8")); print(adb("shell","ping","-c","2","www.google.com"))
elif mode=="resource-wait":
    time.sleep(60)
elif mode=="profile-after-wait":
    time.sleep(30); adb("shell","input","tap","960","2200"); time.sleep(5)
elif mode=="profile-after-restart":
    adb("shell","am","force-stop","com.kwai.video"); adb("shell","monkey","-p","com.kwai.video","1"); time.sleep(20); adb("shell","input","tap","960","2200"); time.sleep(5)
elif mode=="clear-cache":
    adb("shell","pm","trim-caches","999G"); time.sleep(5)
final=snap("final-"+mode)
print("STABILIZE_MODE="+mode); print("FINAL_UI="+final[:2500])
