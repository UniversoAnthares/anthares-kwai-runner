#!/usr/bin/env python3
"""KW-02: inspect native creator on authorized Kwai session. No upload/publish."""
import re
import subprocess
import time
import xml.etree.ElementTree as ET

def adb(*args):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=32)
    return p.stdout

def snapshot():
    adb("shell","uiautomator","dump","/sdcard/kw02-auth-create.xml")
    raw=adb("exec-out","cat","/sdcard/kw02-auth-create.xml")
    root=ET.fromstring(raw)
    ns=list(root.iter("node"))
    text=" ".join((n.get("text","")+" "+n.get("content-desc","")).strip().casefold() for n in ns)
    return ns,text

def center(n):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds",""))
    if not m:return None
    a,b,c,d=map(int,m.groups())
    return (a+c)//2,(b+d)//2

def click(n):
    p=center(n)
    if p is None:return False
    adb("shell","input","tap",str(p[0]),str(p[1]))
    time.sleep(4)
    return True

def activity():
    out=adb("shell","dumpsys","activity","activities")
    return " ".join(l.strip() for l in out.splitlines() if "topResumedActivity" in l or "mResumedActivity" in l)[-350:]

CREATOR_WORDS=("album","gallery","upload","record","effects","flip camera","select video","choose video","gravar","galeria","álbum","câmera","carregar")
LOGIN_WORDS=("verification code","continue with google","log in to","sign in","entrar com","phone email")

def creator_visible(text,foreground):
    creator=any(w in text for w in CREATOR_WORDS)
    foreground_creator=bool(re.search(r"(record|camera|capture|editor|publish|album)activity",foreground,re.I))
    home=any(w in text for w in ("home discover inbox profile","início descobrir caixa de entrada perfil","for you home"))
    return bool((creator and not home) or foreground_creator)

def main():
    ns,text=snapshot()
    if creator_visible(text,activity()):
        print("KW02_CREATOR_NATIVE_UI=PASS")
        return 0
    candidates=[n for n in ns if (n.get("resource-id") or "").endswith(("id_record_layout","fake_add_button"))]
    if not candidates:
        print("KW02_CREATE_BUTTON_MISSING")
        return 42
    for n in candidates:
        print("KW02_CREATE_CONTROL=ENABLED_%s_CLICKABLE_%s"%(n.get("enabled"),n.get("clickable")))
        if not click(n):continue
        for i in range(5):
            ns2,t=snapshot()
            fg=activity()
            if creator_visible(t,fg):
                print("KW02_CREATOR_NATIVE_UI=PASS")
                print("KW02_CREATOR_ACTIVITY="+fg[:260])
                print("KW02_PUBLISH_OPERATION=NOT_TRIGGERED")
                return 0
            if any(w in t for w in LOGIN_WORDS):
                print("KW02_CREATE_AUTH_GATE=YES")
                return 43
            time.sleep(3)
    print("KW02_CREATOR_NATIVE_UI=BLOCKED")
    return 44

if __name__=="__main__":
    raise SystemExit(main())
