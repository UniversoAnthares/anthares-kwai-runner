#!/usr/bin/env python3
"""GitHub-hosted CORTES Instagram publisher.

Fetch at most one eligible Neon master, queue at most one Buffer video and
reconcile up to two previously scheduled posts. Never run from owner's PC.
Every queue operation is signed with a new GitHub OIDC token, scoped to this
exact main-branch workflow. A Buffer schedule is not a Instagram confirmation.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from social_adapters.buffer_three_channels import api, schedule, BufferBlocked, PINNED_CHANNELS

BASE="https://anthares-remote-primary.vercel.app/api/cortes-queue"
INSTAGRAM_ID=PINNED_CHANNELS["instagram"][0]
TARGET="instagram:universoanthares"
OWNER="buffer-instagram:github-cloud-v1"


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
            os.getenv("RUNNER_ENVIRONMENT")!="github-hosted" or
            os.getenv("RUNNER_OS")!="Linux"):
        raise RuntimeError("CORTES_INSTAGRAM_CLOUD_ONLY")
    if not os.getenv("BUFFER_API_KEY"):
        raise RuntimeError("BUFFER_CREDENTIAL_UNAVAILABLE")
    if not os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") or not os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        raise RuntimeError("GITHUB_OIDC_UNAVAILABLE")
    os.environ["BUFFER_INSTAGRAM_CHANNEL_ID"]=INSTAGRAM_ID


def oidc():
    url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    url+=("&" if "?" in url else "?")+urllib.parse.urlencode({"audience":BASE})
    req=urllib.request.Request(url,headers={
        "Authorization":"Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
        "Accept":"application/json",
    })
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.load(r)["value"]


def queue(action,payload=None):
    from tools.cortes_queue_ha import post
    result=post("buffer-"+action,payload or {},oidc,primary="neon")
    if not result.get("ok"):
        raise RuntimeError("NEON_BUFFER_ACTION_REJECTED_"+action)
    return result


def verify_sent_post(remote_id):
    query=('query { post(input: { id: '+json.dumps(str(remote_id))+
           ' }) { id status externalLink channelId schedulingType } }')
    row=api(query).get("post") or {}
    if str(row.get("id") or "")!=str(remote_id) or str(row.get("channelId") or "")!=INSTAGRAM_ID:
        raise RuntimeError("BUFFER_INSTAGRAM_POST_IDENTITY_UNVERIFIED")
    if str(row.get("schedulingType") or "").lower()!="automatic":
        raise RuntimeError("BUFFER_INSTAGRAM_REQUIRES_MANUAL_PUBLICATION")
    if str(row.get("status") or "").lower()!="sent":
        return None
    link=str(row.get("externalLink") or "")
    uri=urllib.parse.urlparse(link)
    if uri.scheme!="https" or uri.hostname not in ("instagram.com","www.instagram.com"):
        raise RuntimeError("BUFFER_INSTAGRAM_SENT_WITHOUT_PUBLIC_LINK")
    if not __import__("re").fullmatch(r"/(reel|p)/[A-Za-z0-9_-]+/?",uri.path):
        raise RuntimeError("BUFFER_INSTAGRAM_EXTERNAL_PIN_LINK_INVALID")
    return link


def reconcile():
    jobs=queue("pending").get("jobs") or []
    total=0
    for item in jobs:
        remote_id=str(item.get("remote_id") or "")
        if not remote_id:
            continue
        link=verify_sent_post(remote_id)
        if link:
            queue("reconcile",{"id":item["id"],"remote_id":remote_id,"external_link":link})
            total+=1
    return total


def safe_payload(row):
    if row.get("target_key")!=TARGET or row.get("duration_class")!="short":
        raise RuntimeError("NEON_INSTAGRAM_TARGET_INVALID")
    payload=row.get("payload") or {}
    if payload.get("platform")!="instagram" or payload.get("account_id")!="universoanthares":
        raise RuntimeError("NEON_INSTAGRAM_ACCOUNT_INVALID")
    result={
        "platform":"instagram",
        "account_id":"universoanthares",
        "media_url":payload.get("media_url") or payload.get("video_url"),
        "duration_seconds":payload.get("duration_seconds"),
        "title":payload.get("title") or payload.get("video_title"),
        "description":payload.get("description") or "",
    }
    if result["duration_seconds"] is None:
        raise RuntimeError("NEON_INSTAGRAM_DURATION_MISSING")
    return result


def publish_once():
    lease=queue("lease",{"target_key":TARGET,"owner":OWNER})
    row=lease.get("job")
    if not row:
        return "IDLE_BUFFER_CAPACITY" if lease.get("buffer_pending_limit") else "IDLE_NO_CUTS"
    fence={"id":row["id"],"owner":OWNER,"lease_generation":row["lease_generation"]}
    try:
        payload=safe_payload(row)
        # Editorial and destination validation before any irreversible queue write.
        from social_adapters.buffer_three_channels import prepare
        prepare(payload)
    except Exception:
        queue("fail",fence)
        raise
    queue("start",fence)
    try:
        result=schedule(payload)
        if result.get("status")!="SCHEDULED_IN_BUFFER" or not result.get("remote_id"):
            raise RuntimeError("BUFFER_NOT_SCHEDULED")
        queue("scheduled",{**fence,"buffer_post_id":result["remote_id"]})
        return "SCHEDULED_IN_BUFFER"
    except Exception:
        # The Buffer request may already have created a post. Never retry it
        # automatically: started job becomes uncertain, pending reconciliation.
        try: queue("fail",fence)
        except Exception: pass
        raise


def main():
    cloud_only()
    # Reconciliation frees queue slots; Buffer automatic mode uses native schedule.
    confirmed=reconcile()
    status=publish_once()
    print(json.dumps({"instagram_cloud":"PASS","scheduled_action":status,
                      "posts_confirmed_this_run":confirmed},separators=(",",":")))
    return 0


if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        # Only normalized queue error identifiers; no tokens, keys or JWTs.
        from tools.cortes_queue_ha import BackendUnavailable
        reason=(str(e) if isinstance(e,BackendUnavailable) and
                str(e).startswith("CORTES_QUEUE_") else type(e).__name__)
        print(json.dumps({"instagram_cloud":"BLOCKED","reason":reason}))
        sys.exit(2)
