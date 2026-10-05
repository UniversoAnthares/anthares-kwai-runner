#!/usr/bin/env python3
import subprocess, time, xml.etree.ElementTree as ET, re, sys

AUTH = ("log in","login","entrar","sign in","telefone","phone","password","senha",
        "verification code","código de verificação","facebook","google")
HOME = ("following","seguindo","for you","para você","profile","perfil","discover",
        "descobrir","friends","amigos","create","criar")

def adb(*args):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout

def dump():
    adb("shell","uiautomator","dump","/sdcard/kwai-auth.xml")
    adb("pull","/sdcard/kwai-auth.xml","/tmp/kwai-auth.xml")
    root=ET.parse("/tmp/kwai-auth.xml").getroot()
    return " ".join(((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip()) for n in root.iter("node")).lower()

for attempt in range(12):
    try: text=dump()
    except Exception:
        time.sleep(2); continue
    if any(x in text for x in AUTH):
        print("KWAI_AUTH_STATE=AUTH_REQUIRED")
        sys.exit(10)
    if any(x in text for x in HOME):
        print("KWAI_AUTH_STATE=AUTHENTICATED_UI")
        sys.exit(0)
    time.sleep(2)

print("KWAI_AUTH_STATE=UNKNOWN")
sys.exit(11)
