#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def snap(name):
    adb("shell","uiautomator","dump","/sdcard/"+name+".xml")
    return ET.fromstring(adb("shell","cat","/sdcard/"+name+".xml"))
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def tap(n,right=False):
    nums=[int(x) for x in re.findall(r"\d+",n.attrib.get("bounds",""))]
    if len(nums)!=4:return False
    x1,y1,x2,y2=nums
    x=x1+(x2-x1)*3//4 if right else (x1+x2)//2
    adb("shell","input","tap",str(x),str((y1+y2)//2));time.sleep(4);return True
root=snap("preauth")
login=[n for n in root.iter("node") if lab(n) in ("log in","login","sign in","entrar")]
print("V2_LOGIN_NODES="+str(len(login)))
if login: tap(login[0])
root=snap("chooser")
phone=[n for n in root.iter("node") if "phone" in lab(n) or "telefone" in lab(n)]
print("V2_PHONE_NODES="+str(len(phone)))
for n in phone[:5]: print("V2_PHONE_NODE="+lab(n)+" RID="+n.attrib.get("resource-id","")+" B="+n.attrib.get("bounds",""))
if phone: tap(phone[0],"facebook" in lab(phone[0]))
try:
    root=snap("afterphone")
    labels=" | ".join(lab(n) for n in root.iter("node") if lab(n))
    ids=" ".join(n.attrib.get("resource-id","") for n in root.iter("node") if n.attrib.get("resource-id",""))
    print("V2_AFTER_PHONE_UI="+labels[-3000:])
    print("V2_AFTER_PHONE_IDS="+ids[-5000:])
except Exception as e: print("V2_AFTER_PHONE_DUMP_ERROR="+type(e).__name__)
