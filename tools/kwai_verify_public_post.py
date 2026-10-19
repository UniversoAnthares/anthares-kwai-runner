#!/usr/bin/env python3
"""Read-only proof for a Kwai public share URL and the intended author.

This command never uploads, edits, deletes, or publishes media.
Only evidence verified from a real Kwai share link can confirm a job.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET

URL_RE=re.compile(r"^https://(?:k\.kwai\.com/p/[A-Za-z0-9_-]+|www\.kwai\.com/@[A-Za-z0-9_.-]+/photo/[0-9]+)$",re.I)
SERIAL=os.getenv("KWAI_UP_ADB_SERIAL","127.0.0.1:21543")
ADB=os.getenv("ANTHARES_ADB",r"C:\Users\Lucas\.kwai-up\platform-tools\adb.exe")
REMOTE="/sdcard/anthares-kwai-public-link-proof.xml"

def adb(*args: str, timeout=35) -> str:
    proc=subprocess.run([ADB,"-s",SERIAL,*args],capture_output=True,text=True,timeout=timeout)
    if proc.returncode:
        raise RuntimeError("adb_failed:"+str(proc.returncode)+":"+str(args[:2]))
    return proc.stdout

def normal(text: str) -> str:
    x=unicodedata.normalize("NFKD",str(text)).encode("ascii","ignore").decode("ascii").casefold()
    return " ".join(re.findall(r"[a-z0-9]+",x))

def snapshot() -> list[dict]:
    adb("shell","uiautomator","dump",REMOTE,timeout=55)
    doc=ET.fromstring(adb("shell","cat",REMOTE,timeout=25))
    return [dict(node.attrib) for node in doc.iter("node")]

def visible(nodes:list[dict]) -> str:
    return " ".join((n.get("text") or "")+" "+(n.get("content-desc") or "") for n in nodes)

def center(bounds:str):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    a,b,c,d=map(int,m.groups())
    return ((a+c)//2,(b+d)//2)

def verify(url:str,expected_title:str,expected_handle:str,author_display:str):
    if not URL_RE.fullmatch(url):raise RuntimeError("invalid_public_share_url")
    if normal(expected_handle)!="lucasrosalem":raise RuntimeError("unexpected_target_account")
    adb("shell","am","start","-a","android.intent.action.VIEW","-d",url)
    time.sleep(4)
    nodes=snapshot()
    blob=normal(visible(nodes))
    expected=normal(expected_title)
    # Exact title or 6 leading significant words in order, accommodating
    # "EP N |" prefixes and hashtag truncation on small Android screens.
    words=[x for x in expected.split() if x not in ("universo","anthares")]
    phrase=" ".join(words)
    match=(len(phrase)>=12 and phrase in blob) or (len(words)>=4 and " ".join(words[:min(6,len(words))]) in blob)
    author=normal(author_display)
    if not match:raise RuntimeError("video_title_mismatch")
    if not author or author not in blob:raise RuntimeError("video_author_mismatch")
    matching_author_nodes=[node for node in nodes if normal(node.get("text",""))==author and center(node.get("bounds",""))]
    if not matching_author_nodes:
        raise RuntimeError("author_profile_entry_missing")
    x,y=center(matching_author_nodes[0]["bounds"])
    adb("shell","input","tap",str(x),str(y))
    time.sleep(2)
    profile_nodes=snapshot()
    profile_blob=normal(visible(profile_nodes))
    if normal(expected_handle) not in profile_blob:
        raise RuntimeError("public_video_author_handle_mismatch")
    return {"ok":True,"public_url":url,"author_display":author_display,
            "expected_account":expected_handle,"title_match":True,
            "checked_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "method":"kwai_public_deeplink_title_and_author_profile_handle"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True)
    p.add_argument("--title",required=True)
    p.add_argument("--account",default="lucasrosalem")
    p.add_argument("--display-name",default="Lucas Rosalem")
    p.add_argument("--evidence-file")
    opts=p.parse_args()
    evidence=verify(opts.url,opts.title,opts.account,opts.display_name)
    if opts.evidence_file:
        dest=pathlib.Path(opts.evidence_file)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    print("KWAI_PUBLIC_LINK_VERIFIED="+json.dumps(evidence,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
