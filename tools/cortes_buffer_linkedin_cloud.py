#!/usr/bin/env python3
"""GitHub-hosted CORTES LinkedIn publisher.

Fetch at most one eligible Neon master, queue at most one Buffer video and
reconcile up to two previously scheduled posts. Never run from owner's PC.
Every queue operation is signed with a new GitHub OIDC token, scoped to this
exact main-branch workflow. A Buffer schedule is not a LinkedIn confirmation.
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
LINKEDIN_ID=PINNED_CHANNELS["linkedin"][0]
TARGET="linkedin:primary"
OWNER="buffer-linkedin:github-cloud-v1"


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
            os.getenv("RUNNER_ENVIRONMENT")!="github-hosted" or
            os.getenv("RUNNER_OS")!="Linux"):
        raise RuntimeError("CORTES_LINKEDIN_CLOUD_ONLY")
    if not os.getenv("BUFFER_API_KEY"):
        raise RuntimeError("BUFFER_CREDENTIAL_UNAVAILABLE")
    if not os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") or not os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        raise RuntimeError("GITHUB_OIDC_UNAVAILABLE")
    os.environ["BUFFER_LINKEDIN_CHANNEL_ID"]=LINKEDIN_ID


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
    result=post("buffer-"+action,payload or {},oidc)
    if not result.get("ok"):
        raise RuntimeError("NEON_BUFFER_ACTION_REJECTED_"+action)
    return result


def verify_sent_post(remote_id):
    query=('query { post(input: { id: '+json.dumps(str(remote_id))+
           ' }) { id status externalLink channelId schedulingType } }')
    row=api(query).get("post") or {}
    if str(row.get("id") or "")!=str(remote_id) or str(row.get("channelId") or "")!=LINKEDIN_ID:
        raise RuntimeError("BUFFER_LINKEDIN_POST_IDENTITY_UNVERIFIED")
    if str(row.get("schedulingType") or "").lower()!="automatic":
        raise RuntimeError("BUFFER_LINKEDIN_REQUIRES_MANUAL_PUBLICATION")
    if str(row.get("status") or "").lower()!="sent":
        return None
    link=str(row.get("externalLink") or "")
    uri=urllib.parse.urlparse(link)
    if uri.scheme!="https" or uri.hostname not in ("linkedin.com","www.linkedin.com"):
        raise RuntimeError("BUFFER_LINKEDIN_SENT_WITHOUT_PUBLIC_LINK")
    if not (uri.path.startswith("/feed/update/") or uri.path.startswith("/posts/") or
            uri.path.startswith("/company/")):
        raise RuntimeError("BUFFER_LINKEDIN_EXTERNAL_POST_LINK_INVALID")
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
        raise RuntimeError("NEON_LINKEDIN_TARGET_INVALID")
    payload=row.get("payload") or {}
    if payload.get("platform")!="linkedin" or payload.get("account_id")!="primary":
        raise RuntimeError("NEON_LINKEDIN_ACCOUNT_INVALID")
    result={
        "platform":"linkedin",
        "media_url":payload.get("media_url") or payload.get("video_url"),
        "duration_seconds":payload.get("duration_seconds"),
        "title":payload.get("title") or payload.get("video_title"),
        "description":payload.get("description") or "",
        "same_day": True,
    }
    if result["duration_seconds"] is None:
        raise RuntimeError("NEON_LINKEDIN_DURATION_MISSING")
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
    # Reconciliation before scheduling also frees up a Buffer queue slot.
    confirmed=reconcile()
    status=publish_once()
    print(json.dumps({"linkedin_cloud":"PASS","scheduled_action":status,
                      "posts_confirmed_this_run":confirmed},separators=(",",":")))
    return 0


if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        print(json.dumps({"linkedin_cloud":"BLOCKED","reason":type(e).__name__}))
        sys.exit(2)
