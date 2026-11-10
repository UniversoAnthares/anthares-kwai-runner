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
        try:
            original_index=int(row.get("chronological_index") or 0)
        except (ValueError,TypeError):
            original_index=0
        proposed_pos=len(current)-original_index
        proposed_pos=proposed_pos if 0<=proposed_pos<=len(stream_ids) else None
        missing.append({
            "suggested_public_insertion_index":proposed_pos,
            "previous_public_video_id":(stream_ids[proposed_pos-1]
                                        if proposed_pos is not None and proposed_pos>0 else None),
            "next_public_video_id":(stream_ids[proposed_pos]
                                    if proposed_pos is not None and proposed_pos<len(stream_ids) else None),
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
    phases=blocker.get("phases") or {}
    raw_clips=[clip for clip in (blocker.get("clips") or []) if isinstance(clip,dict)]
    locked={
        "video_id":str(blocker.get("video_id") or ""),
        "stage":str(blocker.get("stage") or ""),
        "long_analyzed":bool((phases.get("long") or {}).get("analyzed")),
        "short_analyzed":bool((phases.get("short") or {}).get("analyzed")),
        "long_clips":sum(c.get("type")=="long" for c in raw_clips),
        "short_clips":sum(c.get("type")=="short" for c in raw_clips),
        "files_deleted":bool(blocker.get("files_deleted_at")),
        "cycle_generation":blocker.get("cycle_generation"),
        "total_clips":len(raw_clips),
    }
    result_by_id={str(r.get("video_id") or ""):r for r in current.values()}
    counterpart=result_by_id.get(locked["video_id"]) or {}
    item_phases=counterpart.get("phases") or {}
    locked["registry_stage"]=str(counterpart.get("stage") or "")
    locked["registry_long_analyzed"]=bool((item_phases.get("long") or {}).get("analyzed"))
    locked["registry_short_analyzed"]=bool((item_phases.get("short") or {}).get("analyzed"))
    locked["registry_clips"]=len(counterpart.get("clips") or [])
    locked["generation_closed_at"]=bool(counterpart.get("generation_closed_at"))
    locked["generation_close_reason"]=str(counterpart.get("generation_close_reason") or "")
    locked["generation_closed_cycle"]=counterpart.get("generation_closed_cycle")
    locked["generation_preserved_clips"]=counterpart.get("generation_preserved_clips")
    locked["registry_source_file_available"]=bool(counterpart.get("source_file"))
    locked["registry_files_deleted_at"]=bool(counterpart.get("files_deleted_at"))
    return {"status":"READ_ONLY",
            "locked_source":locked,
            "youtube_streams":len(stream_ids),
            "wordpress_lives":len(current),
            "active_missing_count":len(missing),
            "active_missing":missing,
            "blocker_id":str(blocker.get("video_id") or ""),
            "blocker_stage":str(blocker.get("stage") or ""),
            "writes":0}

def verify_single_video(video_id):
    """Probe an exact missing video URL without downloading it or changing WP."""
    if not isinstance(video_id,str) or len(video_id)!=11 or any(
            not (c.isalnum() or c in "-_") for c in video_id):
        return "INVALID_VIDEO_ID"
    url="https://www.youtube.com/watch?v="+video_id
    cmd=[sys.executable,"-m","yt_dlp","--skip-download","--dump-single-json",
         "--no-warnings","--extractor-args","youtube:player_client=web_safari",url]
    try:
        proc=subprocess.run(cmd,text=True,capture_output=True,timeout=75,check=False)
    except subprocess.TimeoutExpired:
        return "UNVERIFIED_TIMEOUT"
    if proc.returncode==0:
        try:
            video=json.loads(proc.stdout)
            if str(video.get("id") or "") != video_id:
                return "UNVERIFIED_IDENTITY_MISMATCH"
            return ("PUBLIC_AVAILABLE" if video.get("is_live") is not True
                    else "UNVERIFIED_IS_LIVE")
        except (ValueError,TypeError):
            return "UNVERIFIED_JSON"
    err=proc.stderr.lower()
    if "private video" in err or "this video is private" in err:
        return "PRIVATE_VIDEO"
    if "video unavailable" in err or "video has been removed" in err:
        return "VIDEO_UNAVAILABLE"
    return "UNVERIFIED_EXTRACTION_ERROR"

def main():
    state=get_state()
    ids=get_streams()
    result=audit(state,ids)
    for row in result['active_missing'][:3]:
        row['direct_video_status']=verify_single_video(row['video_id'])
    print("CORTES_SOURCE_INVENTORY_QA="+json.dumps(result,ensure_ascii=False,separators=(",",":")))
    # Separate WordPress/CAS cycle readback, never changed by this audit.
    site="https://anthares.us"
    auth=base64.b64encode((str(os.environ["WP_USERNAME"])+":"+
        "".join(str(os.environ["WP_APP_PASSWORD"]).split())).encode()).decode()
    req=urllib.request.Request(site+"/wp-json/anthares/v1/cortes/source-cycle",
         headers={"Authorization":"Basic "+auth,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as response:
        cycle=json.load(response)
    lock=cycle.get("daily_lock") or {}
    source=lock.get("source") or {}
    print("CORTES_CYCLE_LOCK_READONLY="+json.dumps({
        "locked_source":str(source.get("video_id") or ""),
        "locked_date":str(lock.get("date") or ""),
        "locked_status":str(lock.get("status") or ""),
        "live_cursor":cycle.get("live_cursor"),
        "live_cycle_generation":cycle.get("live_cycle_generation"),
        "source_kind":str(source.get("source_kind") or ""),
        "writes":0
    },ensure_ascii=False,separators=(",",":")))
    return 0 if result["active_missing_count"]==0 else 2

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        msg=str(exc)
        if not msg.startswith("CORTES_SOURCE_QA_"):msg=type(exc).__name__
        print("::error::CORTES_SOURCE_QA_BLOCKED="+msg)
        raise SystemExit(3)
