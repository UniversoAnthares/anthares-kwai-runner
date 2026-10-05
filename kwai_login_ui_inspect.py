#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re,json
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout
def dump(tag):
    adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml"); adb("pull",f"/sdcard/{tag}.xml",f"{tag}.xml")
    try:return ET.parse(f"{tag}.xml").getroot()
    except:return None
def rows(r):
    out=[]
    if r is None:return out
    for n in r.iter("node"):
        a=n.attrib
        if a.get("text") or a.get("content-desc") or a.get("resource-id") or a.get("clickable")=="true" or a.get("editable")=="true":
            out.append({k:a.get(k,"") for k in ("text","content-desc","resource-id","class","clickable","editable","bounds")})
    return out
def center(b):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "")
    return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def snap(tag):
    r=dump(tag); rr=rows(r); print("SNAP="+tag); print(json.dumps(rr,ensure_ascii=False)[:12000]); return r,rr
def tap_semantic(rr,words):
    for n in rr:
        s=(n["text"]+" "+n["content-desc"]).lower()
        if any(w in s for w in words):
            p=center(n["bounds"])
            if p: adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
    return False
def clear_permission_dialog():
    for _ in range(6):
        r,rr=snap("permission-check")
        if not any("permissioncontroller" in x["resource-id"] for x in rr):
            return
        target=None
        for x in rr:
            rid=x["resource-id"]
            if rid.endswith("permission_deny_button") or rid.endswith("permission_allow_button"):
                target=x; break
        if target:
            p=center(target["bounds"])
            if p: adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(1);continue
        adb("shell","input","keyevent","4");time.sleep(1)

clear_permission_dialog()

# Traverse interest onboarding by proven adaptive gestures.
for i in range(18):
    r,rr=snap("inspect-stage-"+str(i))
    text=" ".join((x["text"]+" "+x["content-desc"]).lower() for x in rr)
    if "profile" in text and ("home" in text or "discover" in text): break
    adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(.8)
# Stabilize using proven relaunch.
adb("shell","am","force-stop","com.kwai.video");time.sleep(2)
adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1");time.sleep(15)
r,rr=snap("inspect-stable")
# Open Profile semantically, then inspect only; no credentials.
clicked=False
for x in rr:
    if x["resource-id"].endswith("ll_profile"):
        p=center(x["bounds"])
        if p:
            adb("shell","input","tap",str(p[0]),str(p[1]))
            time.sleep(5)
            clicked=True
            break
if not clicked:
    tap_semantic(rr,("profile","perfil"))
r,rr=snap("inspect-profile")
# Try only visible login/sign-in/account controls, one transition at a time.
for step in range(4):
    if not tap_semantic(rr,("log in","login","sign in","entrar","account","conta","phone","telefone","email")): break
    r,rr=snap("inspect-login-"+str(step))
print("INSPECT_COMPLETE")
