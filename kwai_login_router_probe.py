#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re,sys
def adb(*a):
 p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30);return p.returncode,p.stdout
rc,out=adb("shell","am","start","-W","-a","android.intent.action.VIEW","-c","android.intent.category.BROWSABLE","-d","ikwai://login","com.kwai.video")
print("LOGIN_ROUTER_AM_RC="+str(rc));print("LOGIN_ROUTER_AM="+out.replace("\n"," | ")[:1600]);time.sleep(4)
_,acts=adb("shell","dumpsys","activity","activities")
for line in acts.splitlines():
 if "mResumedActivity" in line or ("com.kwai.video" in line and "ActivityRecord" in line):
  print("ACTIVITY="+line.strip()[:500])
adb("shell","uiautomator","dump","/sdcard/login.xml");_,x=adb("shell","cat","/sdcard/login.xml")
try:nodes=list(ET.fromstring(x).iter("node"))
except Exception as e:print("TEST_VALIDITY=UI_DUMP_INVALID "+repr(e));sys.exit(90)
vals=[];edits=0
for n in nodes:
 s=" ".join([n.attrib.get("text",""),n.attrib.get("content-desc",""),n.attrib.get("resource-id","")]).strip()
 if s: vals.append(s)
 if n.attrib.get("editable")=="true" or n.attrib.get("class","").endswith("EditText"): edits+=1
txt=" ".join(vals).lower()
hits=[w for w in ("login","log in","sign in","entrar","email","e-mail","phone","telefone","password","senha","account","conta") if w in txt]
print("EDITTEXT_COUNT="+str(edits));print("AUTH_HITS="+",".join(hits));print("LOGIN_UI="+txt[:2500]);print("TEST_VALIDITY=OK")
if edits or any(w in hits for w in ("login","log in","sign in","entrar","email","e-mail","phone","telefone","password","senha")):
 print("SUCCESS_SIGNAL=LOGIN_ROUTER_AUTH_SURFACE");sys.exit(0)
print("FAILURE_SIGNAL=LOGIN_ROUTER_NO_AUTH_SURFACE");sys.exit(20)
