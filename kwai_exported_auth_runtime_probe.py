#!/usr/bin/env python3
import subprocess,time,re,xml.etree.ElementTree as ET,sys
PKG="com.kwai.video"; URIS=["ikwai://authorization","kwai://authorization","ikwaipartner://auth","com.kwai.video://auth"]
def adb(*a):
 p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30); return p.returncode,p.stdout
rc,out=adb("shell","pm","path",PKG)
if rc or "package:" not in out: print("TEST_VALIDITY=PACKAGE_MISSING");sys.exit(90)
for uri in URIS:
 print("TRY_URI="+uri)
 rc,out=adb("shell","am","start","-W","-a","android.intent.action.VIEW","-c","android.intent.category.BROWSABLE","-d",uri,PKG)
 print("AM_RC="+str(rc));print("AM_RESULT="+out.replace("\n"," | ")[:1400]);time.sleep(3)
 _,acts=adb("shell","dumpsys","activity","activities")
 m=re.search(r"mResumedActivity:.*? ([^ ]+/[^ ]+)",acts); fg=m.group(1) if m else "UNKNOWN";print("FOREGROUND="+fg)
 _,_=adb("shell","uiautomator","dump","/sdcard/a.xml");_,xml=adb("shell","cat","/sdcard/a.xml")
 try: nodes=list(ET.fromstring(xml).iter("node"))
 except Exception as e: print("UI_PARSE_ERROR="+repr(e));continue
 text=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")+" "+n.attrib.get("resource-id","")).lower() for n in nodes)
 edits=sum(n.attrib.get("class","").endswith("EditText") for n in nodes)
 hits=sorted({s for s in ("login","log in","sign in","email","phone","password","senha","telefone","account","conta","authorization","authorize","entrar") if s in text})
 print("EDITTEXT_COUNT="+str(edits));print("AUTH_HITS="+",".join(hits));print("UI="+text[:1800])
 if "login" in fg.lower() or edits or any(x in hits for x in ("login","log in","sign in","email","phone","password","senha","telefone","entrar")):
  print("SUCCESS_SIGNAL=AUTH_FLOW_REACHED");print("SUCCESS_URI="+uri);sys.exit(0)
 adb("shell","am","force-stop",PKG);time.sleep(1)
print("FAILURE_SIGNAL=EXPORTED_ROUTES_NO_LOGIN_UI");sys.exit(20)
