#!/usr/bin/env python3
"""Synchronize today’s CORTES clips to @lucasrosalem4 without access to WP secrets.

The canonical Neon publisher stores immutable clip URLs even after TikTok
@universo.anthares finishes. Fetch them with signed GitHub Actions OIDC, and
atomically materialize a per-account local manifest. Never publish here.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

AUDIENCE="https://anthares-remote-primary.vercel.app/api/cortes-tiktok"
SOURCE="https://br-crimson-unit-b89nau08-cortestiktok.compute.c-14.us-east-1.aws.neon.tech/"
ACCOUNT="lucasrosalem4"
HOME=Path(r"C:\Users\Lucas\AppData\Local\Anthares\TikTok\secondary-publisher")
SEGMENT=re.compile(r"^g[0-9]+:([A-Za-z0-9_-]{6,60}):[0-9]+:[0-9]+$")


def request_json(url, token=None, timeout=25):
    headers={"Accept":"application/json"}
    if token:
        headers["Authorization"]="Bearer "+token
    request=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(request,timeout=timeout) as response:
        if "json" not in str(response.headers.get("Content-Type") or "").lower():
            raise RuntimeError("SECONDARY_MANIFEST_INVALID_CONTENT_TYPE")
        data=json.load(response)
    if not isinstance(data,dict):
        raise RuntimeError("SECONDARY_MANIFEST_JSON_OBJECT_REQUIRED")
    return data


def oidc():
    base=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    authorization=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not base or not authorization or os.environ.get("GITHUB_REF")!="refs/heads/main":
        raise RuntimeError("SECONDARY_MANIFEST_CANONICAL_GITHUB_IDENTITY_REQUIRED")
    url=base+("&" if "?" in base else "?")+urllib.parse.urlencode({"audience":AUDIENCE})
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+authorization,
                                            "Accept":"application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=25) as response:
                result=json.load(response)
            value=str(result.get("value") or "")
            if 200<=len(value)<=16000:
                return value
            raise RuntimeError("SECONDARY_MANIFEST_JWT_UNAVAILABLE")
        except urllib.error.HTTPError as error:
            if error.code not in (500,502,503,504) or attempt==3:
                raise
        except (urllib.error.URLError,OSError):
            if attempt==3:
                raise
        time.sleep((2,5,10)[attempt])
    raise RuntimeError("SECONDARY_MANIFEST_OIDC_RETRIES_EXHAUSTED")


def valid_clip(clip):
    if not isinstance(clip,dict):
        return False
    match=SEGMENT.fullmatch(str(clip.get("segment_id") or ""))
    if not match or str(clip.get("source_id") or "")!=match.group(1):
        return False
    url=urllib.parse.urlsplit(str(clip.get("media_url") or ""))
    if url.scheme!="https" or url.hostname not in ("anthares.us","www.anthares.us"):
        return False
    if not url.path.startswith("/wp-content/uploads/") or url.username or url.password:
        return False
    try:
        return 30<=float(clip.get("duration_seconds") or 0)<=90 and len(str(clip.get("title") or ""))>=8
    except (TypeError,ValueError):
        return False


def main():
    if os.name!="nt":
        raise RuntimeError("SECONDARY_MANIFEST_WINDOWS_RUNNER_REQUIRED")
    response=request_json(SOURCE+"?action=source-manifest",oidc())
    if not response.get("ok") or response.get("account")!=ACCOUNT:
        raise RuntimeError("SECONDARY_MANIFEST_UPSTREAM_ACCOUNT_UNVERIFIED")
    day=str(response.get("date") or "")
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",day):
        raise RuntimeError("SECONDARY_MANIFEST_DAY_INVALID")
    if day!=datetime.now().strftime("%Y-%m-%d"):
        raise RuntimeError("SECONDARY_MANIFEST_PC_DATE_MISMATCH")
    received=response.get("clips")
    if not isinstance(received,list) or len(received)>100:
        raise RuntimeError("SECONDARY_MANIFEST_CAP_OR_FORMAT_INVALID")
    if any(not valid_clip(clip) for clip in received):
        raise RuntimeError("SECONDARY_MANIFEST_CLIP_VALIDATION_FAILED")
    HOME.mkdir(parents=True,exist_ok=True)
    dest=HOME/(day+"-queue-manifest.json")
    merged={}
    if dest.exists():
        old=json.loads(dest.read_text(encoding="utf-8"))
        if old.get("account")!=ACCOUNT or old.get("date")!=day:
            raise RuntimeError("SECONDARY_MANIFEST_PREVIOUS_ACCOUNT_INVALID")
        for c in old.get("clips",[]):
            if valid_clip(c):
                merged[c["segment_id"]]=c
    for clip in received:
        merged[clip["segment_id"]]={
            "segment_id":clip["segment_id"],
            "source_id":clip["source_id"],
            "media_url":clip["media_url"],
            "title":clip["title"],
            "duration_seconds":float(clip["duration_seconds"]),
        }
    if len(merged)>100:
        raise RuntimeError("SECONDARY_MANIFEST_MERGED_CAP_EXCEEDED")
    output={"account":ACCOUNT,"date":day,"origin":"authenticated_neon_primary_ledger",
            "clip_count":len(merged),"clips":list(merged.values())}
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=HOME,
                                     prefix="manifest-",suffix=".tmp",delete=False) as temp:
        json.dump(output,temp,ensure_ascii=False,indent=2)
        temporary=Path(temp.name)
    os.replace(temporary,dest)
    print("SECONDARY_TIKTOK_MANIFEST_REFRESH_OK count="+str(len(merged))+" day="+day,flush=True)
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("SECONDARY_TIKTOK_MANIFEST_ERROR="+type(exc).__name__,file=sys.stderr,flush=True)
        sys.exit(2)
