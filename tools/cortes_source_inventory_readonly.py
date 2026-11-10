#!/usr/bin/env python3
"""Read-only cross-check of WordPress CORTES live inventory against YouTube.

Print only public YouTube IDs and sanitized status facts. No source-cycle
mutations, publisher operations, social leases, downloads or cleanup.
"""
from __future__ import annotations
import base64
import json
import os
import subprocess
import sys
import urllib.request

WP="https://anthares.us/wp-json/anthares/v1/cortes/state"
STREAMS="https://www.youtube.com/@UniversoAnthares/streams"

def get_state():
    site=str(os.getenv("WP_SITE_URL") or "").rstrip("/")
    user=str(os.getenv("WP_USERNAME") or "")
    pwd="".join(str(os.getenv("WP_APP_PASSWORD") or "").split())
    if site!="https://anthares.us" or not user or not pwd:
        raise RuntimeError("CORTES_SOURCE_QA_AUTH_UNAVAILABLE")
    basic=base64.b64encode(f"{user}:{pwd}".encode()).decode()
    req=urllib.request.Request(WP,headers={"Authorization":"Basic "+basic,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as r: obj=json.load(r)
    if not isinstance(obj,dict) or not isinstance(obj.get("items"),list):
        raise RuntimeError("CORTES_SOURCE_QA_WP_INVALID_STATE")
    return obj

def get_streams():
    cmd=[sys.executable,"-m","yt_dlp","--flat-playlist",
         "--dump-single-json","--playlist-end","500","--no-warnings",
         "--extractor-args","youtube:player_client=mweb",STREAMS]
    proc=subprocess.run(cmd,text=True,capture_output=True,timeout=90,check=False)
    if proc.returncode or not proc.stdout.strip():
        raise RuntimeError("CORTES_SOURCE_QA_YOUTUBE_LIST_UNAVAILABLE")
    obj=json.loads(proc.stdout)
    if not isinstance(obj.get("entries"),list):
        raise RuntimeError("CORTES_SOURCE_QA_YOUTUBE_LIST_INVALID")
    rows=[r for r in obj["entries"]
          if isinstance(r,dict) and str(r.get("live_status") or "") not in
          ("is_live","is_upcoming","post_live")]
    ids=[str(r.get("id") or "").strip() for r in rows if str(r.get("id") or "").strip()]
    if not ids or len(ids)!=len(set(ids)):
        raise RuntimeError("CORTES_SOURCE_QA_YOUTUBE_DUPLICATE_OR_EMPTY")
    return ids

def audit(state,stream_ids):
    present=set(stream_ids)
    current={str(row.get("video_id")):row for row in state["items"]
             if isinstance(row,dict) and row.get("video_id")
             and str(row.get("source_kind") or "live")!="regular_video"}
    missing=[]
    for vid,row in current.items():
        if vid in present or row.get("legacy_completed") or str(row.get("stage") or "")=="completed":
            continue
        phases=row.get("phases") or {}
        missing.append({
            "video_id":vid,
            "stage":str(row.get("stage") or ""),
            "kind":str(row.get("source_kind") or "live"),
            "chronological_index":row.get("chronological_index"),
            "has_source_file":bool(row.get("source_file")),
            "has_source_url":bool(row.get("source_url")),
            "long_analyzed":bool((phases.get("long") or {}).get("analyzed")),
            "short_analyzed":bool((phases.get("short") or {}).get("analyzed")),
            "registered_clips":len(row.get("clips") or [])
        })
    blocker=state.get("blocker") or {}
    return {"status":"READ_ONLY",
            "youtube_streams":len(stream_ids),
            "wordpress_lives":len(current),
            "active_missing_count":len(missing),
            "active_missing":missing,
            "blocker_id":str(blocker.get("video_id") or ""),
            "blocker_stage":str(blocker.get("stage") or ""),
            "writes":0}

def main():
    state=get_state()
    ids=get_streams()
    result=audit(state,ids)
    print("CORTES_SOURCE_INVENTORY_QA="+json.dumps(result,ensure_ascii=False,separators=(",",":")))
    return 0 if result["active_missing_count"]==0 else 2

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        msg=str(exc)
        if not msg.startswith("CORTES_SOURCE_QA_"):msg=type(exc).__name__
        print("::error::CORTES_SOURCE_QA_BLOCKED="+msg)
        raise SystemExit(3)
