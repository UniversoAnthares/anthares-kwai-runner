#!/usr/bin/env python3
"""GitHub-hosted LinkedIn CORTES queue producer; no owner-PC dependency.

Only enqueues uniquely identified 30–90-second WordPress master clips in the
canonical Neon queue. Does NOT create Buffer posts, confirm publication,
or erase masters. OIDC is scoped to one workflow on main.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error

NEON="https://anthares-remote-primary.vercel.app/api/cortes-queue"
TARGET="linkedin:primary"


def require_cloud():
    if (os.getenv("GITHUB_ACTIONS")!="true" or os.getenv("RUNNER_ENVIRONMENT")!="github-hosted"
            or os.getenv("RUNNER_OS")!="Linux"):
        raise RuntimeError("LINKEDIN_FANOUT_MUST_RUN_IN_CLOUD")
    for name in ("WP_SITE_URL","WP_USERNAME","WP_APP_PASSWORD",
                 "ACTIONS_ID_TOKEN_REQUEST_URL","ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        if not os.getenv(name):
            raise RuntimeError("LINKEDIN_FANOUT_MISSING_"+name)
    if os.environ["WP_SITE_URL"].rstrip("/")!="https://anthares.us":
        raise RuntimeError("LINKEDIN_FANOUT_WRONG_WORDPRESS_SITE")


def wp_state():
    user=os.environ["WP_USERNAME"].strip()
    password="".join(os.environ["WP_APP_PASSWORD"].split())
    token=base64.b64encode((user+":"+password).encode("utf-8")).decode("ascii")
    req=urllib.request.Request(
        "https://anthares.us/wp-json/anthares/v1/cortes/state",
        headers={"Authorization":"Basic "+token,"Accept":"application/json"},
    )
    with urllib.request.urlopen(req,timeout=25) as response:
        data=json.load(response)
    if not isinstance(data,dict):
        raise RuntimeError("LINKEDIN_FANOUT_WP_STATE_INVALID")
    return data


def candidate_jobs(state):
    sources={}
    for source in list(state.get("items") or [])+[state.get("blocker")]:
        if isinstance(source,dict) and source.get("video_id"):
            sources[str(source["video_id"])]=source
    output={}
    for source in sources.values():
        sid=str(source["video_id"])
        for clip in source.get("clips") or []:
            if not isinstance(clip,dict) or clip.get("type")!="short" or not clip.get("stored"):
                continue
            segment=str(clip.get("segment_id") or clip.get("clip_id") or "")
            parts=segment.rsplit(":",2)
            if len(parts)!=3: continue
            try:
                start,end=int(parts[-2]),int(parts[-1])
                duration=float(clip.get("duration_seconds") or 0)
                attachment=int(clip.get("attachment_id") or 0)
            except (ValueError,TypeError):continue
            if start<0 or end<=start or not 30<=duration<=90 or attachment<=0:continue
            media=str(clip.get("url") or "")
            parsed=urllib.parse.urlparse(media)
            if (parsed.scheme!="https" or parsed.hostname not in ("anthares.us","www.anthares.us")
                    or parsed.username or parsed.password or not parsed.path.lower().endswith(".mp4")):continue
            title=str(clip.get("title") or source.get("title") or "").strip()
            if not title:continue
            key=(sid,segment)
            if key in output and output[key]["media_url"]!=media:
                raise RuntimeError("LINKEDIN_FANOUT_MASTER_IDENTITY_COLLISION")
            digest=hashlib.sha256((sid+"|"+segment+"|"+TARGET).encode()).hexdigest()[:32]
            jobid="cortes-fanout-linkedin-"+digest
            output[key]={
                "id":jobid,"dedupe_key":jobid,"executor":"social_video",
                "platform":"linkedin","target_key":TARGET,"account_id":"primary",
                "master_id":sid,"source_id":sid,"segment_id":segment,
                "duration_class":"short","duration_seconds":duration,
                "source_start":start,"source_end":end,
                "media_sha256":hashlib.sha256((sid+"|"+segment+"|"+media).encode()).hexdigest(),
                "media_hash_kind":"dispatch_identity",
                "media_url":media,"video_url":media,"title":title,"video_title":title,
                "cortes_attachment_id":attachment,
                "planned_at":str(clip.get("planned_at") or ""),
            }
    return [output[k] for k in sorted(output)]


def oidc():
    u=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    u+=("&" if "?" in u else "?")+urllib.parse.urlencode({"audience":NEON})
    req=urllib.request.Request(u,headers={
        "Authorization":"Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
        "Accept":"application/json",
    })
    with urllib.request.urlopen(req,timeout=15) as response:
        return json.load(response)["value"]


def enqueue(job):
    req=urllib.request.Request(NEON+"?action=enqueue",
       data=json.dumps(job,ensure_ascii=False,separators=(",",":")).encode("utf-8"),
       method="POST",
       headers={"Authorization":"Bearer "+oidc(),"Content-Type":"application/json",
                "User-Agent":"AntharesLinkedInCloudFanout/1.0"},
    )
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            result=json.load(response)
    except urllib.error.HTTPError as e:
        raise RuntimeError("LINKEDIN_NEON_ENQUEUE_HTTP_"+str(e.code)) from None
    except (OSError,ValueError):
        raise RuntimeError("LINKEDIN_NEON_ENQUEUE_UNKNOWN_RESULT") from None
    row=result.get("job") or {}
    if not result.get("ok") or row.get("id")!=job["id"]:
        raise RuntimeError("LINKEDIN_NEON_ENQUEUE_NOT_ACKNOWLEDGED")
    if result.get("deduped") and (result.get("reason")!="identity" or row.get("target_key")!=TARGET):
        raise RuntimeError("LINKEDIN_NEON_WRONG_DEDUPE")
    return bool(result.get("deduped"))


def main():
    require_cloud()
    jobs=candidate_jobs(wp_state())
    if jobs:
        budget=50
        chunks=(len(jobs)+budget-1)//budget
        index=(int(time.time())//900)%chunks
        jobs_in_this_run=jobs[index*budget:(index+1)*budget]
    else:
        jobs_in_this_run=[]
    new=existing=0
    for job in jobs_in_this_run:
        if enqueue(job):existing+=1
        else:new+=1
    print(json.dumps({"linkedin_fanout":"PASS","eligible":len(jobs),
        "visited":len(jobs_in_this_run),"enqueued":new,"already_known":existing},separators=(",",":")))


if __name__=="__main__":
    try:main()
    except Exception as err:
        print(json.dumps({"linkedin_fanout":"BLOCKED","error":str(err) if str(err).startswith("LINKEDIN_") else type(err).__name__}))
        raise SystemExit(2)
