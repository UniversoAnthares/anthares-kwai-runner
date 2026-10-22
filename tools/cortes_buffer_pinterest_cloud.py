#!/usr/bin/env python3
"""GitHub-hosted CORTES Pinterest publisher.

Fetch at most one eligible Neon master, queue at most one Buffer video and
reconcile up to two previously scheduled posts. Never run from owner's PC.
Every queue operation is signed with a new GitHub OIDC token, scoped to this
exact main-branch workflow. A Buffer schedule is not a Pinterest confirmation.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from social_adapters.buffer_three_channels import api, schedule, BufferBlocked, PINNED_CHANNELS

BASE="https://anthares-remote-primary.vercel.app/api/cortes-queue"
PINTEREST_ID=PINNED_CHANNELS["pinterest"][0]
TARGET="pinterest:lucasyahn"
OWNER="buffer-pinterest:github-cloud-v1"


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
            os.getenv("RUNNER_ENVIRONMENT")!="github-hosted" or
            os.getenv("RUNNER_OS")!="Linux"):
        raise RuntimeError("CORTES_PINTEREST_CLOUD_ONLY")
    if not os.getenv("BUFFER_API_KEY"):
        raise RuntimeError("BUFFER_CREDENTIAL_UNAVAILABLE")
    if not os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") or not os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        raise RuntimeError("GITHUB_OIDC_UNAVAILABLE")
    os.environ["BUFFER_PINTEREST_CHANNEL_ID"]=PINTEREST_ID


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
    if str(row.get("id") or "")!=str(remote_id) or str(row.get("channelId") or "")!=PINTEREST_ID:
        raise RuntimeError("BUFFER_PINTEREST_POST_IDENTITY_UNVERIFIED")
    if str(row.get("schedulingType") or "").lower()!="automatic":
        raise RuntimeError("BUFFER_PINTEREST_REQUIRES_MANUAL_PUBLICATION")
    if str(row.get("status") or "").lower()!="sent":
        return None
    link=str(row.get("externalLink") or "")
    uri=urllib.parse.urlparse(link)
    if uri.scheme!="https" or uri.hostname not in ("pinterest.com","www.pinterest.com"):
        raise RuntimeError("BUFFER_PINTEREST_SENT_WITHOUT_PUBLIC_LINK")
    if not __import__("re").fullmatch(r"/pin/[0-9]+/?",uri.path):
        raise RuntimeError("BUFFER_PINTEREST_EXTERNAL_PIN_LINK_INVALID")
    return link


def reconcile():
    """Read back scheduled Pinterest IDs without letting one bad item stop others.

    Unidentified uncertain creates are NEVER retried or marked confirmed.
    Reconciliation writes retain the backend's fencing and idempotence.
    """
    jobs=queue("pending").get("jobs") or []
    total=0
    unknown=0
    for item in jobs:
        remote_id=str(item.get("remote_id") or "")
        if not remote_id:
            unknown+=1
            continue
        try:
            link=verify_sent_post(remote_id)
        except (BufferBlocked, RuntimeError) as exc:
            if isinstance(exc,BufferBlocked) and str(exc)=="BUFFER_HTTP_429":
                raise
            # Transient Buffer readback or invalid remote identity: quarantine
            # this one post. Keep reconciling independent verified IDs.
            print("::warning::CORTES_PINTEREST_READBACK_UNVERIFIED",flush=True)
            continue
        if link:
            # Backend checks HTTPS Pinterest permalink, exact remote id and
            # prior buffer_scheduled evidence atomically before marking sent.
            queue("reconcile",{"id":item["id"],"remote_id":remote_id,"external_link":link})
            print("CORTES_PINTEREST_CONFIRMED_URL="+link,flush=True)
            total+=1
    if unknown:
        print("::warning::CORTES_PINTEREST_UNCERTAIN_WITHOUT_REMOTE_ID="+str(unknown),flush=True)
    return total


def safe_payload(row):
    if row.get("target_key")!=TARGET or row.get("duration_class")!="short":
        raise RuntimeError("NEON_PINTEREST_TARGET_INVALID")
    payload=row.get("payload") or {}
    if isinstance(payload,str):
        try: payload=json.loads(payload)
        except (ValueError,TypeError):
            raise RuntimeError("CORTES_BUFFER_NEON_PAYLOAD_INVALID_JSON") from None
    if not isinstance(payload,dict):
        raise RuntimeError("CORTES_BUFFER_NEON_PAYLOAD_NOT_OBJECT")
    if payload.get("platform")!="pinterest" or payload.get("account_id")!="lucasyahn":
        raise RuntimeError("NEON_PINTEREST_ACCOUNT_INVALID")
    result={
        "platform":"pinterest",
        "account_id":"lucasyahn",
        "media_url":payload.get("media_url") or payload.get("video_url"),
        "duration_seconds":payload.get("duration_seconds"),
        "title":payload.get("title") or payload.get("video_title"),
        "description":payload.get("description") or "",
        # Preserve editorial provenance: the adapter's strategic gate must
        # see it before ANY Buffer createPost side effect.
        "segment_id":payload.get("segment_id"),
        "editorial_policy":payload.get("editorial_policy"),
        "keywords":payload.get("keywords"),
        "hashtags":payload.get("hashtags"),
    }
    if result["duration_seconds"] is None:
        raise RuntimeError("NEON_PINTEREST_DURATION_MISSING")
    return result


def is_media_missing(url):
    from urllib.parse import urlparse
    parsed=urlparse(str(url or ""))
    if parsed.scheme!="https" or parsed.hostname not in ("anthares.us","www.anthares.us") or not parsed.path.endswith(".mp4"):
        return False
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"CortesPinterestMediaPreflight/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=15):
            return False
    except urllib.error.HTTPError as exc:
        return exc.code==404


def notify_media_p0(job_id,media_url):
    fingerprint=hashlib.sha256(job_id.encode()).hexdigest()[:24]
    title="[QA P0][pinterest] Mídia inexistente no WordPress"
    body=("QA-P0-FINGERPRINT:"+fingerprint+"\\n\\n"
          "P0: corrigir URL de mídia 404 e validar entrega HTTP 200; "
          "registro isolado, sem impedir outros vídeos.\\nJob: "+job_id+
          "\\nMedia URL SHA256: "+hashlib.sha256(media_url.encode()).hexdigest()+
          "\\nRetry previsto somente no dia seguinte, descarte se continuar inválido.\\n")
    env=os.environ.copy()
    if not env.get("GH_TOKEN") and env.get("GITHUB_TOKEN"):
        env["GH_TOKEN"]=env["GITHUB_TOKEN"]
    if not env.get("GH_TOKEN"):
        print("::warning::PINTEREST_QA_CENTRAL_TOKEN_UNAVAILABLE",flush=True)
        return
    repo="UniversoAnthares/anthares-kwai-runner"
    try:
        check=subprocess.run(["gh","issue","list","--repo",repo,"--state","all",
            "--search",fingerprint,"--json","number","--limit","5"],
            capture_output=True,text=True,timeout=15,env=env)
        if check.returncode!=0:
            raise RuntimeError("QA_QUERY_UNAVAILABLE")
        if json.loads(check.stdout):
            return
        created=subprocess.run(["gh","issue","create","--repo",repo,"--title",title,
            "--body",body,"--label","QA-P0","--label","publication-failure"],
            capture_output=True,text=True,timeout=20,env=env)
        if created.returncode!=0:
            raise RuntimeError("QA_ISSUE_CREATE_UNAVAILABLE")
        print("CORTES_PINTEREST_MEDIA_QA_P0_REPORTED",flush=True)
    except (ValueError,OSError,RuntimeError,subprocess.TimeoutExpired):
        print("::warning::PINTEREST_QA_CENTRAL_UNAVAILABLE",flush=True)


def notify_buffer_rejection_p0(job_id,classification,diagnostic):
    """Deduplicated P0 QA ticket with sanitized Buffer API diagnostic."""
    from datetime import datetime, timezone
    env=os.environ.copy()
    env["GH_TOKEN"]=env.get("GH_TOKEN") or env.get("GITHUB_TOKEN","")
    if not env["GH_TOKEN"]:
        print("::warning::PINTEREST_BUFFER_QA_AUTH_UNAVAILABLE",flush=True)
        return
    day=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fingerprint=hashlib.sha256(("pinterest-buffer|"+classification+"|"+day).encode()).hexdigest()[:24]
    repo="UniversoAnthares/anthares-kwai-runner"
    try:
        checked=subprocess.run(["gh","issue","list","--repo",repo,"--state","all",
            "--search",fingerprint,"--json","number","--limit","5"],
            capture_output=True,text=True,timeout=18,env=env)
        if checked.returncode!=0 or json.loads(checked.stdout):
            return
        body=("QA-P0-FINGERPRINT:"+fingerprint+"\\n\\n"+
              "P0: Buffer createPost returned typed MutationError, with no post ID. "
              "No blind retry: the Neon ledger isolates this job for 120 minutes.\\n"+
              "Classification: "+classification+"\\n"+
              "Sanitized diagnostic: "+diagnostic+"\\n"+
              "Job: "+job_id+"\\n"+
              "ACTION: correct cause, test against board/channel/media metadata, "
              "preserve 100-post network cap, avoid duplicate submissions.\\n")
        created=subprocess.run(["gh","issue","create","--repo",repo,
            "--title","[QA P0][Pinterest] Buffer definite "+classification+" rejection",
            "--body",body,"--label","QA-P0","--label","publication-failure"],
            capture_output=True,text=True,timeout=23,env=env)
        if created.returncode!=0:
            print("::warning::PINTEREST_BUFFER_QA_ISSUE_UNAVAILABLE",flush=True)
    except (OSError,ValueError,subprocess.TimeoutExpired):
        print("::warning::PINTEREST_BUFFER_QA_ISSUE_UNAVAILABLE",flush=True)


def notify_editorial_p0(job_id,code):
    """Report a safe classification, never captions, secrets or media URLs."""
    from datetime import datetime, timezone
    env=os.environ.copy()
    env["GH_TOKEN"]=env.get("GH_TOKEN") or env.get("GITHUB_TOKEN","")
    if not env["GH_TOKEN"]:return
    fingerprint=hashlib.sha256(("pinterest-editorial|"+code+"|"+
        datetime.now(timezone.utc).strftime("%Y-%m-%d")).encode()).hexdigest()[:24]
    repo="UniversoAnthares/anthares-kwai-runner"
    try:
        existing=subprocess.run(["gh","issue","list","--repo",repo,
            "--state","all","--search",fingerprint,"--json","number",
            "--limit","5"],capture_output=True,text=True,timeout=14,env=env)
        if existing.returncode!=0 or json.loads(existing.stdout):return
        message=("QA-P0-FINGERPRINT:"+fingerprint+"\\n"+
                 "Preflight editorial failed before createPost, with safe code "+
                 code+". Work item "+job_id+" was atomically returned to "+
                 "transcript metadata QA without a network submission. "+
                 "Repair that metadata; do not retry uncertain jobs.")
        subprocess.run(["gh","issue","create","--repo",repo,
            "--title","[QA P0][Pinterest] Editorial validation blocks clip",
            "--body",message,"--label","QA-P0","--label","publication-failure"],
            capture_output=True,text=True,timeout=20,env=env)
    except (OSError,ValueError,subprocess.TimeoutExpired):
        print("::warning::PINTEREST_EDITORIAL_QA_CENTRAL_UNAVAILABLE",flush=True)


def publish_once():
    # Keep advancing the lane when a particular pre-start cut needs repair.
    # A bounded loop avoids infinite QA retries and respects one successful
    # Buffer createPost per run. Every candidate uses a fresh Neon lease.
    for _ in range(6):
        result=publish_one_candidate()
        if result in ("EDITORIAL_ISOLATED_QA_P0", "MEDIA_ISOLATED_QA_P0"):
            # Quarantined media must not block other eligible clips.
            # Neon isolates this lease before the next candidate is claimed.
            continue
        return result
    return "PINTEREST_QUARANTINE_BATCH_LIMIT"


def publish_one_candidate():
    lease=queue("lease",{"target_key":TARGET,"owner":OWNER})
    row=lease.get("job")
    if not row:
        return "IDLE_BUFFER_CAPACITY" if lease.get("buffer_pending_limit") else "IDLE_NO_CUTS"
    fence={"id":row["id"],"owner":OWNER,"lease_generation":row["lease_generation"]}
    if lease.get("delivery_route") != "buffer":
        # Old Vercel fallback versions do not enforce the weekly allocation.
        # Return the lease before starting; never steal a browser-lane clip.
        queue("fail",fence)
        raise RuntimeError("PINTEREST_BUFFER_LANE_NOT_ACKNOWLEDGED")
    try:
        payload=safe_payload(row)
        # Editorial and destination validation before any irreversible queue write.
        from social_adapters.buffer_three_channels import prepare
        try:
            prepare(payload)
        except ValueError as exc:
            # No createPost call has happened. Move only this exact lease
            # back to transcript QA; do not re-lease the invalid cut.
            import re
            msg=str(exc)
            code=msg if re.fullmatch(r"CORTES_[A-Z0-9_]{5,75}",msg) else "CORTES_EDITORIAL_VALIDATION_FAILED"
            marked=queue("editorial-invalid",{**fence,"reason":code})
            if not marked.get("ok"):
                raise RuntimeError("PINTEREST_EDITORIAL_INVALID_FENCE_FAILED")
            notify_editorial_p0(row["id"],code)
            print("::warning::PINTEREST_EDITORIAL_ISOLATED_QA_P0="+code,flush=True)
            return "EDITORIAL_ISOLATED_QA_P0"
        if is_media_missing(payload["media_url"]):
            marked=queue("media-missing",fence)
            if not marked.get("ok"):
                raise RuntimeError("PINTEREST_MEDIA_ISOLATION_FAILED")
            notify_media_p0(row["id"],payload["media_url"])
            print("::warning::CORTES_PINTEREST_MEDIA_404_ISOLATED",flush=True)
            return "MEDIA_ISOLATED_QA_P0"
    except Exception:
        queue("fail",fence)
        raise
    queue("start",fence)
    from social_adapters.buffer_three_channels import BufferDefiniteRejection
    try:
        result=schedule(payload)
        if result.get("status")!="SCHEDULED_IN_BUFFER" or not result.get("remote_id"):
            raise RuntimeError("BUFFER_NOT_SCHEDULED")
        queue("scheduled",{**fence,"buffer_post_id":result["remote_id"]})
        return "SCHEDULED_IN_BUFFER"
    except BufferDefiniteRejection as exc:
        # Buffer explicitly returned MutationError, not a transport timeout.
        # The backend CAS checks started+owner+generation+no remote ID.
        rejected=queue("rejected",{**fence,"reason":exc.classification})
        if not rejected.get("ok"):
            raise RuntimeError("BUFFER_REJECTION_RECOVERY_FENCE_FAILED")
        print("::warning::PINTEREST_BUFFER_MUTATION_DIAGNOSTIC="+exc.diagnostic,flush=True)
        notify_buffer_rejection_p0(row["id"],exc.classification,exc.diagnostic)
        return "DEFINITIVE_REJECTION_QUARANTINED"
    except Exception:
        # The Buffer request may already have created a post. Never retry it
        # automatically: started job becomes uncertain, pending reconciliation.
        try: queue("fail",fence)
        except Exception: pass
        raise


def alternate_pinterest_boards():
    """Recover Buffer's *authenticated* Pinterest boards through channels query.

    This is a read-only, independent GraphQL resolver proven to return the
    pinned board when the direct 'channel' resolver intermittently returns 500.
    The channel identity and service are checked before any board is trusted.
    """
    result=api("query CortesPinterestAccountOrganizations { account { organizations { id } } }")
    organizations=(result.get("account") or {}).get("organizations") or []
    for org in organizations[:6]:
        oid=str(org.get("id") or "")
        if not oid:
            continue
        q=('query CortesPinterestAlternativeBoards { channels(input: { organizationId: '
           +json.dumps(oid)
           +' }) { id service metadata { ... on PinterestMetadata { boards { serviceId } } } } }')
        rows=api(q).get("channels") or []
        selected=[item for item in rows if str(item.get("id") or "")==PINTEREST_ID
                  and str(item.get("service") or "").lower()=="pinterest"]
        if len(selected)!=1:
            continue
        boards=(selected[0].get("metadata") or {}).get("boards") or []
        if not isinstance(boards,list):
            raise BufferBlocked("BUFFER_PINTEREST_BOARD_RESPONSE_INVALID")
        return boards
    return []


def board_gate():
    """Require the EXACT Buffer-authorized board before leasing a Pin.

    Both resolvers are read only. Retry on transient GraphQL errors, while
    enforcing the same pinned board and preserving fail-closed mutations.
    Never retry a createPost call after an uncertain response.
    """
    from social_adapters.buffer_three_channels import pinterest_boards, PINTEREST_PUBLIC_BOARD_ID
    had_read=False
    for attempt in range(3):
        for source,reader in (("DIRECT",pinterest_boards),
                              ("CHANNELS",alternate_pinterest_boards)):
            try:
                rows=reader()
                had_read=True
                if any(str(x.get("serviceId") or "")==PINTEREST_PUBLIC_BOARD_ID
                       for x in rows):
                    print("CORTES_PINTEREST_BOARD_AUTHORIZED_VIA="+source,flush=True)
                    return PINTEREST_PUBLIC_BOARD_ID
            except (BufferBlocked,ValueError,TypeError) as exc:
                if isinstance(exc,BufferBlocked) and str(exc)=="BUFFER_HTTP_429":
                    raise
                # Only controlled BufferBlocked codes are safe in public CI
                # logs. Never print arbitrary API response bodies/tokens.
                reason=str(exc) if isinstance(exc,BufferBlocked) else type(exc).__name__
                safe=reason if reason.startswith(("BUFFER_HTTP_","BUFFER_GRAPHQL_","BUFFER_RESPONSE_",
                    "BUFFER_PINTEREST_")) else "BOARD_READ_EXCEPTION"
                print("::warning::CORTES_PINTEREST_BOARD_READ_TRANSIENT_"+source+"_"+safe,flush=True)
        if attempt<2:
            time.sleep((1,3)[attempt])
    if had_read:
        print("::error::CORTES_PINTEREST_AWAITING_BUFFER_BOARD_SYNC",flush=True)
        raise BufferBlocked("PINTEREST_BUFFER_BOARD_NOT_SYNCED")
    print("::error::CORTES_PINTEREST_BUFFER_BOARD_READ_FAILED",flush=True)
    raise BufferBlocked("PINTEREST_BUFFER_BOARD_READ_FAILED")


def notify_rate_limit_p0():
    # Safe, fingerprinted incident once per UTC day.
    from datetime import datetime, timezone
    marker="buffer-pinterest-http429-"+datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fingerprint=hashlib.sha256(marker.encode()).hexdigest()[:24]
    env=os.environ.copy()
    env["GH_TOKEN"]=env.get("GH_TOKEN") or env.get("GITHUB_TOKEN","")
    if not env["GH_TOKEN"]:
        return
    repo="UniversoAnthares/anthares-kwai-runner"
    try:
        checked=subprocess.run(["gh","issue","list","--repo",repo,"--state","all",
            "--search",fingerprint,"--json","number","--limit","6"],capture_output=True,
            text=True,timeout=15,env=env)
        if checked.returncode==0 and not json.loads(checked.stdout):
            body=("QA-P0-FINGERPRINT:"+fingerprint+"\\n\\n"
                  "Buffer API retorna HTTP 429 para consultas autenticadas. "
                  "Cooldown compartilhado Neon de 30 minutos instalado. "
                  "Não criar posts ou reenviar incertos durante o bloqueio; "
                  "investigar volume agregado de calls e renovação da cota.\\n")
            subprocess.run(["gh","issue","create","--repo",repo,"--title",
                "[QA P0][pinterest] Buffer HTTP 429, publicador nuvem em cooldown",
                "--body",body,"--label","QA-P0","--label","publication-failure"],
                capture_output=True,text=True,timeout=20,env=env)
    except (ValueError,OSError,subprocess.TimeoutExpired):
        print("::warning::PINTEREST_RATE_LIMIT_QA_ISSUE_UNAVAILABLE",flush=True)


def main():
    cloud_only()
    policy=queue("policy")
    if not policy.get("enabled") or int(policy.get("remaining",0))<=0:
        print(json.dumps({"pinterest_cloud":"BUFFER_BUDGET_HANDOFF_OWN",
                          "buffer_used_today":policy.get("used"),
                          "buffer_daily_limit":20,
                          "buffer_weekday_enabled":bool(policy.get("enabled"))}),flush=True)
        return 0
    state=queue("cooldown-status")
    if state.get("active"):
        print(json.dumps({"pinterest_cloud":"COOLDOWN_HTTP_429",
                          "until":state.get("cooldown_until"),
                          "published":0},separators=(",",":")),flush=True)
        return 0
    try:
        # Readback comes first; never lose remote evidence on board outages.
        confirmed=reconcile()
        board_gate()
        status=publish_once()
        print(json.dumps({"pinterest_cloud":"PASS","scheduled_action":status,
                          "posts_confirmed_this_run":confirmed},separators=(",",":")))
        return 0
    except BufferBlocked as exc:
        if str(exc)=="BUFFER_HTTP_429":
            recorded=queue("cooldown",{"seconds":1800})
            if not recorded.get("ok"):
                raise RuntimeError("PINTEREST_BUFFER_COOLDOWN_NOT_PERSISTED")
            notify_rate_limit_p0()
            print(json.dumps({"pinterest_cloud":"COOLDOWN_HTTP_429",
                 "until":recorded.get("cooldown_until"),
                 "published":0},separators=(",",":")),flush=True)
            return 0
        raise


if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        from tools.cortes_queue_ha import BackendUnavailable
        safe=str(e)
        code=(safe if (isinstance(e,BufferBlocked) and safe.startswith(("BUFFER_","PINTEREST_","MASTER_","TITLE_","DURATION_","CAPTION_")))
              or (isinstance(e,BackendUnavailable) and safe.startswith("CORTES_QUEUE_"))
              else type(e).__name__)
        # A type alone hides otherwise straightforward operator fixes.
        # Do not log exception messages/arguments: they may contain API
        # responses, titles, tokens or media URLs. Return only basename/line.
        import traceback
        site="UNKNOWN"
        entries=traceback.extract_tb(e.__traceback__)
        local=[x for x in entries if str(x.filename).startswith(str(ROOT))]
        if local:
            end=local[-1]
            site=Path(end.filename).name+":"+str(end.lineno)
        if isinstance(e,ValueError) and safe.startswith("CORTES_QUEUE_"):
            code=safe
        print(json.dumps({"pinterest_cloud":"BLOCKED","reason":code,
                          "failure_site":site},separators=(",",":")))
        sys.exit(2)
