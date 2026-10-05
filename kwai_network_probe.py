#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re,urllib.request,socket
def sh(*a,timeout=20):
    return subprocess.run(list(a),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout).stdout.strip()
def adb(*a): return sh("adb",*a)
def ui():
    adb("shell","uiautomator","dump","/sdcard/net.xml"); adb("pull","/sdcard/net.xml","net.xml")
    try:
        r=ET.parse("net.xml").getroot()
        return " ".join(((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()) for n in r.iter("node"))
    except: return ""
print("ANDROID_DNS="+adb("shell","getprop","net.dns1"))
print("ANDROID_ROUTE="+adb("shell","ip","route").replace("\n"," | ")[:1200])
for host in ["www.kwai.com","m.kwai.com","api.kwai.com","www.google.com"]:
    try: print("HOST_DNS_"+host+"="+socket.gethostbyname(host))
    except Exception as e: print("HOST_DNS_"+host+"=ERR:"+type(e).__name__)
    out=adb("shell","sh","-c",f"getent hosts {host} 2>/dev/null || ping -c 1 -W 2 {host} 2>&1 | head -4")
    print("ANDROID_"+host+"="+out.replace("\n"," | ")[:800])
for i in range(5):
    t=ui()
    m=re.search(r"(resource downloading[^%]{0,120}(\d+)%|\b(\d+)%\b)",t)
    print(f"UI_CHECK_{i}="+t[:1600])
    print(f"RESOURCE_PROGRESS_{i}="+((m.group(2) or m.group(3)) if m else "NONE"))
    time.sleep(10)
