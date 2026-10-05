#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re,sys
PKG="com.kwai.video"
ACTS=[
"com.yxcorp.gifshow.login.emaillogin.activity.EmailLoginActivity",
"com.yxcorp.gifshow.login.LoginActivity",
"com.yxcorp.gifshow.login.activity.CommonLoginActivity",
"com.yxcorp.gifshow.login.PhoneAccountActivityV2",
"com.yxcorp.gifshow.login.SplashLoginActivity",
]
def adb(*a,timeout=30):
 p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
 return p.returncode,p.stdout
rc,out=adb("shell","pm","path",PKG);print("PACKAGE_PATH_RC=",rc);print(out[:1000])
if rc or "package:" not in out: print("TEST_VALIDITY=PACKAGE_NOT_INSTALLED");sys.exit(90)
signals=("login","log in","sign in","email","e-mail","phone","password","senha","telefone","account","conta","auth","entrar")
valid=0
for act in ACTS:
 print("\nTRY_ACTIVITY="+act)
 rc,out=adb("shell","am","start","-W","-n",PKG+"/"+act); print("AM_RC="+str(rc));print("AM_RESULT="+out.replace("\n"," | ")[:1600])
 if rc!=0 or re.search(r"(Error type|does not exist|Permission Denial|unable to resolve)",out,re.I):
  print("START_ALLOWED=False");continue
 valid+=1;print("START_ALLOWED=True");time.sleep(3)
 _,fg=adb("shell","dumpsys","activity","activities"); m=re.search(r"mResumedActivity:.*? ([^ ]+/[^ ]+)",fg);print("FOREGROUND="+(m.group(1) if m else "UNKNOWN"))
 _,dump=adb("shell","uiautomator","dump","/sdcard/login.xml"); _,xml=adb("shell","cat","/sdcard/login.xml")
 try:
  root=ET.fromstring(xml); nodes=list(root.iter("node"))
 except Exception as e:
  print("UI_PARSE_ERROR="+repr(e));continue
 text=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")+" "+n.attrib.get("resource-id","")).lower() for n in nodes)
 edits=sum(1 for n in nodes if n.attrib.get("class","").endswith("EditText"))
 hits=sorted({s for s in signals if s in text})
 print("EDITTEXT_COUNT="+str(edits));print("AUTH_HITS="+",".join(hits));print("UI="+text[:2400])
 if edits>0 or hits:
  print("SUCCESS_SIGNAL=DECLARED_LOGIN_SURFACE_REACHED")
  print("SUCCESS_ACTIVITY="+act);sys.exit(0)
 adb("shell","am","force-stop",PKG);time.sleep(1)
if valid==0: print("FAILURE_SIGNAL=ALL_DECLARED_ACTIVITIES_REJECTED");sys.exit(20)
print("FAILURE_SIGNAL=ACTIVITIES_STARTED_WITHOUT_LOGIN_UI");sys.exit(21)
