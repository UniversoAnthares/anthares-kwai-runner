#!/usr/bin/env python3
"""Publish ONE fenced CORTES TikTok short from a GitHub-hosted browser.

Canonical encrypted session -> account verification -> Neon lease -> media
preflight -> irreversible-start checkpoint -> publisher -> profile confirmation
-> WordPress callback -> Neon confirmation. Never retry an uncertain upload.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
import cortes_tiktok_queue_consumer as q

EXPECTED=q.ACCOUNT

def publication_window_open(now_utc=None, not_before_utc=None):
    """Fail closed until the explicitly configured first TikTok round."""
    raw=str(not_before_utc or os.getenv("TIKTOK_PUBLISH_NOT_BEFORE_UTC") or "").strip()
    if not raw:
        return False
    try:
        target=datetime.fromisoformat(raw.replace("Z","+00:00"))
        if target.tzinfo is None:
            return False
        now=now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now=now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)>=target.astimezone(timezone.utc)
    except (TypeError,ValueError,OverflowError):
        return False

MAX_SIZE=180*1024*1024
MIN_SIZE=32*1024


def preflight_vault():
    from tiktok_session_authority import load_canonical_state
    from playwright.sync_api import sync_playwright
    state,meta=load_canonical_state()
    valid=[x for x in state.get("cookies") or [] if
           x.get("name") in {"sessionid","sessionid_ss","sid_tt"} and
           (not x.get("expires") or float(x.get("expires"))>time.time())]
    if not valid:
        raise q.SafeStop("TIKTOK_AUTHENTICATION_EXPIRED")
    from playwright.sync_api import TimeoutError as PWTimeout
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1280,"height":900})
            page=ctx.new_page()
            try:
                page.goto("https://www.tiktok.com/profile",wait_until="domcontentloaded",timeout=45000)
                page.wait_for_timeout(1400)
            except PWTimeout as exc:
                raise q.SafeStop("TIKTOK_PROFILE_NAVIGATION_TIMEOUT") from exc
            user=""
            try:
                script=page.locator("#__UNIVERSAL_DATA_FOR_REHYDRATION__").text_content(timeout=6000)
                info=json.loads(script or "{}")
                user=str(info.get("__DEFAULT_SCOPE__",{}).get("webapp.app-context",{}).get("user",{}).get("uniqueId") or "").lower()
            except (ValueError,Exception):
                pass
            match=re.search(r"tiktok\.com/@([^/?#]+)",page.url,re.I)
            redirect=match.group(1).lower() if match else ""
            gate="/login" in page.url.lower() or bool(page.locator("input[type=password]").count())
            if gate or (user!=EXPECTED and redirect!=EXPECTED):
                raise q.SafeStop("TIKTOK_OWNER_IDENTITY_UNVERIFIED")
        finally:
            browser.close()
    print("CORTES_TIKTOK_CANONICAL_OWNER_VERIFIED",flush=True)
    return state


def download_verified(job,path):
    from urllib.parse import urlparse
    url=str(job["media_url"])
    u=urlparse(url)
    if u.scheme!="https" or u.hostname not in ("anthares.us","www.anthares.us") or u.username or u.password:
        raise q.SafeStop("TIKTOK_MEDIA_ORIGIN_DENIED")
    request=urllib.request.Request(url,headers={"Accept":"video/mp4,application/octet-stream"})
    total=0
    start=time.monotonic()
    try:
        with urllib.request.urlopen(request,timeout=38) as stream, open(path,"wb") as output:
            content_type=str(stream.headers.get("Content-Type") or "").lower()
            if content_type and not any(x in content_type for x in ("video","octet-stream","application/mp4")):
                raise q.SafeStop("TIKTOK_MEDIA_CONTENT_TYPE_INVALID")
            while True:
                if time.monotonic()-start>120:
                    raise q.SafeStop("TIKTOK_MEDIA_TRANSFER_TIMEOUT")
                b=stream.read(1024*1024)
                if not b:break
                total+=len(b)
                if total>MAX_SIZE:
                    raise q.SafeStop("TIKTOK_MEDIA_EXCEEDS_LIMIT")
                output.write(b)
    except OSError as exc:
        raise q.SafeStop("TIKTOK_MEDIA_DOWNLOAD_FAILED") from exc
    if total<MIN_SIZE:
        raise q.SafeStop("TIKTOK_MEDIA_TOO_SMALL")
    print("CORTES_TIKTOK_MEDIA_PREFLIGHT_OK bytes="+str(total),flush=True)


def inventory(state):
    import tiktok_worker as tw
    from tiktok_creator_inventory import inventory_studio
    tw.STORAGE_RAW=json.dumps(state,separators=(",",":"))
    result=inventory_studio(EXPECTED,state)
    if not result:
        result=tw.inventory_profile_videos(EXPECTED)
    return {"ok":True,"account":EXPECTED,"items":result}


def trusted_workflow_event(event, ref, event_path):
    """Allow cron, manual main dispatch or successful trusted Core Supervisor."""
    if ref != "refs/heads/main":
        return False
    if event in ("schedule", "workflow_dispatch"):
        return True
    if event != "workflow_run" or not event_path:
        return False
    try:
        with open(event_path, "r", encoding="utf-8") as fh:
            source=json.load(fh).get("workflow_run") or {}
        origin=source.get("head_repository") or {}
        return (
            source.get("name")=="Anthares Core Supervisor"
            and source.get("conclusion")=="success"
            and source.get("head_branch")=="main"
            and origin.get("full_name")=="UniversoAnthares/anthares-kwai-runner"
        )
    except (OSError, ValueError, TypeError):
        return False


def main():
    if os.getenv("CORTES_TIKTOK_HOSTED_DRY_RUN")=="1":
        print("CORTES_TIKTOK_HOSTED_DRY_RUN_NO_PUBLISH",flush=True)
        return 0
    event=os.getenv("GITHUB_EVENT_NAME","")
    if not trusted_workflow_event(event,os.getenv("GITHUB_REF",""),os.getenv("GITHUB_EVENT_PATH","")):
        print("CORTES_TIKTOK_UNTRUSTED_OR_NONPUBLISH_EVENT_SKIP",flush=True)
        return 0
    if not publication_window_open():
        print("CORTES_TIKTOK_DEFERRED_UNTIL_2026_10_20_0600_CUIABA",flush=True)
        return 0

    state=preflight_vault()
    control=q.oidc()
    health=q.qcall("health",control)
    if not health.get("ok") or health.get("service")!="cortes-tiktok-neon":
        raise q.SafeStop("TIKTOK_NEON_QUEUE_UNAVAILABLE")
    before=inventory(state)
    claim=q.qcall("claim",control,{})
    if not claim.get("ok"):
        raise q.SafeStop("TIKTOK_CLAIM_UNCONFIRMED")
    mode=str(claim.get("mode") or "")
    job=claim.get("job")
    if mode in ("idle","busy","paced","cap") or not job:
        print("CORTES_TIKTOK_QUEUE_"+(mode or "IDLE").upper(),flush=True)
        return 0
    sid,generation=q.validate_job(job)
    matching=q.found(before,sid)
    if mode=="reconcile":
        if matching:
            q.finish(job,generation,matching,control)
        else:
            print("CORTES_TIKTOK_UNCERTAIN_REQUIRES_REVIEW segment="+sid,flush=True)
        return 0
    if mode!="publish" or job.get("status")!="leased":
        raise q.SafeStop("TIKTOK_INVALID_QUEUE_STATE")

    with tempfile.TemporaryDirectory(prefix="anthares-tiktok-hosted-") as tmp:
        folder=Path(tmp)
        if not matching:
            # Download before the irreversible checkpoint. A transient 5xx
            # here can safely leave the lease to expire back to queued.
            download_verified(job,folder/"short.mp4")
        changed=q.qcall("start",control,{"id":job["id"],"lease_generation":generation})
        if not changed.get("ok") or (changed.get("job") or {}).get("status")!="started":
            raise q.SafeStop("TIKTOK_IRREVERSIBLE_FENCE_UNCONFIRMED")
        try:
            if matching:
                remote=matching
            else:
                # Avoid downloading a second time after the started checkpoint.
                remote=publish_one_preloaded(job,sid,folder,state)
                verified=q.found(inventory(state),sid)
                if verified!=remote:
                    raise q.SafeStop("TIKTOK_PROFILE_MARKER_CONFIRMATION_MISMATCH")
            q.finish(job,generation,remote,control)
            return 0
        except Exception:
            try:
                q.qcall("fail",control,{"id":job["id"],"lease_generation":generation,
                                         "error":"after_started_requires_reconciliation"})
            except Exception:
                pass
            raise


def publish_one_preloaded(job,sid,folder,state):
    # Isolate publisher run from download and queue state mutations.
    # Publication code expects only the local media and a strict plan file.
    media=folder/"short.mp4"
    if not media.is_file() or media.stat().st_size<MIN_SIZE:
        raise q.SafeStop("TIKTOK_MEDIA_MISSING_AT_START")
    plan={
        "source_id":str(job["source_id"]),
        "segment_id":sid,
        "source_title":str(job.get("title") or ""),
        "title":q.caption(job),
        "expected_tiktok_username":EXPECTED,
        "media_path":str(media),
    }
    plan_file=folder/"plan.json"
    plan_file.write_text(json.dumps(plan,ensure_ascii=False),encoding="utf-8")
    env=os.environ.copy()
    env.pop("TIKTOK_STORAGE_STATE",None)
    env.update({
        "EXPECTED_TIKTOK_USERNAME":EXPECTED,
        "TIKTOK_STORAGE_STATE_FILE":str(folder/"canonical-state.json"),
        "TIKTOK_YOUTUBE_PLAN":str(plan_file),
        "ATD_ARTIFACT_DIR":str(folder/"artifacts"),
        "TIKTOK_AUTOMATION_HALT":str(folder/"halt.json"),
        "TIKTOK_PUBLISH_EVIDENCE":str(folder/"publish-evidence.json"),
        "TIKTOK_PUBLISHED_KEYS":str(folder/"published.json"),
    })
    (folder/"canonical-state.json").write_text(json.dumps(state,separators=(",",":")),encoding="utf-8")
    (folder/"canonical-state.json").chmod(0o600)
    try:
        proc=subprocess.run([sys.executable,"-u",str(ROOT/"direct-tiktok-publisher"/"tiktok_cloud_publish.py")],
                            cwd=str(ROOT),env=env,text=True,capture_output=True,timeout=390)
    except subprocess.TimeoutExpired as exc:
        raise q.SafeStop("TIKTOK_BROWSER_PUBLISH_TIMEOUT_RECONCILE_ONLY") from exc
    if proc.returncode:
        # The publisher may have clicked Post. Inspect only fixed, safe markers
        # and error categories; never print original browser text or stderr.
        stage = "before_upload_form"
        if (folder/"artifacts"/"tiktok-owned-upload-page.png").is_file():
            stage = "upload_form_open"
        if "TIKTOK_CAPTION=" in proc.stdout:
            stage = "caption_filled"
        if (folder/"artifacts"/"tiktok-owned-upload-ready.png").is_file():
            stage = "upload_ready"
        if "TIKTOK_PROFILE_VERIFY attempt=" in proc.stdout:
            stage = "after_post_profile_reconciliation"
        if (folder/"artifacts"/"tiktok-owned-after-post.png").is_file():
            stage = "after_publish_click"
        body = (proc.stderr+"\\n"+proc.stdout).lower()
        rules = (
            ("captcha", "platform_challenge"),
            ("security check", "platform_challenge"),
            ("login", "identity_expired_or_login"),
            ("página de upload", "upload_page_unavailable"),
            ("input[type", "upload_field_missing"),
            ("campo de legenda", "caption_field_missing"),
            ("botão publicar", "post_button_unavailable"),
            ("confirmação inequívoca", "confirmation_missing"),
            ("múltiplos vídeos novos", "profile_multiple_posts"),
            ("nenhum vídeo novo", "profile_not_updated"),
            ("module", "publisher_import_failure"),
            ("timeout", "browser_timeout"),
        )
        category=next((v for k,v in rules if k in body),"unclassified")
        print("CORTES_TIKTOK_PUBLISH_FAILURE_STAGE="+stage+" CATEGORY="+category,flush=True)
        raise q.SafeStop("TIKTOK_BROWSER_PUBLISH_UNVERIFIED")
    try:
        evidence=json.loads((folder/"publish-evidence.json").read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        raise q.SafeStop("TIKTOK_PUBLISH_EVIDENCE_MISSING") from exc
    remote=str(evidence.get("remote_id") or "")
    if not (evidence.get("confirmed") is True and q.ID_RE.fullmatch(remote) and
            str(evidence.get("segment_id") or "")==sid and str(evidence.get("account") or "").lstrip("@").casefold()==EXPECTED):
        raise q.SafeStop("TIKTOK_PUBLISH_EVIDENCE_INVALID")
    return remote


if __name__=="__main__":
    try:sys.exit(main())
    except q.SafeStop as ex:
        print("CORTES_TIKTOK_HOSTED_HOLD="+str(ex),file=sys.stderr,flush=True)
        sys.exit(2)
    except Exception as ex:
        print("CORTES_TIKTOK_HOSTED_ERROR="+type(ex).__name__,file=sys.stderr,flush=True)
        sys.exit(3)
