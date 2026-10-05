#!/usr/bin/env python3
import os, re, subprocess, sys, time, xml.etree.ElementTree as ET

TITLE=os.environ.get("KWAI_VIDEO_TITLE","").strip()
VIDEO="/sdcard/Movies/anthares-upload.mp4"

def adb(*args):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30).stdout

def dump():
    adb("shell","uiautomator","dump","/sdcard/kwai-publish.xml")
    adb("pull","/sdcard/kwai-publish.xml","/tmp/kwai-publish.xml")
    return ET.parse("/tmp/kwai-publish.xml").getroot()

def label(n):
    return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()

def center(bounds):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2)

def tap(words, retries=4):
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
    if not TITLE:return
    r=dump()
    edits=[n for n in r.iter("node") if n.attrib.get("class","").endswith("EditText")]
    if not edits:return
    p=center(edits[0].attrib.get("bounds",""))
    if not p:return
    adb("shell","input","tap",str(p[0]),str(p[1]))
    safe=TITLE[:120].replace("%","%25").replace(" ","%s").replace("&","\\&").replace("(","\\(").replace(")","\\)")
    adb("shell","input","text",safe); time.sleep(1)

# Refresh media index and launch authenticated app.
adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE","-d","file://"+VIDEO)
adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
time.sleep(3)
# Create/upload button.
if not tap(("create","criar","post","publicar","+")): sys.exit(70)
# Select upload/gallery path.
tap(("album","álbum","gallery","galeria","upload","carregar","photos","fotos"))
time.sleep(2)
# Prefer the injected media by tapping first selectable video thumbnail.
r=dump()
candidates=[]
for n in r.iter("node"):
    s=label(n)
    if any(k in s for k in ("video","vídeo","0:","00:","anthares")) or n.attrib.get("clickable")=="true":
        p=center(n.attrib.get("bounds",""))
        if p and p[1] > 180: candidates.append(p)
if not candidates: sys.exit(71)
adb("shell","input","tap",str(candidates[0][0]),str(candidates[0][1])); time.sleep(2)
tap(("next","próximo","avançar","continue","continuar"))
time.sleep(2)
fill_title()
# Final publish action.
if not tap(("publish","publicar","post","compartilhar","share"),6): sys.exit(72)
# Wait for upload completion/home return; fail on visible errors.
for _ in range(60):
    time.sleep(3)
    try:
        txt=" ".join(label(n) for n in dump().iter("node"))
    except Exception: continue
    if any(k in txt for k in ("failed","falhou","error","erro","try again","tente novamente")): sys.exit(73)
    if any(k in txt for k in ("published","publicado","posted","enviado com sucesso","upload complete")):
        print("KWAI_PUBLISH_CONFIRMED_UI"); sys.exit(0)
    if any(k in txt for k in ("for you","para você","following","seguindo","profile","perfil")) and not any(k in txt for k in ("publish","publicar","post")):
        print("KWAI_PUBLISH_RETURNED_HOME"); sys.exit(0)
sys.exit(74)
