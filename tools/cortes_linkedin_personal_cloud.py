#!/usr/bin/env python3
"""GitHub-hosted LinkedIn personal video publisher, one fenced job per invocation.

Reads the personal OAuth credential from Bitwarden at runtime. Never prints
token, identity, media URLs, or API response bodies. Runs only on GitHub cloud.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request

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


def publish_one(skipped=0):
    cloud_only()
    account_preflight()
    out = queue("lease", {"target_key": TARGET, "owner": OWNER})
    row = out.get("job")
    if not row:
        reason = ("UNRESOLVED_POST" if out.get("unresolved_publication")
                  else "DAILY_LIMIT" if out.get("daily_limit_reached") else "NO_NEW_CUT")
        return {"linkedin_personal": "IDLE", "reason": reason}
    fence = {"id": row["id"], "owner": OWNER, "lease_generation": row["lease_generation"]}
    try:
        payload = _safe_job(row, "linkedin", "personal")
        if linkedin(payload, publish=False).get("status") != "READY":
            raise ConfigRequired("PERSONAL_PREFLIGHT_FAILED")
        if not media_available(payload["media_url"]):
            queue("media-missing", fence)
            return publish_one(skipped + 1) if skipped < 10 else {"linkedin_personal": "SOURCE_MEDIA_MISSING_FOR_REPAIR"}
    except Exception:
        # Nested media-404 skips may have already closed this lease.
        try: queue("fail", fence)
        except Exception: pass
        raise
    queue("start", fence)
    try:
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


def main():
    try:
        result = publish_one()
        print(json.dumps(result, separators=(",", ":")))
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
