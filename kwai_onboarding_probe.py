#!/usr/bin/env python3
import os,subprocess,time,xml.etree.ElementTree as ET
mode=os.environ.get("TEST_MODE","baseline")
def adb(*a):
    return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20).stdout
def snap(tag):
    adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml")
    adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
    with open(f"{tag}.png","wb") as f: subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=20)
def ui():
    snap("probe-"+mode)
    try:
        r=ET.parse("probe-"+mode+".xml").getroot()
        return " ".join(((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()) for n in r.iter("node"))
    except Exception:return ""
if mode=="permission": adb("shell","pm","grant","com.kwai.video","android.permission.POST_NOTIFICATIONS")
elif mode=="back":
    for _ in range(4): adb("shell","input","keyevent","4"); time.sleep(1)
elif mode=="swipe":
    for _ in range(4): adb("shell","input","swipe","850","1100","180","1100","300"); time.sleep(1)
elif mode=="tap":
    for x,y in [(270,1200),(810,1200),(540,2050),(950,2050)]: adb("shell","input","tap",str(x),str(y)); time.sleep(1)
elif mode=="activity": print(adb("shell","dumpsys","package","com.kwai.video"))
elif mode=="intent": adb("shell","am","start","-a","android.intent.action.VIEW","-d","kwai://login","com.kwai.video"); time.sleep(3)
elif mode=="settings":
    adb("shell","appops","set","com.kwai.video","POST_NOTIFICATION","allow")
    adb("shell","settings","put","global","heads_up_notifications_enabled","0")
elif mode=="adaptive":
    for _ in range(8):
        t=ui()
        if any(x in t for x in ["login","log in","sign in","entrar"]): break
        adb("shell","input","swipe","850","1100","180","1100","250"); time.sleep(1)
elif mode=="inspect":
    print(adb("shell","dumpsys","activity","activities")); print(adb("shell","dumpsys","window","windows"))
snap("result-"+mode)
print("MODE="+mode)
print("UI="+ui()[:1500])
