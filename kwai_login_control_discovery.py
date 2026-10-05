#!/usr/bin/env python3
import subprocess,time,xml.etree.ElementTree as ET,re
def adb(*a):
    return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout
def dump(tag):
    adb("shell","uiautomator","dump",f"/sdcard/{tag}.xml")
    adb("pull",f"/sdcard/{tag}.xml",f"/tmp/{tag}.xml")
    try:return ET.parse(f"/tmp/{tag}.xml").getroot()
    except:return None
def ns(r): return list(r.iter("node")) if r is not None else []
def lab(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip().lower()
def ctr(b):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",b or "")
    return ((int(m[1])+int(m[3]))//2,(int(m[2])+int(m[4]))//2) if m else None
def tap(n):
    p=ctr(n.attrib.get("bounds"))
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]));time.sleep(2);return True
def summary(tag,r):
    vals=[]
    for n in ns(r):
        s=lab(n); rid=n.attrib.get("resource-id","")
        if s or rid:
            vals.append((s,rid,n.attrib.get("class","").split(".")[-1],n.attrib.get("clickable","")))
    print("STATE="+tag)
    for x in vals[-80:]: print("NODE="+" | ".join(x))
def interest(r):
    for suffix in ("tiny_discovery_dislike_button","tiny_discovery_like_button"):
        for n in ns(r):
            if n.attrib.get("resource-id","").endswith(suffix):
                return tap(n)
    return False
# Advance using actual controls first; swipe only when no icon control exists.
for i in range(20):
    r=dump(f"s{i}"); t=" ".join(lab(n) for n in ns(r))
    if "profile" in t and ("home" in t or "discover" in t or "inbox" in t):
        summary("MAIN_NAV",r);break
    # Explicit final onboarding gate discovered in run 37380757409.
    start=[n for n in ns(r) if n.attrib.get("resource-id","").endswith("tiny_discovery_left_operation_btn") or lab(n)=="start now"]
    if start:
        print("START_NOW_GATE=1")
        if tap(start[0]): continue
    if interest(r):continue
    adb("shell","input","swipe","850","1100","180","1100","250");time.sleep(1)
else:
    summary("NO_MAIN_NAV",dump("no-main"));raise SystemExit(20)
# Semantic Profile.
r=dump("main")
for n in ns(r):
    if n.attrib.get("resource-id","").endswith("ll_profile") and n.attrib.get("clickable")=="true":
        print("PROFILE_CLICK_TARGET="+n.attrib.get("resource-id",""))
        if tap(n): break
else:
    for n in ns(r):
        if "profile" in lab(n) and tap(n): break
r=dump("profile");summary("PROFILE_INITIAL",r)
# Profile is a dynamic feature in this build. Wait for the download gate to
# disappear before concluding that authentication controls are absent.
for wait_idx in range(36):
    t=" ".join(lab(n) for n in ns(r))
    loading=("resource downloading" in t or "access to all the features when" in t)
    if not loading:
        print("PROFILE_MODULE_READY=1")
        break
    print("PROFILE_MODULE_WAIT="+str(wait_idx))
    time.sleep(5)
    r=dump("profile-wait")
else:
    print("PROFILE_MODULE_TIMEOUT=1")
    # Hide the progress dialog, then re-open the already requested Profile module.
    for n in ns(r):
        if n.attrib.get("resource-id","").endswith("btn_cancel") or lab(n)=="hide":
            tap(n); break
    rr=dump("main-after-hide")
    for n in ns(rr):
        if n.attrib.get("resource-id","").endswith("ll_profile") or lab(n)=="profile":
            if tap(n): break
    r=dump("profile-after-reopen")
summary("PROFILE_READY_STATE",r)
# Try only explicit auth/account controls, logging state after each candidate.
terms=("log in","login","sign in","entrar","account","conta","phone","telefone","email","e-mail")
candidates=[n for n in ns(r) if any(t in lab(n) for t in terms)]
print("AUTH_CANDIDATES="+str(len(candidates)))
for idx,n in enumerate(candidates[:8]):
    print("TRY="+str(idx)+" | "+lab(n)+" | "+n.attrib.get("resource-id",""))
    if tap(n):
        rr=dump("candidate");summary("AFTER_AUTH_CANDIDATE",rr)
        edits=[x for x in ns(rr) if x.attrib.get("editable")=="true" or x.attrib.get("class","").endswith("EditText")]
        if edits:
            print("LOGIN_FORM_FOUND=1");raise SystemExit(0)
        adb("shell","input","keyevent","4");time.sleep(1)
print("LOGIN_FORM_FOUND=0")
raise SystemExit(21)
