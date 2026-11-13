#!/usr/bin/env python3
"""Read-only public Kwai media proof on an ephemeral GitHub Actions runner.

No Android/ADB, authentication, production queue API, Neon writes or PC.
The only output is a JSON metadata report; all downloaded video is deleted.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright
import cv2
import numpy as np

JOBS = (
    {
        "id": "kwai-cortes-cOhqEaY3-08-g1-cOhqEaY3-08-1983-2023",
        "account": "lucasrosalem",
        "photo_id": "5200963257196327565",
        "started_ms": 1794599393942,
        "posted_ms": 1794599403839,
        "source_url": "https://anthares.us/wp-content/uploads/anthares-clips/2026/11/short_cOhqEaY3-08_g1_1983_2023.mp4",
        "source_sha256": "518658676f83aa49165b6f327004acc62eea94c2d9d5a984d48991069f2bc664",
    },
    {
        "id": "kwai-cortes-A7BsgCe3-oo-g1-A7BsgCe3-oo-7595-7635",
        "account": "lucasrosalem",
        "photo_id": "5236429103303004807",
        "started_ms": 1794529424700,
        "posted_ms": 1794529434243,
        "source_url": "https://anthares.us/wp-content/uploads/2026/10/short_A7BsgCe3-oo_g1_7595_7635.mp4",
        "source_sha256": "75f2c75e96d5a9696203281192198eb1d91d51ca55df4fe4d3f1a456987adf7d",
    },
    {
        "id": "kwai-cortes-ua-217fddfeae7c0a86be66d8e8511e2916",
        "account": "universoanthares",
        "photo_id": "5244028928629526188",
        "started_ms": 1794534747829,
        "posted_ms": 1794534757025,
        "source_url": "https://anthares.us/wp-content/uploads/2026/10/short_A7BsgCe3-oo_g1_7595_7635.mp4",
        "source_sha256": "75f2c75e96d5a9696203281192198eb1d91d51ca55df4fe4d3f1a456987adf7d",
    },
)
MEDIA_LIMIT = 80 * 1024 * 1024
FRACTIONS = (.12, .28, .44, .60, .76, .90)

def fetch_media(url: str, destination: Path) -> tuple[str, int]:
    u = urllib.parse.urlsplit(url)
    host = (u.hostname or "").lower()
    allowed = host in {"anthares.us","www.anthares.us","aws-br-cdn.kwai.net","ak-br-cdn.kwai.net"}
    if not allowed or u.scheme != "https" or not u.path.endswith(".mp4"):
        raise ValueError("MEDIA_ORIGIN_REJECTED")
    request = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=38) as response, destination.open("wb") as out:
        if response.status != 200:
            raise RuntimeError("MEDIA_HTTP_NOT_200")
        while True:
            data = response.read(256 * 1024)
            if not data:
                break
            size += len(data)
            if size > MEDIA_LIMIT:
                raise RuntimeError("MEDIA_LIMIT_EXCEEDED")
            digest.update(data)
            out.write(data)
    if size < 200000:
        raise RuntimeError("MEDIA_TOO_SHORT")
    return digest.hexdigest(), size

def sample(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError("VIDEO_DECODER_CANNOT_OPEN")
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = count / fps if fps > 0 else 0
        if not 4 <= duration <= 1500:
            raise RuntimeError("VIDEO_DURATION_INVALID")
        sift = cv2.SIFT_create(nfeatures=1250)
        features = []
        for fraction in FRACTIONS:
            cap.set(cv2.CAP_PROP_POS_MSEC, duration * fraction * 1000)
            ok, img = cap.read()
            if not ok:
                raise RuntimeError("VIDEO_FRAME_MISSING")
            h,w = img.shape[:2]
            scale = 460/max(h,w)
            img = cv2.resize(img,(max(1,int(w*scale)),max(1,int(h*scale))))
            features.append(sift.detectAndCompute(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY),None))
        return duration, features
    finally:
        cap.release()

def inliers(a,b):
    kp1,desc1=a
    kp2,desc2=b
    if desc1 is None or desc2 is None or min(len(desc1),len(desc2))<12:
        return 0
    pairs=cv2.BFMatcher().knnMatch(desc1,desc2,k=2)
    good=[x for pair in pairs if len(pair)==2 for x,y in [pair] if x.distance < .70*y.distance]
    if len(good)<9:
        return len(good)
    p1=np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    p2=np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    try:
        _,mask=cv2.findHomography(p1,p2,cv2.RANSAC,5)
        return int(mask.sum()) if mask is not None else 0
    except cv2.error:
        return 0

def media_proof(source: Path, public: Path) -> dict:
    source_duration, a = sample(source)
    public_duration, b = sample(public)
    scores=[max(inliers(x,y) for y in b) for x in a]
    qualifies=sum(n>=240 for n in scores)
    return {
        "source_duration_seconds": round(source_duration,3),
        "public_duration_seconds": round(public_duration,3),
        "best_source_frame_inliers": scores,
        "qualifying_distinct_frames": qualifies,
        "media_matched": qualifies >= 4 and abs(source_duration-public_duration) <= 3,
        "matcher":"sift_source_to_public_cdn_v1",
    }

def public_feed(page, handle: str, wanted: set[str]) -> dict:
    found={}
    def save(rows):
        for x in rows if isinstance(rows,list) else ():
            photo=str(x.get("photo_id_str") or "")
            if photo not in wanted:
                continue
            found[photo]={
                "photo_id":photo,"account":str(x.get("kwai_id") or "").lower(),
                "posted_ms":int(x.get("timestamp") or 0),
                "media_url":str((x.get("main_mv_urls") or [{}])[0].get("url") or ""),
            }
    def capture(response):
        if "/rest/o/w/pc/feed/profile" not in response.url:
            return
        try:
            obj=response.json()
            if response.status==200 and isinstance(obj,dict):
                save(obj.get("feeds"))
        except Exception:
            pass
    page.on("response",capture)
    try:
        response=page.goto("https://www.kwai.com/@"+handle,wait_until="domcontentloaded",timeout=25000)
        if response is None or response.status!=200:
            raise RuntimeError("PUBLIC_PROFILE_UNAVAILABLE")
        save(page.evaluate("() => window.__NUXT__?.data?.[0]?.feedsData?.feeds || []"))
        for _ in range(12):
            if len(found)==len(wanted):
                break
            page.evaluate("""() => {
                const el=document.querySelector('#main-container');
                if(el) el.scrollTop=el.scrollHeight;
                else window.scrollTo(0,document.body.scrollHeight);
            }""")
            page.wait_for_timeout(1000)
        return found
    finally:
        page.remove_listener("response",capture)

def main():
    report={
        "kind":"kwai_three_readonly_independent_media_proof_v1",
        "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "scope":"public_profile_and_public_cdn_only",
        "queue_mutations":0,"posts_submitted":0,"results":[]
    }
    by_account={}
    for job in JOBS:
        by_account.setdefault(job["account"],set()).add(job["photo_id"])
    feeds={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel="chrome",headless=True,
            args=["--no-first-run","--mute-audio","--disable-sync"])
        try:
            page=browser.new_page(locale="pt-BR")
            for handle,ids in by_account.items():
                feeds[handle]=public_feed(page,handle,ids)
        finally:
            browser.close()
    source_paths={}
    with tempfile.TemporaryDirectory(prefix="anthares-kwai-readonly-") as home:
        base=Path(home)
        for pos,job in enumerate(JOBS):
            result={k:job[k] for k in ("id","account","photo_id","started_ms","posted_ms","source_sha256")}
            result["public_url"]=f"https://www.kwai.com/@{job['account']}/video/{job['photo_id']}"
            result["status"]="INCONCLUSIVE_KEEP_QUARANTINED"
            try:
                post=feeds.get(job["account"],{}).get(job["photo_id"])
                if post is None or post["account"]!=job["account"] or post["posted_ms"]!=job["posted_ms"] or abs(job["posted_ms"]-job["started_ms"])>120000:
                    raise RuntimeError("PUBLIC_AUTHOR_TIMESTAMP_OR_ID_MISMATCH")
                if job["source_url"] not in source_paths:
                    path=base / ("source"+str(len(source_paths))+".mp4")
                    sha,size=fetch_media(job["source_url"],path)
                    if sha != job["source_sha256"]:
                        raise RuntimeError("SOURCE_SHA256_MISMATCH")
                    source_paths[job["source_url"]]=path
                url=post["media_url"]
                path=base / ("post"+str(pos)+".mp4")
                remote_sha,remote_size=fetch_media(url,path)
                proof=media_proof(source_paths[job["source_url"]],path)
                result["proof"]=proof
                result["public_media_sha256"]=remote_sha
                result["public_media_bytes"]=remote_size
                if proof["media_matched"]:
                    result["status"]="VERIFIED_PUBLIC_SOURCE_MEDIA_READONLY"
            except Exception as exc:
                result["error_type"]=type(exc).__name__
                result["error"]=str(exc)[:140]
            report["results"].append(result)
            print("KWAI_READBACK",result["account"],result["photo_id"],result["status"],
                  "frames="+str((result.get("proof") or {}).get("qualifying_distinct_frames","NA")),
                  "error="+result.get("error",""),flush=True)
    # This evidence is deliberately not an authenticated signed production
    # reconciliation: the appropriate queue owner must perform the confirm
    # action after verifying the external readback and its native state.
    Path("kwai-three-public-readback.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("READ_ONLY_REPORT_FILE=kwai-three-public-readback.json")
    print("QUEUE_STATUS_UNCHANGED=YES")
    print("MEDIA_FILES_REMOVED=YES")

if __name__=="__main__":
    main()
