#!/usr/bin/env python3
"""Instagram Reels direct Graph publisher, independent of Buffer.

All mutations use the canonical Neon fenced queue, scoped GitHub Actions OIDC.
A published media request that cannot be verified is left uncertain, never
replayed. Credentials are never printed.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.instagram_publish import InstagramClient
from tools.cortes_queue_ha import post

AUDIENCE = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
TARGET = "instagram:universoanthares"
OWNER = "instagram-direct:github-cloud-v1"


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


def main() -> int:
    client = require_cloud()
    claim = neon("lease", {"target_key": TARGET, "owner": OWNER})
    job = claim.get("job")
    if not job:
        print(json.dumps({"direct_cloud": "IDLE", "daily_limit_reached": bool(
            claim.get("daily_limit_reached"))}), flush=True)
        return 0
    fence = {"id": job["id"], "owner": OWNER, "lease_generation": job["lease_generation"]}
    started = False
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
            return 0
        caption = ((payload.get("title") or "").strip() + "\n"
                   + (payload.get("description") or "").strip())[:2200]
        if not caption.strip():
            raise RuntimeError("DIRECT_CAPTION_EMPTY")
        quota = client.get_quota()
        if (quota.total is not None and quota.usage is not None
                and quota.usage >= quota.total):
            neon("fail", fence)
            print(json.dumps({"direct_cloud": "IDLE_PROVIDER_QUOTA"}), flush=True)
            return 0
        neon("start", fence)
        started = True
        container = client.create_reel_container(url, caption, share_to_feed=True)
        client.wait_until_ready(container, interval=15, attempts=24)
        media_id = client.publish_container(container)
        proof = client._request("GET", media_id, query={"fields": "id,permalink"})
        permalink = str(proof.get("permalink") or "")
        if str(proof.get("id") or "") != media_id:
            raise RuntimeError("DIRECT_INSTAGRAM_MEDIA_ID_UNVERIFIED")
        neon("confirm", {**fence, "media_id": media_id, "permalink": permalink})
        print(json.dumps({"direct_cloud": "INSTAGRAM_REEL_CONFIRMED",
                          "id": job["id"], "permalink": permalink}), flush=True)
        return 0
    except Exception as exc:
        try:
            neon("fail", fence)
        except Exception:
            pass
        print(json.dumps({"direct_cloud": "HELD_UNVERIFIED" if started else "BLOCKED_PRE_SUBMIT",
                          "reason": type(exc).__name__, "id": job["id"]}), flush=True)
        # No automatic replay after a submission has started.
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"direct_cloud": "BLOCKED", "reason": type(exc).__name__}), flush=True)
        sys.exit(2)
