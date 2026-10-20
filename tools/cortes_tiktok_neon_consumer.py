#!/usr/bin/env python3
"""TikTok CORTES consumer: fenced Neon job -> Northflank UI -> profile -> WP callback.

Never repeats a request once publication may have started. Credentials remain
in their existing independent GitHub Actions repositories.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from urllib.parse import urlsplit

QUEUE="https://anthares-remote-primary.vercel.app/api/cortes-tiktok"
WORKER="https://anthares-tiktok-worker.anthares1.workers.dev"
ACCOUNT="universo.anthares"

class Blocked(RuntimeError): pass

def get_or_post(url, headers, payload=None, timeout=60):
    if urlsplit(url).hostname not in ("anthares-remote-primary.vercel.app",
        "anthares-tiktok-worker.anthares1.workers.dev","anthares.us"):
        raise Blocked("UNTRUSTED_TARGET")
    h={**headers,"Accept":"application/json"}
    if payload is not None: h["Content-Type"]="application/json"
    req=urllib.request.Request(url,headers=h,
        method="POST" if payload is not None else "GET",
        data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode())
    with urllib.request.urlopen(req,timeout=timeout) as r: response=json.load(r)
    if not isinstance(response,dict):raise Blocked("INVALID_REMOTE_RESPONSE")
    return response

def oidc_headers():
    url=os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL","")
    auth=os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url or not auth:raise Blocked("GITHUB_OIDC_MISSING")
    req=urllib.request.Request(
      url+("&" if "?" in url else "?")+urllib.parse.urlencode({"audience":QUEUE}),
      headers={"Authorization":"Bearer "+auth})
    with urllib.request.urlopen(req,timeout=25) as r: token=str(json.load(r).get("value") or "")
    if not token:raise Blocked("OIDC_TOKEN_UNAVAILABLE")
    return {"Authorization":"Bearer "+token}

def worker_headers():
    shared=os.getenv("ARA_SHARED","").strip()
    if not shared:raise Blocked("ARA_SHARED_SECRET_MISSING")
    return {"Authorization":"Bearer "+shared}

def marker(sid):
    return "#anthares"+hashlib.sha256((ACCOUNT+":"+sid).encode()).hexdigest()[:10]

def video_id(inv,mark):
    if inv.get("ok") is not True or str(inv.get("account") or "").lstrip("@").lower()!=ACCOUNT:
        raise Blocked("ACCOUNT_IDENTITY_UNVERIFIED")
    found={}
    for row in inv.get("items") or []:
        if not isinstance(row,dict):continue
        rid=str(row.get("id") or "")
        if re.fullmatch(r"[0-9]{12,25}",rid) and mark in " ".join(str(row.get("text") or "").lower().split()):
            found[rid]=True
    if len(found)>1:raise Blocked("DUPLICATE_PROFILE_MARKER")
    return next(iter(found),"")

def queue_call(action,auth,payload):
    return get_or_post(QUEUE+"?action="+action,auth,payload,timeout=60)

def callback(job,rid):
    expected="https://anthares.us/wp-json/anthares/v1/cortes/clip-network-callback"
    if str(job.get("callback_url") or "")!=expected:raise Blocked("CALLBACK_URL_INVALID")
    token=str(job.get("callback_token") or "")
    if len(token)<32:raise Blocked("CALLBACK_TOKEN_MISSING")
    ack=get_or_post(expected,{},{
      "video_id":job["source_id"],"clip_id":job["segment_id"],"network":"tiktok",
      "attachment_id":int(job["attachment_id"]),"account_id":"primary",
      "status":"completed","remote_id":rid,"token":token},timeout=50)
    if ack.get("ok") is not True:raise Blocked("WORDPRESS_CALLBACK_UNCONFIRMED")

def inventory(auth):
    return get_or_post(WORKER+"/profile-inventory",auth,timeout=125)

def complete(job,rid,qa):
    callback(job,rid)
    result=queue_call("confirm",qa,{"id":job["id"],"lease_generation":int(job["lease_generation"]),"remote_id":rid})
    if result.get("ok") is not True:raise Blocked("NEON_CONFIRM_UNACKNOWLEDGED")
    print("TIKTOK_CORTES_CONFIRMED remote_id="+rid,flush=True)

def run():
    qa=oidc_headers();wa=worker_headers()
    session=get_or_post(WORKER+"/session-status",wa,timeout=65)
    if not (session.get("ok") and session.get("bootstrapped") and
            session.get("identity_verified") and session.get("ready_for_tiktok")):
        raise Blocked("TIKTOK_SESSION_UNREADY")
    current=inventory(wa)
    video_id(current,marker("preflight-unique-never-uploaded"))
    q=get_or_post(QUEUE+"?action=status",qa)
    if not q.get("ok"):raise Blocked("NEON_STATUS_UNAVAILABLE")
    if os.getenv("CORTES_TIKTOK_PREFLIGHT","0")=="1":
        print("TIKTOK_REMOTE_READY account=@"+ACCOUNT+" queue="+str(q.get("count") or {}),flush=True)
        return 0
    item=queue_call("claim",qa,{})
    if item.get("ok") is not True:raise Blocked("NEON_CLAIM_FAILED")
    job=item.get("job")
    if not job:
        print("TIKTOK_CORTES_IDLE mode="+str(item.get("mode") or "empty"),flush=True)
        return 0
    sid=str(job.get("segment_id") or "")
    gen=int(job.get("lease_generation") or 0)
    if not sid or gen<1:raise Blocked("INVALID_FENCED_JOB")
    found=video_id(current,marker(sid))
    if found:
        complete(job,found,qa)
        return 0
    if item.get("mode")=="reconcile" or job.get("publication_started_at"):
        raise Blocked("UNCERTAIN_POST_ABSENT_FROM_PROFILE_REVIEW_REQUIRED")
    if job.get("status")!="leased":raise Blocked("LEASE_NOT_CURRENT")
    if not 30<=float(job.get("duration_seconds") or 0)<=90:raise Blocked("INVALID_CLIP_DURATION")
    url=str(job.get("media_url") or "")
    if not url.startswith("https://anthares.us/"):raise Blocked("MEDIA_ORIGIN_INVALID")
    started=queue_call("start",qa,{"id":job["id"],"lease_generation":gen})
    if started.get("ok") is not True:raise Blocked("PUBLISH_FENCE_REJECTED")
    title=" ".join(str(job.get("title") or "Literatura e escrita").split())
    text=title[:70].rstrip(" .,-")+" "+marker(sid)
    print("TIKTOK_PUBLISH_BOUNDARY_CROSSED segment="+sid,flush=True)
    try:
        published=get_or_post(WORKER+"/publish-url",wa,{
          "media_url":url,
          "plan":{"segment_id":sid,"source_id":str(job["source_id"]),
                  "source_title":title,"title":text,
                  "expected_tiktok_username":ACCOUNT},
        },timeout=415)
        if not published.get("ok") or not published.get("confirmed"):
            raise Blocked("PUBLISH_UI_NOT_CONFIRMED")
        for attempt in range(5):
            if attempt:time.sleep(8)
            rid=video_id(inventory(wa),marker(sid))
            if rid:
                complete(job,rid,qa)
                return 0
        raise Blocked("PROFILE_VERIFICATION_PENDING")
    except Exception:
        try:queue_call("fail",qa,{"id":job["id"],"lease_generation":gen,"error":"publication_uncertain_verify_profile"})
        except Exception:pass
        raise Blocked("PUBLISH_UNCERTAIN_NEVER_AUTO_RETRY")

if __name__=="__main__":
    try:sys.exit(run())
    except Exception as e:
        label=str(e) if isinstance(e,Blocked) else type(e).__name__
        print("TIKTOK_CORTES_CONSUMER_BLOCKED "+label,file=sys.stderr)
        sys.exit(2)
