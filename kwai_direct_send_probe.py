#!/usr/bin/env python3
import hashlib,os,re,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path

PKG="com.kwai.video"
ACTIVITY="com.kscorp.oversea.platform.router.ui.UriRouterActivity"
LOCAL=Path("direct-send-probe.mp4")
XML=Path("direct-send-after.xml")
PNG=Path("direct-send-after.png")
BASE_XML=Path("direct-send-before.xml")

def run(cmd,check=False,timeout=60,text=True):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=text,timeout=timeout)
    if check and p.returncode: raise RuntimeError(f"rc={p.returncode} cmd={cmd} out={p.stdout}")
    return p

def adb(*args,check=False,timeout=45):
    return run(["adb",*args],check=check,timeout=timeout).stdout

def dump(local):
    remote="/sdcard/"+local.name
    adb("shell","uiautomator","dump",remote,check=True)
    adb("pull",remote,str(local),check=True)
    root=ET.parse(local).getroot()
    text=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).casefold() for n in root.iter("node"))
    ids=" ".join(n.attrib.get("resource-id","") for n in root.iter("node") if n.attrib.get("resource-id"))
    return " ".join(text.split()),ids

def screenshot():
    adb("shell","screencap","-p","/sdcard/direct-send-after.png")
    adb("pull","/sdcard/direct-send-after.png",str(PNG))

def foreground():
    out=adb("shell","dumpsys","window","windows")
    lines=[x.strip() for x in out.splitlines() if "mCurrentFocus" in x or "mFocusedApp" in x]
    return " | ".join(lines[:4])

# Deterministic, local-only test media: no network source and no user content.
ff=run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","lavfi","-i","color=c=black:s=320x240:r=24:d=2","-an","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(LOCAL)],timeout=60)
if ff.returncode or not LOCAL.exists() or LOCAL.stat().st_size<1000:
    print("TEST_VALIDITY=INVALID_FFMPEG_MEDIA_GENERATION"); print(ff.stdout or ""); sys.exit(90)
sha=hashlib.sha256(LOCAL.read_bytes()).hexdigest(); size=LOCAL.stat().st_size
name=f"anthares-direct-send-{sha[:12]}.mp4"
remote=f"/sdcard/Movies/AntharesPublish/{name}"
print(f"MEDIA_SHA256={sha}"); print(f"MEDIA_SIZE={size}"); print(f"MEDIA_NAME={name}")

adb("shell","mkdir","-p","/sdcard/Movies/AntharesPublish",check=True)
adb("shell","rm","-f","/sdcard/Movies/AntharesPublish/*")
adb("push",str(LOCAL),remote,check=True,timeout=90)
adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE","-d",f"file://{remote}")
time.sleep(3)
q=adb("shell","content","query","--uri","content://media/external/video/media","--projection","_id:_display_name:_size")
rows=[line for line in q.splitlines() if f"_display_name={name}" in line and f"_size={size}" in line]
if len(rows)!=1:
    print(f"TEST_VALIDITY=INVALID_MEDIASTORE_COUNT COUNT={len(rows)}"); sys.exit(91)
m=re.search(r"_id=(\d+)",rows[0])
if not m:
    print("TEST_VALIDITY=INVALID_MEDIASTORE_ID"); sys.exit(92)
media_id=m.group(1); uri=f"content://media/external/video/media/{media_id}"
print(f"MEDIASTORE_ID={media_id}"); print(f"MEDIA_URI={uri}")

# Normalize to a normal app surface before the explicit share handoff.
adb("shell","pm","grant",PKG,"android.permission.POST_NOTIFICATIONS")
adb("shell","am","force-stop",PKG)
adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1")
time.sleep(5)
try:
    before_text,before_ids=dump(BASE_XML)
except Exception as e:
    print(f"TEST_VALIDITY=INVALID_BASELINE_DUMP ERROR={e}"); sys.exit(93)
print("BASELINE_UI="+before_text[:900])

adb("shell","am","force-stop",PKG)
cmd=["shell","am","start","-W","-n",f"{PKG}/{ACTIVITY}","-a","android.intent.action.SEND","-t","video/mp4","-f","0x1","--eu","android.intent.extra.STREAM",uri]
out=adb(*cmd,timeout=60)
print("AM_RESULT="+" | ".join(out.splitlines()))
if "Status: ok" not in out and "Complete" not in out:
    print("FAILURE_SIGNAL=ACTION_SEND_REJECTED"); sys.exit(20)
time.sleep(8)
try:
    after_text,after_ids=dump(XML); screenshot()
except Exception as e:
    print(f"TEST_VALIDITY=INVALID_POST_SEND_DUMP ERROR={e}"); sys.exit(94)
fg=foreground(); print("FOREGROUND="+fg)
print("POST_SEND_UI="+after_text[:1800])
print("POST_SEND_IDS="+after_ids[:2200])
if PKG not in fg:
    print("FAILURE_SIGNAL=KWAI_NOT_FOREGROUND_AFTER_SEND"); sys.exit(21)
if any(x in after_text for x in ("import failed","unsupported file","can't import","cannot import","falha ao importar","arquivo não suportado")):
    print("FAILURE_SIGNAL=EXPLICIT_IMPORT_ERROR"); sys.exit(22)
editor_markers=(" next "," próximo "," publish "," publicar "," edit "," editar "," cover "," capa "," effects "," efeitos "," music "," música "," caption "," legenda ")
editor_id_markers=("editor","publish","post","caption","cover","preview","photo_editor","video_edit")
editor_hit=any(x in " "+after_text+" " for x in editor_markers) or any(x in after_ids.casefold() for x in editor_id_markers)
changed=(after_text!=before_text or after_ids!=before_ids)
if editor_hit and changed:
    print("SUCCESS_SIGNAL=DIRECT_SEND_MEDIA_EDITOR")
    sys.exit(0)
if changed:
    print("PARTIAL_SIGNAL=DIRECT_SEND_ACCEPTED_UI_CHANGED")
    sys.exit(23)
print("FAILURE_SIGNAL=DIRECT_SEND_UNCHANGED_MAIN")
sys.exit(24)
