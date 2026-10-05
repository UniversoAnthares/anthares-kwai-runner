#!/usr/bin/env python3
import subprocess,re,time,xml.etree.ElementTree as ET
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout
def ui():
 adb("shell","uiautomator","dump","/sdcard/u.xml");x=adb("shell","cat","/sdcard/u.xml")
 try:r=ET.fromstring(x)
 except:return "",[]
 ns=list(r.iter("node"));t=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower() for n in ns)
 return t,ns
dump=adb("shell","dumpsys","package","com.kwai.video")
print("PACKAGE_DUMP_OK="+str("com.kwai.video" in dump))
targets=[]
for line in dump.splitlines():
 if any(k in line for k in ["TinyLoginActivity","TinyUserInfoActivity","TinyGoogleSSOActivity","AutoLoginActivity"]):
  print("COMPONENT_LINE="+line.strip())
  for tok in re.findall(r'([A-Za-z0-9_.$]+/[A-Za-z0-9_.$]+)',line):
   if tok not in targets: targets.append(tok)
print("TARGET_COUNT="+str(len(targets)))
if not targets: raise SystemExit(30)
for comp in targets:
 print("TRY_COMPONENT="+comp)
 out=adb("shell","am","start","-W","-n",comp);print("AM_RESULT="+out.replace("\n"," | ")[:900])
 time.sleep(3);t,ns=ui()
 ids=" ".join(n.attrib.get("resource-id","") for n in ns)
 edit=sum(1 for n in ns if n.attrib.get("class","").endswith("EditText"))
 signal=any(k in ids for k in ["tiny_login_","auth_token_login_button","tiny_google_login_platform_item"]) or edit>0
 print("LOGIN_SIGNAL="+str(signal)+" EDITABLES="+str(edit))
 print("UI="+t[:1200]);print("IDS="+ids[:2200])
 if signal:
  print("DIRECT_LOGIN_SURFACE_PROVEN="+comp);raise SystemExit(0)
print("DIRECT_LOGIN_SURFACE_NOT_FOUND");raise SystemExit(31)
