#!/usr/bin/env python3
"""CORTES -> TikTok: one fenced, reconciled publication per scheduled tick.

WordPress is the canonical media/destination ledger. TikTok's authenticated
Anthares publisher performs the actual upload. A marked attempt is NEVER
blindly retried after a possible publication.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlsplit

ACCOUNT = "universo.anthares"
WORKER = os.environ.get("ANTHARES_TIKTOK_WORKER_URL", "https://anthares-tiktok-worker.anthares1.workers.dev").rstrip("/")
EXPECTED_WORKER_HOST = "anthares-tiktok-worker.anthares1.workers.dev"
WP = os.environ.get("WP_SITE_URL", "").strip().rstrip("/")
TIMEOUT = 40
MIN_GAP_SECONDS = 10 * 60
MAX_PER_DAY = 100


class Blocked(RuntimeError):
    """Fail safely before crossing the TikTok publication boundary."""


def _json_request(url: str, headers: dict, payload=None, timeout=TIMEOUT) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST" if payload is not None else "GET",
                                 headers=dict(headers, **({"Content-Type": "application/json"} if body is not None else {})))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        # Return only a small allowlisted error code, never headers, cookies or JWTs.
        detail = ""
        try:
            payload = json.loads(exc.read(1024).decode("utf-8", "replace"))
            raw = str((payload or {}).get("error") or "") if isinstance(payload, dict) else ""
            if re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", raw):
                detail = "_" + raw
        except (ValueError, UnicodeError, OSError):
            pass
        raise Blocked("HTTP_" + str(exc.code) + "_FROM_" + str(urlsplit(url).hostname) + detail) from exc
    except (TimeoutError, OSError, ValueError) as exc:
        raise Blocked("REQUEST_UNCERTAIN_" + type(exc).__name__) from exc
    if not isinstance(data, dict):
        raise Blocked("INVALID_RESPONSE")
    return data


def wp_headers() -> dict:
    user = os.getenv("WP_USERNAME", "").strip()
    password = "".join(os.getenv("WP_APP_PASSWORD", "").split())
    if not (WP.startswith("https://") and user and password):
        raise Blocked("WORDPRESS_CREDENTIALS_MISSING")
    auth = base64.b64encode((user + ":" + password).encode()).decode()
    return {"Authorization": "Basic " + auth, "Accept": "application/json"}


def oidc_headers() -> dict:
    # Northflank was provisioned with ARA_SHARED as RENDER_WORKER_TOKEN.
    # A GitHub-hosted public runner can use this existing authenticated channel.
    shared = os.getenv("ARA_SHARED", "").strip()
    if shared:
        if urlsplit(WORKER).hostname != EXPECTED_WORKER_HOST:
            raise Blocked("TIKTOK_WORKER_HOST_NOT_ALLOWED")
        return {"Authorization": "Bearer " + shared, "Accept": "application/json"}
    url = os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    token = os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not url or not token:
        raise Blocked("GITHUB_OIDC_MISSING")
    sep = "&" if "?" in url else "?"
    endpoint = url + sep + urllib.parse.urlencode({"audience": "anthares-render-worker"})
    data = _json_request(endpoint, {"Authorization": "Bearer " + token, "Accept": "application/json"})
    bearer = str(data.get("value") or "")
    if not bearer:
        raise Blocked("GITHUB_OIDC_EMPTY")
    if urlsplit(WORKER).hostname != EXPECTED_WORKER_HOST:
        raise Blocked("TIKTOK_WORKER_HOST_NOT_ALLOWED")
    return {"Authorization": "Bearer " + bearer, "Accept": "application/json"}


def segment_id(clip: dict) -> str:
    return str(clip.get("segment_id") or clip.get("clip_id") or "").strip()


def marker(sid: str) -> str:
    return "#anthares" + hashlib.sha256((ACCOUNT + ":" + sid).encode()).hexdigest()[:10]


def caption(blocker: dict, clip: dict) -> str:
    original = " ".join(str(clip.get("titulo") or clip.get("title") or blocker.get("title") or "Literatura e escrita").split())
    original = re.sub(r"[\r\n\t]+", " ", original)
    return original[:76].rstrip(" .,-") + " " + marker(segment_id(clip))


def post_id_for_marker(inventory: dict, target: str) -> str:
    if not inventory.get("ok") or str(inventory.get("account") or "").lstrip("@").casefold() != ACCOUNT:
        raise Blocked("TIKTOK_INVENTORY_ACCOUNT_UNVERIFIED")
    found = {}
    for video in inventory.get("items") or []:
        body = " ".join(str(video.get("text") or "").casefold().split())
        remote_id = str(video.get("id") or "")
        if remote_id and target in body:
            found[remote_id] = True
    if len(found) > 1:
        raise Blocked("TIKTOK_MARKER_COLLISION")
    return next(iter(found), "")


def valid_clip(clip: dict) -> bool:
    if not isinstance(clip, dict) or clip.get("type") != "short" or clip.get("stored") is False:
        return False
    if not segment_id(clip) or not int(clip.get("attachment_id") or 0):
        return False
    try:
        duration = float(clip.get("duration_seconds") or 0)
    except (TypeError, ValueError):
        return False
    return 30 <= duration <= 90 and str(clip.get("url") or "").startswith("https://")


def pick(state: dict):
    blocker = state.get("blocker")
    if not isinstance(blocker, dict) or not blocker.get("video_id"):
        return None, []
    clips = [c for c in blocker.get("clips") or [] if valid_clip(c)]
    unresolved = []
    ready = []
    for c in clips:
        status = str(((c.get("networks") or {}).get("tiktok") or {}).get("status") or "")
        if status in ("processing", "uncertain"):
            unresolved.append(c)
        elif status in ("", "pending"):
            ready.append(c)
    ready.sort(key=lambda c: (str(c.get("planned_at") or ""), segment_id(c)))
    return (blocker, ready), unresolved


def get_network_enabled(state: dict) -> bool:
    return any(n.get("key") == "tiktok" and n.get("enabled") and "short" in (n.get("types") or [])
               for n in state.get("networks") or [])


def posting_pace(state: dict, now: datetime):
    rows = []
    for live in state.get("items") or []:
        for clip in live.get("clips") or []:
            net = ((clip.get("networks") or {}).get("tiktok") or {})
            if net.get("status") != "completed":
                continue
            try:
                ts = datetime.fromisoformat(str(net.get("updated_at") or "").replace("Z", "+00:00")).astimezone(timezone.utc)
                rows.append(ts)
            except (TypeError, ValueError):
                pass
    today = now.astimezone(timezone(timedelta(hours=-4))).date()
    if sum(x.astimezone(timezone(timedelta(hours=-4))).date() == today for x in rows) >= MAX_PER_DAY:
        raise Blocked("TIKTOK_DAILY_CAP")
    if rows and (now - max(rows)).total_seconds() < MIN_GAP_SECONDS:
        raise Blocked("TIKTOK_PACING_COOLDOWN")


def main() -> int:
    if os.getenv("CORTES_TIKTOK_DRY_RUN", "0") == "1":
        print("TIKTOK_CORTES_DRY_RUN_NO_MUTATIONS")
        return 0
    auth_wp = wp_headers()
    auth_tiktok = oidc_headers()
    session = _json_request(WORKER + "/session-status", auth_tiktok, timeout=50)
    if not (session.get("ok") and session.get("bootstrapped") and session.get("identity_verified")
            and session.get("ready_for_tiktok")):
        raise Blocked("TIKTOK_SESSION_NOT_READY")
    if os.getenv("CORTES_TIKTOK_PREFLIGHT", "0") == "1":
        base = WP + "/wp-json/anthares/v1/cortes/"
        state = _json_request(base + "state", auth_wp)
        choice, unresolved = pick(state)
        count = len(choice[1]) if choice else 0
        print("TIKTOK_CORTES_PREFLIGHT session_ready=1 source_present="
              + str(bool(choice)) + " ready_clips=" + str(count)
              + " unresolved=" + str(len(unresolved))
              + " tiktok_network_enabled=" + str(get_network_enabled(state)), flush=True)
        return 0
    inventory = _json_request(WORKER + "/profile-inventory", auth_tiktok, timeout=130)
    if not inventory.get("ok") or str(inventory.get("account") or "").lstrip("@").lower() != ACCOUNT:
        raise Blocked("TIKTOK_PROFILE_UNVERIFIED")

    base = WP + "/wp-json/anthares/v1/cortes/"
    state = _json_request(base + "state", auth_wp)
    choice, unresolved = pick(state)
    if choice is None:
        print("TIKTOK_CORTES_IDLE_NO_SOURCE")
        return 0
    blocker, ready = choice

    # Every uncertain previous request is reconciled from the account inventory.
    # An absent post remains held for manual review; never submit twice on doubt.
    for old in unresolved:
        existing_id = post_id_for_marker(inventory, marker(segment_id(old)))
        if existing_id:
            completed = _json_request(base + "clip-network", auth_wp, {
                "video_id": blocker["video_id"], "clip_id": segment_id(old),
                "attachment_id": int(old["attachment_id"]), "network": "tiktok",
                "account_id": "primary", "status": "completed", "remote_id": existing_id,
            })
            if not completed:
                raise Blocked("TIKTOK_RECONCILE_WRITE_FAILED")
            print("TIKTOK_CORTES_RECONCILED segment=" + segment_id(old) + " remote_id=" + existing_id)
            return 0
    if unresolved:
        raise Blocked("TIKTOK_UNCERTAIN_PREVIOUS_POST_REQUIRES_REVIEW")

    if not ready:
        print("TIKTOK_CORTES_IDLE_NO_PENDING_SHORT")
        return 0
    now = datetime.now(timezone.utc)
    posting_pace(state, now)
    clip = ready[0]
    sid = segment_id(clip)
    target = marker(sid)
    already = post_id_for_marker(inventory, target)
    if already:
        raise Blocked("TIKTOK_EXISTING_MARKED_POST_NEEDS_MANUAL_RECONCILIATION")
    video_url = str(clip["url"])
    if urlsplit(video_url).hostname != urlsplit(WP).hostname:
        raise Blocked("CORTES_MEDIA_HOST_MISMATCH")

    if not get_network_enabled(state):
        enabled = _json_request(base + "network", auth_wp, {"key": "tiktok", "label": "TikTok",
                                                            "types": ["short"], "enabled": True})
        if not enabled.get("ok") or not (enabled.get("network") or {}).get("enabled"):
            raise Blocked("TIKTOK_NETWORK_ACTIVATION_FAILED")
        print("TIKTOK_CORTES_NETWORK_ENABLED=1")

    # Persist fencing BEFORE submitting the irreversible upload request.
    processing = _json_request(base + "clip-network", auth_wp, {
        "video_id": blocker["video_id"], "clip_id": sid,
        "attachment_id": int(clip["attachment_id"]), "network": "tiktok",
        "account_id": "primary", "status": "processing", "remote_id": "",
    })
    changed = [x for x in processing.get("clips") or [] if segment_id(x) == sid]
    if len(changed) != 1 or ((changed[0].get("networks") or {}).get("tiktok") or {}).get("status") != "processing":
        raise Blocked("TIKTOK_PROCESSING_FENCE_UNCONFIRMED")

    plan = {"source_id": str(blocker["video_id"]), "segment_id": sid,
            "source_title": str(blocker.get("title") or ""), "title": caption(blocker, clip),
            "expected_tiktok_username": ACCOUNT}
    print("TIKTOK_CORTES_STARTED segment=" + sid, flush=True)
    try:
        answer = _json_request(WORKER + "/publish-url", auth_tiktok, {
            "media_url": video_url, "plan": plan,
        }, timeout=410)
    except Exception:
        print("TIKTOK_CORTES_UNCERTAIN_AFTER_START segment=" + sid, flush=True)
        raise

    # UI success alone does not suffice. Verify the public profile independently.
    if not answer.get("ok") or not answer.get("confirmed"):
        raise Blocked("TIKTOK_PUBLISHER_NO_CONFIRMED_UI_RESULT")
    for attempt in range(4):
        if attempt:
            time.sleep(8)
        after = _json_request(WORKER + "/profile-inventory", auth_tiktok, timeout=130)
        remote_id = post_id_for_marker(after, target)
        if remote_id:
            result = _json_request(base + "clip-network", auth_wp, {
                "video_id": blocker["video_id"], "clip_id": sid,
                "attachment_id": int(clip["attachment_id"]), "network": "tiktok",
                "account_id": "primary", "status": "completed", "remote_id": remote_id,
            })
            rows = [x for x in result.get("clips") or [] if segment_id(x) == sid]
            if len(rows) != 1 or ((rows[0].get("networks") or {}).get("tiktok") or {}).get("status") != "completed":
                raise Blocked("TIKTOK_WORDPRESS_CONFIRMATION_UNVERIFIED")
            print("TIKTOK_CORTES_CONFIRMED segment=" + sid + " remote_id=" + remote_id)
            return 0
    raise Blocked("TIKTOK_PROFILE_CONFIRMATION_PENDING_NO_RETRY")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Blocked as exc:
        print("TIKTOK_CORTES_BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print("TIKTOK_CORTES_ERROR " + type(exc).__name__, file=sys.stderr)
        sys.exit(3)
