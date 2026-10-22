#!/usr/bin/env python3
"""GitHub-hosted LinkedIn personal video publisher, one fenced job per invocation.

Reads the personal OAuth credential from Bitwarden at runtime. Never prints
token, identity, media URLs, or API response bodies. Runs only on GitHub cloud.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

from tools.cortes_queue_ha import post
from tools.cortes_social_queue_consumer import _safe_job
from tools.cortes_social_media_probe import available as media_available
from social_adapters.video_social import linkedin, ConfigRequired, PlatformLimit

BASE = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
OWNER = "linkedin-personal:github-cloud-v1"
TARGET = "linkedin:personal"
_MEMBER_SUB = re.compile(r"[A-Za-z0-9_-]{2,200}\Z")


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS") != "true" or
            os.getenv("RUNNER_ENVIRONMENT") != "github-hosted" or
            os.getenv("RUNNER_OS") != "Linux" or
            os.getenv("ANTHARES_SOCIAL_COMMIT") != "1"):
        raise ConfigRequired("LINKEDIN_PERSONAL_CLOUD_ARM_UNAVAILABLE")
    if not os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") or not os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        raise ConfigRequired("GITHUB_OIDC_UNAVAILABLE")
    if not os.getenv("LINKEDIN_PERSONAL_ACCESS_TOKEN"):
        raise ConfigRequired("LINKEDIN_PERSONAL_ACCESS_TOKEN")
    os.environ["CORTES_QUEUE_PRIMARY"] = "neon"


def oidc():
    url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"audience": BASE})
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
                      "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)["value"]


def queue(action, body):
    out = post("personal-" + action, body, oidc)
    if not out.get("ok"):
        raise RuntimeError("PERSONAL_QUEUE_" + action.upper() + "_REJECTED")
    return out


def account_preflight():
    """Verify actual OAuth subject and pin author identity without logging PII."""
    token = os.environ["LINKEDIN_PERSONAL_ACCESS_TOKEN"].strip()
    if not token or any(c in token for c in "\r\n\x00"):
        raise ConfigRequired("PERSONAL_TOKEN_INVALID")
    req = urllib.request.Request("https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET")
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.load(response)
    sub = str(data.get("sub") or "")
    if not _MEMBER_SUB.fullmatch(sub):
        raise ConfigRequired("PERSONAL_MEMBER_ID_UNVERIFIED")
    author = "urn:li:person:" + sub
    configured = os.getenv("LINKEDIN_PERSONAL_AUTHOR_URN", "").strip()
    if configured and configured != author:
        raise ConfigRequired("PERSONAL_ACCOUNT_SWITCH_REJECTED")
    os.environ["LINKEDIN_PERSONAL_AUTHOR_URN"] = author


_PUBLIC_EMBED_CONTROL = "urn:li:ugcPost:0000000000000000000"


def public_embed_status(remote_id: str, *, opener=urllib.request.urlopen) -> int:
    """Read-only unauthenticated HEAD: 200 for existing post, 404 for invalid."""
    if not re.fullmatch(r"urn:li:(?:ugcPost|share):[0-9]{8,25}", str(remote_id)):
        return 0
    uri = "https://www.linkedin.com/embed/feed/update/" + remote_id
    req = urllib.request.Request(uri, method="HEAD", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0 (AntharesLinkedInPublicVerification)"})
    try:
        with opener(req, timeout=18) as response:
            if response.geturl() != uri:
                return 0
            return 200 if response.status == 200 else 0
    except urllib.error.HTTPError as error:
        return 404 if error.code == 404 else 0
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0


def reconcile_personal():
    cloud_only()
    account_preflight()
    rows = (queue("pending", {}).get("jobs") or [])
    if not rows:
        return 0
    if public_embed_status(_PUBLIC_EMBED_CONTROL) != 404:
        print("PERSONAL_PUBLIC_CONTROL_UNAVAILABLE=1", flush=True)
        return 0
    total = 0
    for row in rows:
        remote = str(row.get("remote_id") or "")
        if public_embed_status(remote) != 200:
            print("PERSONAL_PUBLIC_POST_READBACK_PENDING=1", flush=True)
            continue
        try:
            queue("reconcile-public", {"id": row["id"], "remote_id": remote,
                  "public_status": 200, "control_status": 404,
                  "proof_kind": "linkedin_public_embed_head"})
            total += 1
        except RuntimeError:
            print("PERSONAL_PUBLIC_CAS_PENDING=1", flush=True)
    return total


def publish_one(skipped=0):
    print("PERSONAL_STAGE=cloud_preflight", flush=True)
    cloud_only()
    print("PERSONAL_STAGE=identity_preflight", flush=True)
    account_preflight()
    print("PERSONAL_STAGE=queue_lease", flush=True)
    out = queue("lease", {"target_key": TARGET, "owner": OWNER})
    row = out.get("job")
    if not row:
        reason = ("UNRESOLVED_POST" if out.get("unresolved_publication")
                  else "DAILY_LIMIT" if out.get("daily_limit_reached") else "NO_NEW_CUT")
        return {"linkedin_personal": "IDLE", "reason": reason}
    print("PERSONAL_STAGE=job_leased", flush=True)
    fence = {"id": row["id"], "owner": OWNER, "lease_generation": row["lease_generation"]}
    try:
        print("PERSONAL_STAGE=payload_validation", flush=True)
        # Neon/function transports may encode JSONB as an object or serialized
        # JSON. Normalize before validating account, duration, origin and title.
        row_payload = row.get("payload")
        if isinstance(row_payload, str):
            row = {**row, "payload": json.loads(row_payload)}
        try:
            payload = _safe_job(row, "linkedin", "personal")
        except ValueError as error:
            safe_codes = {
                "queue_target_mismatch","queue_payload_missing",
                "queue_duration_class_mismatch","queue_payload_account_mismatch",
                "queue_media_origin_invalid","queue_rendered_duration_invalid",
                "queue_duration_invalid","queue_title_missing",
            }
            key = str(error)
            print("PERSONAL_PAYLOAD_REJECTION=" + (key if key in safe_codes else "UNEXPECTED_VALUE"), flush=True)
            raise
        print("PERSONAL_STAGE=linkedin_preflight", flush=True)
        if linkedin(payload, publish=False).get("status") != "READY":
            raise ConfigRequired("PERSONAL_PREFLIGHT_FAILED")
        print("PERSONAL_STAGE=media_readonly", flush=True)
        if not media_available(payload["media_url"]):
            queue("media-missing", fence)
            return publish_one(skipped + 1) if skipped < 10 else {"linkedin_personal": "SOURCE_MEDIA_MISSING_FOR_REPAIR"}
    except Exception:
        # Nested media-404 skips may have already closed this lease.
        try: queue("fail", fence)
        except Exception: pass
        raise
    print("PERSONAL_STAGE=queue_start", flush=True)
    queue("start", fence)
    try:
        print("PERSONAL_STAGE=linkedin_upload", flush=True)
        response = linkedin(payload, publish=True)
        remote = str(response.get("remote_id") or "")
        if response.get("status") == "CONFIRMED" and remote:
            verified = response.get("confirmation_evidence") or {}
            if verified.get("kind") != "linkedin_author_readback_verified":
                raise RuntimeError("PERSONAL_PROOF_INCOMPLETE")
            queue("confirmed", {**fence, "remote_id": remote,
                  "confirmation_evidence": {"kind": "linkedin_author_readback_verified",
                     "verified_id": remote, "author_verified": True}})
            return {"linkedin_personal": "CONFIRMED_BY_AUTHOR_READBACK"}
        if response.get("status") == "ACCEPTED_UNVERIFIED" and remote:
            queue("accepted", {**fence, "remote_id": remote})
            return {"linkedin_personal": "LINKEDIN_ACCEPTED_PENDING_PUBLIC_PROOF"}
        raise RuntimeError("PERSONAL_REMOTE_CREATION_NOT_PROVEN")
    except Exception:
        # After 'start' the remote may already have created a post.
        # Mark UNCERTAIN. A second worker must never re-upload blindly.
        try:
            queue("fail", fence)
        except Exception:
            pass
        raise


def exception_active():
    local = datetime.now(ZoneInfo("America/Campo_Grande"))
    return (datetime(2026, 10, 21, 22, 45, tzinfo=local.tzinfo)
            <= local <
            datetime(2026, 10, 22, 5, 0, tzinfo=local.tzinfo))


def main():
    try:
        try:
            confirmed_public = reconcile_personal()
            print("PERSONAL_PUBLIC_READBACK_CONFIRMED=" + str(confirmed_public), flush=True)
        except Exception as error:
            # Temporary public lookup failures must not stop independent cuts.
            print("PERSONAL_PUBLIC_READBACK_DEFERRED=" + type(error).__name__, flush=True)
        batch_size = 2 if exception_active() else 1
        for attempt in range(batch_size):
            result = publish_one()
            print(json.dumps({**result, "batch_ordinal": attempt + 1}, separators=(",", ":")), flush=True)
            if result.get("linkedin_personal") != "CONFIRMED_BY_AUTHOR_READBACK" and result.get("linkedin_personal") != "LINKEDIN_ACCEPTED_PENDING_PUBLIC_PROOF":
                break
        return 0
    except (ConfigRequired, PlatformLimit) as exc:
        print(json.dumps({"linkedin_personal": "BLOCKED",
                          "reason": type(exc).__name__}, separators=(",", ":")))
        return 2
    except Exception as exc:
        print(json.dumps({"linkedin_personal": "BLOCKED_OR_UNCERTAIN",
                          "reason": type(exc).__name__}, separators=(",", ":")))
        return 3


if __name__ == "__main__":
    sys.exit(main())
