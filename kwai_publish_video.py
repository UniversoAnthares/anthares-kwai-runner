#!/usr/bin/env python3
import os,re,subprocess,sys,time,xml.etree.ElementTree as ET
TITLE=os.environ.get("KWAI_VIDEO_TITLE","").strip()
MEDIA_NAME=os.environ.get("KWAI_MEDIA_NAME","").strip()
VIDEO=os.environ.get("KWAI_ANDROID_VIDEO","").strip()
if not MEDIA_NAME or not VIDEO:
    print("STATE=FAILED_SAFE REASON=missing-media-identity"); sys.exit(69)
def adb(*args):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout
def dump():
    adb("shell","uiautomator","dump","/sdcard/kwai-publish.xml")
    adb("pull","/sdcard/kwai-publish.xml","/tmp/kwai-publish.xml")
    return ET.parse("/tmp/kwai-publish.xml").getroot()
def label(n): return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()
def center(bounds):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2)
def tap(words,retries=4):
    for _ in range(retries):
        try:r=dump()
        except Exception: time.sleep(1); continue
        for n in r.iter("node"):
            if any(w in label(n) for w in words):
                p=center(n.attrib.get("bounds",""))
                if p:
                    adb("shell","input","tap",str(p[0]),str(p[1])); time.sleep(2); return True
        time.sleep(1)
    return False
def fill_title():
    if not TITLE:return True
    r=dump(); edits=[n for n in r.iter("node") if n.attrib.get("class","").endswith("EditText")]
    if not edits:return False
    p=center(edits[0].attrib.get("bounds",""))
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]))
    safe=TITLE[:120].replace("%","%25").replace(" ","%s").replace("&","\\&").replace("(","\\(").replace(")","\\)")
    adb("shell","input","text",safe); time.sleep(1); return True

adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1"); time.sleep(3)
if not tap(("create","criar","post","publicar","+")): print("STATE=FAILED_SAFE REASON=composer-not-opened"); sys.exit(70)
tap(("album","álbum","gallery","galeria","upload","carregar","photos","fotos")); time.sleep(2)
# Deterministic invariant: the AntharesPublish MediaStore namespace contains exactly one staged video.
q=adb("shell","content","query","--uri","content://media/external/video/media","--projection","_id:_display_name:_size")
rows=[x for x in q.splitlines() if MEDIA_NAME in x]
if len(rows)!=1:
    print(f"STATE=FAILED_SAFE REASON=media-identity-not-unique COUNT={len(rows)}"); sys.exit(71)
print("STATE=MEDIA_IDENTITY_VERIFIED NAME="+MEDIA_NAME)
r=dump(); candidates=[]
for n in r.iter("node"):
    s=label(n); p=center(n.attrib.get("bounds",""))
    if p and p[1]>180 and n.attrib.get("clickable")=="true":
        candidates.append((p,s))
# Fresh remote executor + dedicated namespace must expose a selectable video. We do not claim identity from UI alone.
if not candidates: print("STATE=FAILED_SAFE REASON=no-selectable-media"); sys.exit(71)
adb("shell","input","tap",str(candidates[0][0][0]),str(candidates[0][0][1])); time.sleep(2)
if not tap(("next","próximo","avançar","continue","continuar")):
    print("STATE=FAILED_SAFE REASON=media-selection-not-accepted"); sys.exit(75)
time.sleep(2)
if not fill_title(): print("STATE=FAILED_SAFE REASON=caption-field-missing"); sys.exit(76)
print("STATE=CAPTION_SET")
# From this line onward any crash/timeout is ambiguous: never blind-retry.
print("STATE=PUBLISH_REQUESTED")
if not tap(("publish","publicar","post","compartilhar","share"),6):
    print("STATE=FAILED_SAFE REASON=publish-control-not-found"); sys.exit(72)
for _ in range(20):
    time.sleep(3)
    try: txt=" ".join(label(n) for n in dump().iter("node"))
    except Exception: continue
    if any(k in txt for k in ("failed","falhou","error","erro","try again","tente novamente")):
        print("STATE=UNCERTAIN REASON=post-request-visible-error"); sys.exit(90)
    if any(k in txt for k in ("published","publicado","posted","enviado com sucesso","upload complete")):
        print("STATE=VERIFYING UI_MARKER=1"); sys.exit(0)
    if any(k in txt for k in ("for you","para você","following","seguindo","profile","perfil")) and not any(k in txt for k in ("publish","publicar","post")):
        print("STATE=VERIFYING HOME_RETURN=1"); sys.exit(0)
print("STATE=UNCERTAIN REASON=post-request-timeout"); sys.exit(90)
