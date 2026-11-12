#!/usr/bin/env python3
"""Instagram Reels direct Graph publisher, independent of Buffer.

All mutations use the canonical Neon fenced queue, scoped GitHub Actions OIDC.
A published media request that cannot be verified is left uncertain, never
replayed. Credentials are never printed.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.instagram_publish import InstagramClient
from tools.cortes_queue_ha import post
from anthares_publisher.editorial import branded_title, add_site_to_keywords, WEBSITE
from tools.cortes_instagram_vertical_asset import ensure_vertical_media

AUDIENCE = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
TARGET = "instagram:universoanthares"
OWNER = "instagram-direct:github-cloud-v1"
QUOTA_ISSUE = "https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/2409"
QUOTA_SERVICE = "instagram-direct-graph"


def quota_issue(method: str = "GET", body: dict | None = None) -> dict:
    """Durable, account-scoped provider backoff. Any unreadable state fails closed."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("INSTAGRAM_QUOTA_GATE_TOKEN_MISSING")
    headers = {"Authorization": "Bearer " + token,
               "Accept": "application/vnd.github+json",
               "Content-Type": "application/json",
               "User-Agent": "Anthares-Cortes-Instagram-Quota"}
    request = urllib.request.Request(QUOTA_ISSUE,
        data=json.dumps(body).encode() if body is not None else None,
        method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        doc = json.load(response)
    if not isinstance(doc, dict) or not isinstance(doc.get("body"), str):
        raise RuntimeError("INSTAGRAM_QUOTA_GATE_RESPONSE_INVALID")
    return doc


def quota_record(issue_body: str) -> tuple[dict, re.Match]:
    match = re.search(r"```json\s*(\{[^<>]*?\})\s*```", issue_body, flags=re.S)
    if not match:
        raise RuntimeError("INSTAGRAM_QUOTA_GATE_FORMAT_INVALID")
    record = json.loads(match.group(1))
    if record.get("service") != QUOTA_SERVICE:
        raise RuntimeError("INSTAGRAM_QUOTA_GATE_SCOPE_INVALID")
    return record, match


def quota_hold_until() -> str | None:
    record, _ = quota_record(quota_issue()["body"])
    value = record.get("cooldown_until_utc")
    if not isinstance(value, str):
        return None
    expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if expiry.tzinfo is None:
        raise RuntimeError("INSTAGRAM_QUOTA_GATE_TIMESTAMP_INVALID")
    return value if expiry > datetime.now(timezone.utc) else None


def record_quota_hold() -> str:
    issue = quota_issue()
    record, match = quota_record(issue["body"])
    until = datetime.now(timezone.utc) + timedelta(hours=24)
    value = until.isoformat(timespec="seconds").replace("+00:00", "Z")
    record.update(cooldown_until_utc=value, last_error_code=9,
                  last_error_subcode=2207042,
                  last_error_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    new_fence = "```json\n" + json.dumps(record, indent=2) + "\n```"
    current = issue["body"]
    updated = current[:match.start()] + new_fence + current[match.end():]
    quota_issue("PATCH", {"body": updated})
    return value


def oidc() -> str:
    u = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    u += ("&" if "?" in u else "?") + urllib.parse.urlencode({"audience": AUDIENCE})
    request = urllib.request.Request(u, headers={
        "Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=16) as response:
        return json.load(response)["value"]


def neon(action: str, data: dict | None = None) -> dict:
    res = post("instagram-direct-" + action, data or {}, oidc)
    if not res.get("ok"):
        raise RuntimeError("DIRECT_NEON_ACTION_REJECTED_" + action.upper())
    return res


def require_cloud() -> InstagramClient:
    if not (os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("RUNNER_OS") == "Linux"
            and os.getenv("GITHUB_REPOSITORY") == "UniversoAnthares/anthares-kwai-runner"
            and os.getenv("GITHUB_REF") == "refs/heads/main"
            and os.getenv("GITHUB_WORKFLOW_REF", "").endswith(
                "/.github/workflows/cortes-instagram-direct-cloud.yml@refs/heads/main")):
        raise RuntimeError("INSTAGRAM_DIRECT_HOSTED_WORKFLOW_ONLY")
    if os.getenv("ANTHARES_SOCIAL_COMMIT") != "1":
        raise RuntimeError("INSTAGRAM_DIRECT_DISABLED")
    if not os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") or not os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        raise RuntimeError("INSTAGRAM_DIRECT_OIDC_MISSING")
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN") or ""
    uid = os.getenv("INSTAGRAM_USER_ID") or ""
    if not token or not re.fullmatch(r"[0-9]{6,30}", uid):
        raise RuntimeError("INSTAGRAM_DIRECT_CREDENTIAL_NOT_CONFIGURED")
    preferred = os.getenv("INSTAGRAM_GRAPH_HOST") or "graph.instagram.com"
    allowed = ("graph.instagram.com", "graph.facebook.com")
    if preferred not in allowed:
        raise RuntimeError("INSTAGRAM_DIRECT_UNTRUSTED_GRAPH_HOST")
    # Both Meta login products are supported. Probe each using GET only;
    # no Neon lease or video submission occurs before exact account matching.
    rejected = []
    for host in (preferred, *(name for name in allowed if name != preferred)):
        client = InstagramClient(user_id=uid, access_token=token,
            api_version=os.getenv("INSTAGRAM_API_VERSION") or "v26.0",
            graph_host=host)
        try:
            profile = client._request("GET", uid, query={"fields": "id,username"})
        except Exception as exc:
            # Never print Meta's raw error text (which may include identifiers).
            marker = re.search(r"HTTP\\s+(\\d{3})", str(exc))
            rejected.append(host + ":" + (marker.group(1) if marker else type(exc).__name__))
            continue
        if (str(profile.get("id")) == uid and
                str(profile.get("username", "")).lower() == "universoanthares"):
            print(json.dumps({"direct_cloud":"GRAPH_IDENTITY_VERIFIED",
                              "graph_host":host}), flush=True)
            return client
        rejected.append(host + ":IDENTITY_MISMATCH")
    print(json.dumps({"direct_cloud":"GRAPH_PREFLIGHT_REJECTED",
                      "attempts":rejected}), flush=True)
    raise RuntimeError("INSTAGRAM_DIRECT_ACCOUNT_IDENTITY_UNVERIFIED")


def missing_media(url: str) -> bool:
    p = urllib.parse.urlparse(str(url))
    if (p.scheme != "https" or p.hostname not in ("anthares.us", "www.anthares.us")
            or not p.path.endswith(".mp4") or p.username or p.password):
        raise RuntimeError("DIRECT_MEDIA_URL_INVALID")
    for method in ("HEAD", "GET"):
        h = {"User-Agent": "AntharesCortes-InstagramDirect/1"}
        if method == "GET": h["Range"] = "bytes=0-31"
        req = urllib.request.Request(url, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=17) as response:
                if response.status in (200, 206):
                    return False
                raise RuntimeError("DIRECT_MEDIA_UNEXPECTED_HTTP")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                if method == "GET":
                    return True
                continue
            raise
    return False


def qa_404(job: dict, url: str) -> None:
    print(json.dumps({"warning": "INSTAGRAM_DIRECT_MEDIA_404",
        "priority": "P0", "id": job["id"], "skip": True}), flush=True)
    token = os.getenv("GITHUB_TOKEN") or ""
    if not token:
        return
    body = ("[CORTES QA P0] Instagram Graph: mídia 404 isolada, sem interromper outras publicações. "
            f"Job `{job['id']}`; source {url}. Corrigir antes da próxima rodada; "
            "descarte se permanecer indisponível.")
    req = urllib.request.Request(
        "https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments",
        data=json.dumps({"body": body}).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "CORTES-Instagram-Direct-QA"})
    try:
        with urllib.request.urlopen(req, timeout=15):
            pass
    except (OSError, ValueError):
        print("::warning::INSTAGRAM_DIRECT_QA_ALERT_DELIVERY_FAILED", flush=True)


def instagram_caption(payload: dict, job_id: str | None = None) -> str:
    """Preserve source-specific editorial text and enforce universal branding."""
    title = branded_title(str(payload.get("title") or "").strip(), limit=180)
    description = add_site_to_keywords(str(payload.get("description") or "").strip())
    if WEBSITE not in description:
        description = description.rstrip() + "\n" + WEBSITE
    # Stable public-caption key enables exact chronological reconciliation.
    # An older untagged Reel remains uncertain if no unique proof exists.
    if job_id:
        tag = "#antharescorte" + hashlib.sha256(job_id.encode()).hexdigest()[:12]
        if tag not in description:
            description = description.rstrip() + "\n" + tag
    room = 2200 - len(title) - 1
    if room < len(WEBSITE) + 1:
        raise RuntimeError("DIRECT_CAPTION_TITLE_TOO_LONG")
    if len(description) > room:
        # Keep public proof tag and website even if older text exceeds the API cap.
        suffix = WEBSITE + (("\n" + tag) if job_id else "")
        description = description[:room - len(suffix) - 1].rstrip() + "\n" + suffix
    return title + "\n" + description


def publish_once(client: InstagramClient) -> int:
    claim = neon("lease", {"target_key": TARGET, "owner": OWNER})
    job = claim.get("job")
    if not job:
        print(json.dumps({"direct_cloud": "IDLE", "daily_limit_reached": bool(
            claim.get("daily_limit_reached"))}), flush=True)
        return 0
    fence = {"id": job["id"], "owner": OWNER, "lease_generation": job["lease_generation"]}
    started = False
    phase = "preflight"
    try:
        payload = job.get("payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        if (job.get("target_key") != TARGET or job.get("duration_class") != "short"
                or payload.get("platform") != "instagram"
                or payload.get("account_id") != "universoanthares"):
            raise RuntimeError("DIRECT_QUEUE_TARGET_INVALID")
        url = payload.get("media_url") or payload.get("video_url")
        if missing_media(url):
            neon("missing", fence)
            qa_404(job, url)
            print(json.dumps({"direct_cloud": "QUARANTINED_404", "id": job["id"]}), flush=True)
            return 3
        caption = instagram_caption(payload, job["id"])
        # Build/verify a 9:16 Instagram-only derivative before irreversible Graph submission.
        # The canonical WordPress master and Neon queue identity remain unchanged.
        url = ensure_vertical_media(url, job["id"], payload.get("cortes_attachment_id"),
                                   title=str(payload.get("title") or "Universo Anthares"))
        quota = client.get_quota()
        if (quota.total is not None and quota.usage is not None
                and quota.usage >= quota.total):
            neon("fail", fence)
            print(json.dumps({"direct_cloud": "IDLE_PROVIDER_QUOTA"}), flush=True)
            return 0
        neon("start", fence)
        started = True
        phase = "container_create"
        container = client.create_reel_container(url, caption, share_to_feed=True)
        phase = "container_processing"
        client.wait_until_ready(container, interval=15, attempts=24)
        phase = "media_publish"
        media_id = client.publish_container(container)
        phase = "receipt_verify"
        proof = client._request("GET", media_id, query={"fields": "id,permalink"})
        permalink = str(proof.get("permalink") or "")
        if str(proof.get("id") or "") != media_id:
            raise RuntimeError("DIRECT_INSTAGRAM_MEDIA_ID_UNVERIFIED")
        neon("confirm", {**fence, "media_id": media_id, "permalink": permalink})
        print(json.dumps({"direct_cloud": "INSTAGRAM_REEL_CONFIRMED",
                          "id": job["id"], "permalink": permalink}), flush=True)
        return 1
    except Exception as exc:
        # An uncertain remote submission is fenced and held in Neon. Only a
        # committed fail/hold transition permits progress to another job.
        fenced = False
        try:
            neon("fail", fence)
            fenced = True
        except Exception:
            print("::error::INSTAGRAM_NEON_HOLD_NOT_ACKNOWLEDGED", flush=True)
        # Print only numeric Meta diagnostics; omit potentially sensitive provider messages.
        error_text = str(exc)
        http = re.search(r"HTTP\s+(\d{3})", error_text)
        code = re.search(r"\bcode=(\d+)", error_text)
        subcode = re.search(r"\bsubcode=(\d+)", error_text)
        # Meta explicitly rejected the media_publish call under its 24-hour quota.
        # Persist cooldown before any other scheduled run can claim a new clip.
        quota_stopped = False
        if (phase == "media_publish" and http and http.group(1) == "400"
                and code and code.group(1) == "9"
                and subcode and subcode.group(1) == "2207042"):
            try:
                until = record_quota_hold()
                quota_stopped = True
                print(json.dumps({"direct_cloud": "PROVIDER_QUOTA_COOLDOWN",
                                  "resume_after_utc": until}), flush=True)
            except Exception:
                print("::error::INSTAGRAM_QUOTA_GATE_WRITE_UNACKNOWLEDGED", flush=True)
        print(json.dumps({"direct_cloud": "HELD_UNVERIFIED" if started else "BLOCKED_PRE_SUBMIT",
                          "reason": type(exc).__name__, "id": job["id"],
                          "phase": phase, "http_status": int(http.group(1)) if http else None,
                          "graph_code": int(code.group(1)) if code else None,
                          "graph_subcode": int(subcode.group(1)) if subcode else None,
                          "ledger_fenced": fenced}), flush=True)
        # The rejected media stays fenced; quota resumes without replay after reset.
        return 5 if quota_stopped else (4 if fenced and started else 2)


def daily_publication_window(now: datetime | None = None) -> bool:
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("America/Campo_Grande"))
    return 6 <= local.hour <= 23


def main() -> int:
    if not daily_publication_window():
        print(json.dumps({"direct_cloud": "IDLE_OUTSIDE_DAILY_PUBLICATION_WINDOW",
                          "timezone": "America/Campo_Grande", "opens": "06:00"}), flush=True)
        return 0
    client = require_cloud()
    hold = quota_hold_until()
    if hold:
        # The 24-hour marker is a conservative fallback, not a fixed Meta reset.
        # Meta's authoritative moving-window quota may regain capacity earlier.
        # A failed/unreadable quota check keeps the existing hold (fail closed).
        try:
            live_quota = client.get_quota()
            total = live_quota.total
            used = live_quota.usage
        except Exception:
            total = used = None
        if (not isinstance(total, int) or not isinstance(used, int)
                or total <= 0 or used < 0 or used >= total):
            print(json.dumps({"direct_cloud": "IDLE_PROVIDER_QUOTA_COOLDOWN",
                              "resume_after_utc": hold,
                              "quota_readback": "CAP_REACHED_OR_UNKNOWN"}), flush=True)
            return 0
        print(json.dumps({"direct_cloud": "PROVIDER_QUOTA_REOPENED",
                          "quota_total": total, "quota_usage": used,
                          "quota_remaining": total - used}), flush=True)
    confirmed = 0
    quarantined = 0
    # Two existing fenced queue items per hosted run; Meta quota is checked
    # immediately before each POST and each remote receipt is committed alone.
    for index in range(2):
        state = publish_once(client)
        if state == 2:
            return 2
        if state == 0:
            break
        if state == 1:
            confirmed += 1
        if state == 5:
            quarantined += 1
            print(json.dumps({"direct_cloud": "BATCH_STOPPED_PROVIDER_QUOTA",
                              "confirmed_this_run": confirmed}), flush=True)
            break
        if state == 4:
            quarantined += 1
            # Provider status is ambiguous. Keep the fenced claim for remote
            # readback and stop this invocation before any second submission.
            # Independent scheduled runs can continue with a distinct clip.
            print(json.dumps({"direct_cloud": "BATCH_STOPPED_AFTER_UNCERTAIN",
                              "confirmed_this_run": confirmed,
                              "uncertain_this_run": quarantined}), flush=True)
            break
        if index == 0 and state == 1:
            time.sleep(65)
        # Confirmed posts may continue to a distinct queue item.
    print(json.dumps({"direct_cloud": "BATCH_COMPLETE",
                      "confirmed": confirmed, "fenced_uncertain": quarantined,
                      "maximum_per_run": 2}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"direct_cloud": "BLOCKED", "reason": type(exc).__name__}), flush=True)
        sys.exit(2)
