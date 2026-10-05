#!/usr/bin/env python3
import json,os,re,subprocess,sys,time,xml.etree.ElementTree as ET

TITLE=os.environ.get("KWAI_VIDEO_TITLE","").strip()
MEDIA_NAME=os.environ.get("KWAI_MEDIA_NAME","").strip()
VIDEO=os.environ.get("KWAI_ANDROID_VIDEO","").strip()
JOB_ID=os.environ.get("KWAI_QUEUE_JOB_ID","").strip()
PHASE=(sys.argv[1] if len(sys.argv)>1 else os.environ.get("KWAI_PUBLISH_PHASE","")).strip().lower()
READY_FILE="/tmp/kwai-publish-ready.json"

if not MEDIA_NAME or not VIDEO or not JOB_ID:
    print("STATE=FAILED_SAFE REASON=missing-media-or-job-identity"); sys.exit(69)
if PHASE not in ("prepare","commit"):
    print("STATE=FAILED_SAFE REASON=explicit-publish-phase-required"); sys.exit(68)

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

def find_node(words,retries=4,clickable=False):
    for _ in range(retries):
        try:r=dump()
        except Exception: time.sleep(1); continue
        for n in r.iter("node"):
            if clickable and n.attrib.get("clickable")!="true": continue
            if any(w in label(n) for w in words) and center(n.attrib.get("bounds","")):
                return n
        time.sleep(1)
    return None

def tap(words,retries=4):
    n=find_node(words,retries=retries)
    if n is None:return False
    p=center(n.attrib.get("bounds",""))
    adb("shell","input","tap",str(p[0]),str(p[1])); time.sleep(2); return True

def tap_node(n):
    p=center(n.attrib.get("bounds",""))
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1])); time.sleep(2); return True

def fill_title():
    if not TITLE:return True
    r=dump(); edits=[n for n in r.iter("node") if n.attrib.get("class","").endswith("EditText")]
    if not edits:return False
    p=center(edits[0].attrib.get("bounds",""))
    if not p:return False
    adb("shell","input","tap",str(p[0]),str(p[1]))
    safe=TITLE[:120].replace("%","%25").replace(" ","%s").replace("&","\\&").replace("(","\\(").replace(")","\\)")
    adb("shell","input","text",safe); time.sleep(1); return True

def prepare():
    adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1"); time.sleep(3)
    if not tap(("create","criar","post","publicar","+")):
        print("STATE=FAILED_SAFE REASON=composer-not-opened"); return 70
    tap(("album","álbum","gallery","galeria","upload","carregar","photos","fotos")); time.sleep(2)
    q=adb("shell","content","query","--uri","content://media/external/video/media","--projection","_id:_display_name:_size")
    rows=[x for x in q.splitlines() if MEDIA_NAME in x]
    if len(rows)!=1:
        print(f"STATE=FAILED_SAFE REASON=media-identity-not-unique COUNT={len(rows)}"); return 71
    print("STATE=MEDIA_IDENTITY_VERIFIED NAME="+MEDIA_NAME)
    r=dump(); candidates=[]
    for n in r.iter("node"):
        p=center(n.attrib.get("bounds",""))
        if p and p[1]>180 and n.attrib.get("clickable")=="true": candidates.append((p,label(n)))
    # Temporary fallback until the manifest-proven direct ACTION_SEND path is runtime-accepted.
    if not candidates:
        print("STATE=FAILED_SAFE REASON=no-selectable-media"); return 71
    adb("shell","input","tap",str(candidates[0][0][0]),str(candidates[0][0][1])); time.sleep(2)
    if not tap(("next","próximo","avançar","continue","continuar")):
        print("STATE=FAILED_SAFE REASON=media-selection-not-accepted"); return 75
    time.sleep(2)
    if not fill_title():
        print("STATE=FAILED_SAFE REASON=caption-field-missing"); return 76
    publish=find_node(("publish","publicar","post","compartilhar","share"),retries=3,clickable=True)
    if publish is None:
        print("STATE=FAILED_SAFE REASON=publish-control-not-ready"); return 72
    with open(READY_FILE,"w",encoding="utf-8") as f:
        json.dump({"job_id":JOB_ID,"media_name":MEDIA_NAME,"title":TITLE},f,ensure_ascii=False)
    print("STATE=CAPTION_SET")
    print("STATE=READY_TO_PUBLISH")
    return 0

def commit():
    try:
        with open(READY_FILE,encoding="utf-8") as f: ready=json.load(f)
    except Exception:
        print("STATE=FAILED_SAFE REASON=missing-ready-proof"); return 77
    if ready.get("job_id")!=JOB_ID or ready.get("media_name")!=MEDIA_NAME or ready.get("title")!=TITLE:
        print("STATE=FAILED_SAFE REASON=ready-proof-mismatch"); return 77
    publish=find_node(("publish","publicar","post","compartilhar","share"),retries=2,clickable=True)
    if publish is None:
        print("STATE=FAILED_SAFE REASON=publish-control-lost-before-commit"); return 72
    # Irreversible boundary. The caller MUST have obtained the central started ACK before invoking commit.
    print("STATE=PUBLISH_REQUESTED")
    if not tap_node(publish):
        print("STATE=UNCERTAIN REASON=publish-tap-failed-after-request"); return 90
    for _ in range(20):
        time.sleep(3)
        try: txt=" ".join(label(n) for n in dump().iter("node"))
        except Exception: continue
        if any(k in txt for k in ("failed","falhou","error","erro","try again","tente novamente")):
            print("STATE=UNCERTAIN REASON=post-request-visible-error"); return 90
        if any(k in txt for k in ("published","publicado","posted","enviado com sucesso","upload complete")):
            print("STATE=VERIFYING UI_MARKER=1"); return 0
        if any(k in txt for k in ("for you","para você","following","seguindo","profile","perfil")) and not any(k in txt for k in ("publish","publicar","post")):
            print("STATE=VERIFYING HOME_RETURN=1"); return 0
    print("STATE=UNCERTAIN REASON=post-request-timeout"); return 90

sys.exit(prepare() if PHASE=="prepare" else commit())
