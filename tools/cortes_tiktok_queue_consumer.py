#!/usr/bin/env python3
"""Consume the isolated Neon TikTok queue; publish once and reconcile by profile.

The producer in anthares-clipper owns WordPress credentials. This consumer only
receives a per-clip callback capability from the fenced Neon queue. No videos
are submitted before an authoritative started checkpoint is persisted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse

QUEUE = "https://anthares-remote-primary.vercel.app/api/cortes-tiktok"
WORKER = "https://anthares-tiktok-worker.anthares1.workers.dev"
ACCOUNT = "universo.anthares"
AUDIENCE = QUEUE
CALLBACK = "https://anthares.us/wp-json/anthares/v1/cortes/clip-network-callback"
ID_RE = re.compile(r"^[0-9]{12,25}$")
SEGMENT_RE = re.compile(r"^g[0-9]+:[A-Za-z0-9_-]{6,60}:[0-9]+:[0-9]+$")


class SafeStop(RuntimeError):
    pass


def http(url, headers=None, body=None, timeout=40):
    headers = dict(headers or {})
    headers["Accept"] = "application/json"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, headers=headers, data=data,
                                     method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            out = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SafeStop("HTTP_" + str(exc.code) + "_" + (urlparse(url).hostname or "unknown")) from exc
    except (OSError, ValueError) as exc:
        raise SafeStop("UPSTREAM_RESULT_UNCERTAIN_" + type(exc).__name__) from exc
    if not isinstance(out, dict):
        raise SafeStop("INVALID_JSON_RESPONSE")
    return out


def oidc(audience=AUDIENCE):
    base = os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    assertion = os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not base or not assertion:
        raise SafeStop("GITHUB_OIDC_CONTEXT_REQUIRED")
    endpoint = base + ("&" if "?" in base else "?") + urllib.parse.urlencode({"audience": audience})
    response = http(endpoint, {"Authorization": "Bearer " + assertion}, timeout=20)
    token = str(response.get("value") or "")
    if not token:
        raise SafeStop("GITHUB_OIDC_UNAVAILABLE")
    return {"Authorization": "Bearer " + token}


def worker_auth():
    # Prefer a short-lived identity restricted to the main-branch workflow.
    # This also survives changes to the static ARA_SHARED credential.
    return oidc("anthares-render-worker")


def qcall(action, credentials, payload=None):
    return http(QUEUE + "?action=" + action, credentials, body=payload)


def wcall(route, credentials, payload=None, timeout=120):
    return http(WORKER + route, credentials, body=payload, timeout=timeout)


def marker(segment_id):
    return "#anthares" + hashlib.sha256((ACCOUNT + ":" + segment_id).encode()).hexdigest()[:10]


def caption(job):
    title = " ".join(str(job.get("title") or "").split())
    title = re.sub(r"[\r\n\t]+", " ", title)
    title = title[:74].rstrip(" .,-")
    if len(title) < 8:
        title = "Literatura e escrita"
    return title + " " + marker(str(job.get("segment_id") or ""))


def found(inventory, segment_id):
    if not inventory.get("ok") or str(inventory.get("account") or "").lstrip("@").casefold() != ACCOUNT:
        raise SafeStop("TIKTOK_ACCOUNT_IDENTITY_UNVERIFIED")
    key = marker(segment_id)
    ids = set()
    for row in inventory.get("items") or []:
        if not isinstance(row, dict):
            continue
        remote_id = str(row.get("id") or "")
        if ID_RE.fullmatch(remote_id) and key in str(row.get("text") or "").casefold():
            ids.add(remote_id)
    if len(ids) > 1:
        raise SafeStop("TIKTOK_IDENTITY_MARKER_COLLISION")
    return next(iter(ids), "")


def validate_job(job):
    if not isinstance(job, dict):
        raise SafeStop("QUEUE_JOB_MISSING")
    sid = str(job.get("segment_id") or "")
    vid = str(job.get("source_id") or "")
    if not SEGMENT_RE.fullmatch(sid) or sid.split(":")[1] != vid:
        raise SafeStop("QUEUE_SEGMENT_IDENTITY_INVALID")
    media = urlparse(str(job.get("media_url") or ""))
    if media.scheme != "https" or media.hostname not in ("anthares.us", "www.anthares.us"):
        raise SafeStop("QUEUE_MEDIA_ORIGIN_INVALID")
    if str(job.get("callback_url") or "") != CALLBACK:
        raise SafeStop("QUEUE_CALLBACK_ORIGIN_INVALID")
    if len(str(job.get("callback_token") or "")) < 32:
        raise SafeStop("QUEUE_CALLBACK_CAPABILITY_MISSING")
    if not (30 <= float(job.get("duration_seconds") or 0) <= 90):
        raise SafeStop("QUEUE_SHORT_DURATION_INVALID")
    if not int(job.get("attachment_id") or 0) > 0:
        raise SafeStop("QUEUE_ATTACHMENT_INVALID")
    generation = int(job.get("lease_generation") or 0)
    if generation < 1:
        raise SafeStop("QUEUE_LEASE_FENCE_INVALID")
    return sid, generation


def callback(job, remote_id):
    data = {
        "video_id": job["source_id"], "clip_id": job["segment_id"],
        "attachment_id": int(job["attachment_id"]), "network": "tiktok",
        "account_id": "primary", "status": "completed",
        "remote_id": remote_id, "token": job["callback_token"],
    }
    result = http(CALLBACK, body=data, timeout=35)
    if result.get("ok") is not True:
        raise SafeStop("WORDPRESS_CALLBACK_UNCONFIRMED")
    return result


def finish(job, generation, remote_id, credential):
    if not ID_RE.fullmatch(str(remote_id)):
        raise SafeStop("REMOTE_ID_INVALID")
    # First close WordPress (can release stored file), then the fenced queue.
    # If the second write fails the uncertain job remains reconcilable.
    callback(job, remote_id)
    result = qcall("confirm", credential, {
        "id": job["id"], "lease_generation": generation, "remote_id": remote_id
    })
    if not result.get("ok") or (result.get("job") or {}).get("status") != "confirmed":
        raise SafeStop("QUEUE_CONFIRMATION_UNVERIFIED")
    print("CORTES_TIKTOK_CONFIRMED source=" + job["source_id"] +
          " segment=" + job["segment_id"] + " remote_id=" + remote_id, flush=True)


def inventory(credentials):
    return wcall("/profile-inventory", credentials, timeout=135)


def main():
    control = oidc()
    # Check the independent Neon queue before attempting the TikTok login.
    # Queue health contains no video publication operation.
    health = qcall("health", control)
    if not health.get("ok") or health.get("service") != "cortes-tiktok-neon":
        raise SafeStop("TIKTOK_NEON_QUEUE_UNAVAILABLE")
    print("CORTES_TIKTOK_NEON_HEALTH_OK", flush=True)
    worker = worker_auth()
    session = wcall("/session-status", worker, timeout=50)
    if not (session.get("ok") and session.get("bootstrapped") and session.get("identity_verified")
            and session.get("ready_for_tiktok")):
        print("CORTES_TIKTOK_HOLD_SESSION_NOT_READY", flush=True)
        return 0
    before = inventory(worker)
    if str(before.get("account") or "").lstrip("@").casefold() != ACCOUNT or not before.get("ok"):
        raise SafeStop("TIKTOK_PROFILE_IDENTITY_INVALID")

    response = qcall("claim", control, {})
    if not response.get("ok"):
        raise SafeStop("QUEUE_CLAIM_NOT_ACKNOWLEDGED")
    mode = str(response.get("mode") or "")
    job = response.get("job")
    if mode in ("idle", "busy", "paced", "cap") or not job:
        print("CORTES_TIKTOK_QUEUE_" + (mode or "IDLE").upper(), flush=True)
        return 0
    sid, generation = validate_job(job)

    if mode == "reconcile":
        remote_id = found(before, sid)
        if remote_id:
            finish(job, generation, remote_id, control)
        else:
            print("CORTES_TIKTOK_UNCERTAIN_REQUIRES_PROFILE_RECONCILIATION segment=" + sid, flush=True)
        return 0

    if mode != "publish" or job.get("status") != "leased":
        raise SafeStop("QUEUE_UNEXPECTED_LEASE_STATE")

    try:
        existing = found(before, sid)
        result = qcall("start", control, {"id": job["id"], "lease_generation": generation})
        if not result.get("ok") or (result.get("job") or {}).get("status") != "started":
            raise SafeStop("PUBLICATION_FENCE_NOT_PERSISTED")
    except Exception:
        # If start succeeded but the response was lost, fail() moves it to
        # uncertain rather than creating a duplicate.
        try:
            qcall("fail", control, {
                "id": job["id"], "lease_generation": generation,
                "error": "preflight_or_start_ambiguous"
            })
        except Exception:
            pass
        raise

    try:
        if existing:
            finish(job, generation, existing, control)
            return 0
        print("CORTES_TIKTOK_STARTED segment=" + sid, flush=True)
        plan = {
            "source_id": job["source_id"], "segment_id": sid,
            "source_title": str(job.get("title") or "")[:75],
            "title": caption(job), "expected_tiktok_username": ACCOUNT,
        }
        posted = wcall("/publish-url", worker, {
            "media_url": job["media_url"], "plan": plan,
        }, timeout=415)
        if not (posted.get("ok") and posted.get("confirmed")):
            raise SafeStop("TIKTOK_PUBLISHER_CONFIRMATION_UNAVAILABLE")
        # Never trust the upload click as a post: require the public profile ID.
        for attempt in range(4):
            if attempt:
                time.sleep(10)
            remote_id = found(inventory(worker), sid)
            if remote_id:
                finish(job, generation, remote_id, control)
                return 0
        raise SafeStop("TIKTOK_PROFILE_CONFIRMATION_PENDING")
    except Exception:
        try:
            qcall("fail", control, {
                "id": job["id"], "lease_generation": generation,
                "error": "after_started_reconcile_only",
            })
        except Exception:
            pass
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SafeStop as exc:
        print("CORTES_TIKTOK_SAFE_STOP=" + str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
    except Exception as exc:
        # Never put callback capabilities or authenticated URLs in logs.
        print("CORTES_TIKTOK_UNCERTAIN_ERROR=" + type(exc).__name__, file=sys.stderr, flush=True)
        sys.exit(3)
