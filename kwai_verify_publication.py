#!/usr/bin/env python3
import base64,hashlib,json,os,re,subprocess,sys,time,xml.etree.ElementTree as ET

TITLE=os.environ.get("KWAI_VIDEO_TITLE","").strip()
EXPECTED_ACCOUNT=os.environ.get("KWAI_EXPECTED_ACCOUNT","").strip()
JOB_ID=os.environ.get("KWAI_QUEUE_JOB_ID","").strip()
MEDIA_SHA=os.environ.get("KWAI_MEDIA_SHA256","").strip()

if not TITLE or not EXPECTED_ACCOUNT or not JOB_ID or not MEDIA_SHA:
    print("STATE=PROFILE_UNAVAILABLE REASON=missing-verification-identity"); sys.exit(2)

def norm(s): return " ".join((s or "").casefold().split())
def adb(*a):
    return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25).stdout

def snapshot():
    adb("shell","uiautomator","dump","/sdcard/verify.xml")
    adb("pull","/sdcard/verify.xml","/tmp/verify.xml")
    root=ET.parse("/tmp/verify.xml").getroot()
    text=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower() for n in root.iter("node"))
    return root,norm(text)

def center(bounds):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2)

def click_profile():
    for _ in range(5):
        try: root,text=snapshot()
        except Exception: time.sleep(2); continue
        preferred=[]; fallback=[]
        for n in root.iter("node"):
            rid=n.attrib.get("resource-id","")
            s=norm(n.attrib.get("text","")+" "+n.attrib.get("content-desc",""))
            p=center(n.attrib.get("bounds",""))
            if not p: continue
            if rid.endswith("ll_profile") and n.attrib.get("clickable")=="true": preferred.append((n,p))
            elif s in ("profile","perfil"): fallback.append((n,p))
        choices=preferred or fallback
        if choices:
            p=choices[0][1]; adb("shell","input","tap",str(p[0]),str(p[1])); time.sleep(4); return True
        time.sleep(2)
    return False

if not click_profile():
    print("STATE=PROFILE_UNAVAILABLE REASON=profile-control-not-reached"); sys.exit(2)

expected_account=norm(EXPECTED_ACCOUNT)
title_full=norm(TITLE)
title_needle=title_full[:80]
stable_without_loading=0

for i in range(36):
    try: root,text=snapshot()
    except Exception:
        print(f"STATE=PROFILE_UNAVAILABLE ATTEMPT={i} REASON=snapshot-error"); time.sleep(5); continue
    loading=("resource downloading" in text or "access to all the features when" in text)
    if loading:
        stable_without_loading=0
        print(f"STATE=PROFILE_LOADING ATTEMPT={i}")
        time.sleep(5); continue
    stable_without_loading+=1
    print(f"STATE=PROFILE_READY ATTEMPT={i} STABLE={stable_without_loading}")
    if stable_without_loading < 2:
        time.sleep(3); continue
    if expected_account not in text:
        print("STATE=PROFILE_READY ACCOUNT_MATCH=0")
        time.sleep(5); continue
    print("STATE=PROFILE_READY ACCOUNT_MATCH=1")
    if not title_needle or title_needle not in text:
        print("STATE=PROFILE_READY POST_MATCH=0")
        time.sleep(5); continue
    print("STATE=PROFILE_READY POST_MATCH=1")
    evidence={
        "job_id":JOB_ID,
        "media_sha256":MEDIA_SHA,
        "expected_account":EXPECTED_ACCOUNT,
        "observed_account_match":True,
        "expected_title":TITLE,
        "observed_title_match":True,
        "profile_state":"ready"
    }
    raw=json.dumps(evidence,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    token=base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    digest=hashlib.sha256(raw).hexdigest()
    print("KWAI_PUBLICATION_SPECIFICALLY_VERIFIED")
    print("KWAI_CONFIRMATION_EVIDENCE="+token)
    print("KWAI_CONFIRMATION_EVIDENCE_SHA256="+digest)
    sys.exit(0)

print("STATE=PROFILE_UNAVAILABLE REASON=intended-post-not-positively-verified")
sys.exit(1)
