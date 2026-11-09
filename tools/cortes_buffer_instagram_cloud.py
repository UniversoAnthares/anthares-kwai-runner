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
import datetime
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from social_adapters.buffer_three_channels import api, schedule, BufferBlocked, BufferDefiniteRejection, buffer_cooldown_seconds, PINNED_CHANNELS, trusted_instagram_one_time_runner

BASE="https://anthares-remote-primary.vercel.app/api/cortes-queue"
INSTAGRAM_ID=PINNED_CHANNELS["instagram"][0]
TARGET="instagram:universoanthares"
OWNER="buffer-instagram:github-cloud-v1"


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
            os.getenv("RUNNER_ENVIRONMENT")!="github-hosted" or
            os.getenv("RUNNER_OS")!="Linux") and not trusted_instagram_one_time_runner():
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
    result=post("buffer-"+action,payload or {},oidc)
    if not result.get("ok"):
        raise RuntimeError("NEON_BUFFER_ACTION_REJECTED_"+action)
    return result


def classify_buffer_publish_error(message):
    """Classify Buffer's user-facing publishing error without logging its text."""
    value=" ".join(str(message or "").lower().split())[:1200]
    if not value:
        return "DETAIL_NOT_PROVIDED"
    if any(p in value for p in (
        "authorization", "authorisation", "reauthoriz", "re-authoriz",
        "authentication", "access token", "expired token", "reconnect",
        "disconnected", "permission", "account connection",
    )):
        return "ACCOUNT_AUTH_OR_PERMISSION"
    if any(p in value for p in (
        "media url", "media unavailable", "can't fetch", "cannot fetch",
        "download", "not accessible", "not found", "404", "403",
        "url could not", "invalid url", "file could not", "timeout",
    )):
        return "MEDIA_SOURCE_UNAVAILABLE"
    if any(p in value for p in (
        "aspect ratio", "resolution", "video format", "file format",
        "codec", "unsupported media", "unsupported video", "file size",
        "too large", "duration", "invalid video", "invalid media",
    )):
        return "MEDIA_FORMAT_INVALID"
    if any(p in value for p in (
        "rate limit", "too many requests", "quota", "limit reached",
        "daily limit", "temporarily unavailable", "try again later",
    )):
        return "RATE_OR_TRANSIENT"
    if any(p in value for p in (
        "copyright", "policy", "restricted", "blocked", "violat",
        "community guidelines",
    )):
        return "CONTENT_OR_ACCOUNT_RESTRICTION"
    return "OTHER_PROVIDER_ERROR"


def inspect_buffer_post(remote_id, *, include_error=False):
    """Read only an existing Buffer record; never create a new post."""
    query=('query { post(input: { id: '+json.dumps(str(remote_id))+
           ' }) { id status externalLink channelId schedulingType error { message } } }')
    row=api(query).get("post")
    if row is None:
        return ("missing",None,None) if include_error else ("missing",None)
    if not isinstance(row,dict) or str(row.get("id") or "")!=str(remote_id) or str(row.get("channelId") or "")!=INSTAGRAM_ID:
        raise RuntimeError("BUFFER_INSTAGRAM_POST_IDENTITY_UNVERIFIED")
    if str(row.get("schedulingType") or "").lower()!="automatic":
        raise RuntimeError("BUFFER_INSTAGRAM_REQUIRES_MANUAL_PUBLICATION")
    state=str(row.get("status") or "").lower()
    if state!="sent":
        # A fixed allowlist prevents untrusted provider text in public CI logs.
        if state not in ("scheduled","pending","queued","failed","error","rejected","cancelled","canceled","draft"):
            state="other"
        reason=classify_buffer_publish_error((row.get("error") or {}).get("message")) if state=="error" else None
        return (state,None,reason) if include_error else (state,None)
    link=str(row.get("externalLink") or "")
    uri=urllib.parse.urlparse(link)
    if uri.scheme!="https" or uri.hostname not in ("instagram.com","www.instagram.com"):
        raise RuntimeError("BUFFER_INSTAGRAM_SENT_WITHOUT_PUBLIC_LINK")
    if not __import__("re").fullmatch(r"/(reel|p)/[A-Za-z0-9_-]+/?",uri.path):
        raise RuntimeError("BUFFER_INSTAGRAM_EXTERNAL_PIN_LINK_INVALID")
    return ("sent",link,None) if include_error else ("sent",link)


def verify_sent_post(remote_id):
    """Compatibility: preserve the original confirmation-only contract."""
    state,link=inspect_buffer_post(remote_id)
    if state=="missing":
        raise RuntimeError("BUFFER_INSTAGRAM_POST_IDENTITY_UNVERIFIED")
    return link


def reconcile():
    jobs=queue("pending").get("jobs") or []
    total=0
    for item in jobs:
        remote_id=str(item.get("remote_id") or "")
        if not remote_id:
            continue
        # Only a short, non-secret ledger suffix identifies the diagnostic row.
        record_ref=str(item["id"])[-12:]
        try:
            state,link,error_category=inspect_buffer_post(remote_id,include_error=True)
        except RuntimeError as exc:
            if str(exc) in ("BUFFER_INSTAGRAM_POST_IDENTITY_UNVERIFIED",
                            "BUFFER_INSTAGRAM_REQUIRES_MANUAL_PUBLICATION",
                            "BUFFER_INSTAGRAM_SENT_WITHOUT_PUBLIC_LINK",
                            "BUFFER_INSTAGRAM_EXTERNAL_PIN_LINK_INVALID"):
                print(json.dumps({"instagram_buffer_readback":"REMOTE_POST_STATE",
                                  "record_ref":record_ref,"state":"blocked",
                                  "reason":str(exc)}),flush=True)
            raise
        if link:
            queue("reconcile",{"id":item["id"],"remote_id":remote_id,"external_link":link})
            total+=1
        print(json.dumps({"instagram_buffer_readback":"REMOTE_POST_STATE",
                          "record_ref":record_ref,"state":state,
                          "error_category":error_category,
                          "neon_confirmed":bool(link),"new_posts":0}),flush=True)
    return total


def safe_payload(row):
    if row.get("target_key")!=TARGET or row.get("duration_class")!="short":
        raise RuntimeError("NEON_INSTAGRAM_TARGET_INVALID")
    payload=row.get("payload") or {}
    if isinstance(payload,str):
        try: payload=json.loads(payload)
        except (ValueError,TypeError):
            raise RuntimeError("CORTES_BUFFER_NEON_PAYLOAD_INVALID_JSON") from None
    if not isinstance(payload,dict):
        raise RuntimeError("CORTES_BUFFER_NEON_PAYLOAD_NOT_OBJECT")
    if payload.get("platform")!="instagram" or payload.get("account_id")!="universoanthares":
        raise RuntimeError("NEON_INSTAGRAM_ACCOUNT_INVALID")
    result={
        "platform":"instagram",
        "account_id":"universoanthares",
        "media_url":payload.get("media_url") or payload.get("video_url"),
        "duration_seconds":payload.get("duration_seconds"),
        "title":payload.get("title") or payload.get("video_title"),
        "description":payload.get("description") or "",
        "same_day": (trusted_instagram_one_time_runner() or
                     (os.getenv("CORTES_IG_IMMEDIATE_UNTIL_UTC")=="2026-10-22T09:00:00Z"
                      and datetime.datetime.now(datetime.timezone.utc)
                          < datetime.datetime(2026,10,22,9,0,tzinfo=datetime.timezone.utc))),
    }
    if result["duration_seconds"] is None:
        raise RuntimeError("NEON_INSTAGRAM_DURATION_MISSING")
    return result


def source_media_is_404(url: str) -> bool:
    """Check before Buffer mutation; confirm HEAD 404 using a ranged GET."""
    if not isinstance(url,str) or not url.startswith(("https://anthares.us/","https://www.anthares.us/")):
        raise RuntimeError("SOURCE_URL_NOT_TRUSTED")
    for method in ("HEAD","GET"):
        headers={"User-Agent":"AntharesCORTES-MediaPreflight/2"}
        if method=="GET": headers["Range"]="bytes=0-31"
        request=urllib.request.Request(url,method=method,headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=14) as response:
                if response.status in (200,206): return False
                raise RuntimeError("MEDIA_HTTP_UNEXPECTED_"+str(response.status))
        except urllib.error.HTTPError as exc:
            if exc.code==404:
                if method=="GET": return True
                continue
            if method=="HEAD" and exc.code in (403,405): continue
            raise
    return False


def alert_qa_404(item: dict, url: str) -> None:
    print(json.dumps({"priority":"P0","network":"instagram","error":"SOURCE_MEDIA_HTTP_404",
                      "clip":item["id"],"next_round":"discard_if_unrepaired"}),flush=True)
    token=os.getenv("GITHUB_TOKEN","")
    if not token: return
    note=("[CORTES QA P0] Instagram: mídia 404 isolada sem bloquear a fila; "
          f"clip `{item['id']}`; URL {url}. Investigar e corrigir nesta rodada; "
          "descartar somente na próxima rodada diária se continuar indisponível.")
    request=urllib.request.Request(
        "https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments",
        data=json.dumps({"body":note}).encode(),method="POST",
        headers={"Accept":"application/vnd.github+json","Authorization":"Bearer "+token,
                 "Content-Type":"application/json","User-Agent":"AntharesCORTES-QA"})
    try:
        with urllib.request.urlopen(request,timeout=18) as response:
            print("QA_ALERT_HTTP_"+str(response.status),flush=True)
    except Exception as exc:
        print("QA_ALERT_FAILED_"+type(exc).__name__,flush=True)


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
        if source_media_is_404(payload["media_url"]):
            queue("media-missing",fence)
            alert_qa_404(row,payload["media_url"])
            return "QUARANTINED_HTTP_404"
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
    except BufferDefiniteRejection as exc:
        # A typed Buffer MutationError explicitly refused createPost. Neon
        # must own the exact source job under its original lease/CAS fence.
        # MEDIA fails terminally; other classes back off without a second post.
        rejected=queue("rejected",{**fence,"reason":exc.classification})
        if not rejected.get("ok"):
            raise RuntimeError("INSTAGRAM_BUFFER_REJECTION_FENCE_FAILED")
        print(json.dumps({"instagram_cloud":"DEFINITE_BUFFER_REJECTION",
                          "class":exc.classification,
                          "ledger_status":(rejected.get("job") or {}).get("status"),
                          "new_posts":0}),flush=True)
        return "DEFINITE_REJECTION_"+exc.classification+"_FENCED"
    except Exception:
        # A transport timeout/unknown Buffer result may have created a post.
        # Retain UNCERTAIN and never retry without independent reconciliation.
        try: queue("fail",fence)
        except Exception: pass
        raise


def main():
    cloud_only()
    cooldown=queue("cooldown-status")
    if cooldown.get("active"):
        print(json.dumps({"instagram_cloud":"IDLE_BUFFER_HTTP429_COOLDOWN",
                          "until":cooldown.get("cooldown_until")}),flush=True)
        return 0
    try:
        # Readback of existing Buffer posts is independent of today's NEW-post quota.
        confirmed=reconcile()
        if os.getenv("CORTES_RECONCILE_ONLY")=="1":
            print(json.dumps({"instagram_cloud":"RECONCILE_ONLY",
                              "posts_confirmed_this_run":confirmed,"new_posts":0}),flush=True)
            return 0
        policy=queue("policy")
        if not policy.get("enabled") or int(policy.get("remaining",0))<=0:
            print(json.dumps({"instagram_cloud":"BUFFER_BUDGET_HANDOFF_OWN",
                              "buffer_used_today":policy.get("used"),
                              "buffer_daily_limit":20,
                              "buffer_weekday_enabled":bool(policy.get("enabled")),
                              "posts_confirmed_this_run":confirmed}),flush=True)
            return 0
        # One eligible new post per scheduled run, under the shared Buffer quota.
        status=publish_once()
        print(json.dumps({"instagram":"BUFFER_QUEUE_ITEM_RESULT","attempt":1,
                          "status":status}),flush=True)
        confirmed+=reconcile()
        print(json.dumps({"instagram_cloud":"PASS","scheduled":int(status=="SCHEDULED_IN_BUFFER"),
                          "isolated_404":int(status=="QUARANTINED_HTTP_404"),
                          "confirmed":confirmed}),flush=True)
        return 0
    except BufferBlocked as exc:
        if str(exc)!="BUFFER_HTTP_429":
            raise
        queue("cooldown",{"seconds":buffer_cooldown_seconds(exc,900)})
        print(json.dumps({"instagram_cloud":"IDLE_BUFFER_HTTP429_COOLDOWN",
                          "cooldown_seconds":buffer_cooldown_seconds(exc,900),"queue_mutated":False}),flush=True)
        return 0


if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        if isinstance(e,BufferBlocked) and str(e)=="BUFFER_HTTP_429":
            try:
                queue("cooldown",{"seconds":buffer_cooldown_seconds(e,1800)})
                print("::warning::CORTES_BUFFER_ALL_CHANNELS_BACKOFF=1",flush=True)
            except Exception:
                print("::error::CORTES_BUFFER_SHARED_BACKOFF_PERSISTENCE_FAILED",flush=True)
        # Only normalized queue error identifiers; no tokens, keys or JWTs.
        from tools.cortes_queue_ha import BackendUnavailable
        import re
        normalized = str(e)
        reason=(normalized if isinstance(e,(BackendUnavailable,BufferBlocked)) and
                re.fullmatch(r"[A-Z][A-Z0-9_]{4,95}",normalized)
                else type(e).__name__)
        print(json.dumps({"instagram_cloud":"BLOCKED","reason":reason}))
        sys.exit(2)
