#!/usr/bin/env python3
"""LinkedIn PERSONAL video consumer, independent of corporate Buffer worker.

Neon Functions is the canonical shared ledger; GitHub OIDC authenticates this
specific workflow. A personal OAuth token from the *member* is mandatory.
No local computer, no fallback to company page, no blind retry of uploads/posts.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from social_adapters import linkedin_personal as member

NEON = "https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/"
AUD = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
OWNER = "linkedin-personal:github-cloud"
DEST = "linkedin:personal"


def oidc():
    from tools.cortes_linkedin_neon_fanout import oidc as fresh_oidc
    return fresh_oidc()


def queue(action, payload=None):
    if action not in ("lease", "start", "fail", "uncertain", "confirm", "pending", "stats"):
        raise RuntimeError("PERSONAL_QUEUE_ACTION_NOT_ALLOWED")
    req = urllib.request.Request(
        NEON + "?action=personal-" + action, method="POST",
        data=json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":")).encode(),
        headers={"Authorization": "Bearer " + oidc(),
                 "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=32) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("PERSONAL_QUEUE_HTTP_" + str(exc.code)) from None
    except (OSError, TimeoutError, ValueError):
        raise RuntimeError("PERSONAL_QUEUE_RESULT_UNCERTAIN") from None
    if not result.get("ok"):
        raise RuntimeError("PERSONAL_QUEUE_REJECTED_" + action)
    return result


def safe_job(row):
    if row.get("target_key") != DEST or row.get("duration_class") != "short":
        raise RuntimeError("PERSONAL_WRONG_TARGET")
    payload = row.get("payload") or {}
    if (payload.get("platform") != "linkedin_personal" or
        payload.get("account_id") != "personal"):
        raise RuntimeError("PERSONAL_WRONG_ACCOUNT")
    return {
        "target_key": DEST,
        "media_url": payload.get("media_url") or payload.get("video_url"),
        "duration_seconds": payload.get("duration_seconds"),
        "title": payload.get("title") or payload.get("video_title"),
        "description": payload.get("description") or "",
    }


def reconcile_pending():
    jobs = queue("pending").get("jobs") or []
    total = 0
    for job in jobs:
        remote = str(job.get("remote_id") or "")
        if not remote:
            # An unknown prior post ID cannot be safely submitted again.
            continue
        try:
            urn = member.person_identity()
            post = member.api("GET", member.BASE + "/rest/posts/" +
                              urllib.parse.quote(remote, safe=""))
            if (post.get("id") != remote or post.get("author") != urn or
                post.get("visibility") != "PUBLIC" or
                post.get("lifecycleState") != "PUBLISHED"):
                continue
            queue("confirm", {"id": job["id"], "owner": OWNER,
                 "lease_generation": job["lease_generation"],
                 "remote_id": remote,
                 "external_link": "https://www.linkedin.com/feed/update/" + remote})
            total += 1
        except (member.PersonalAuthRequired, member.PersonalUncertain, RuntimeError):
            # One uncertain post cannot suspend the next eligible master.
            print("LINKEDIN_PERSONAL_RECONCILIATION_PENDING=1", flush=True)
            continue
    return total


def publish_one():
    result = queue("lease", {"target_key": DEST, "owner": OWNER})
    row = result.get("job")
    if not row:
        return "IDLE_NO_ELIGIBLE_CUTS"
    fence = {"id": row["id"], "lease_generation": row["lease_generation"], "owner": OWNER}
    try:
        payload = safe_job(row)
        member.media_url(payload["media_url"])
        if not 30 <= float(payload["duration_seconds"]) <= 90:
            raise RuntimeError("PERSONAL_WRONG_DURATION")
    except Exception:
        queue("fail", fence)
        raise
    queue("start", fence)
    try:
        posted = member.create_public_video(payload)
        if posted.get("status") == "CONFIRMED":
            queue("confirm", {**fence, "remote_id": posted["remote_id"],
                              "external_link": posted["external_link"]})
            return "CONFIRMED_ON_PERSONAL_LINKEDIN"
        if posted.get("status") == "UNCERTAIN":
            queue("uncertain", {**fence, "remote_id": posted["remote_id"]})
            return "PERSONAL_PUBLICATION_PENDING_CONFIRMATION"
        raise RuntimeError("PERSONAL_PUBLISH_NOT_CONFIRMED")
    except Exception:
        # A timeout AFTER post creation is ambiguous; never blindly repost.
        try:
            queue("fail", fence)
        except Exception:
            pass
        raise


def main():
    member.cloud_only()
    # Validate exact member token and pinned identity before leasing.
    member.person_identity()
    confirmed = reconcile_pending()
    posted = publish_one()
    print(json.dumps({"ok": True, "member_network": DEST, "result": posted,
                      "confirmed_reconciled": confirmed}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "member_network": DEST,
                          "error_class": type(exc).__name__}, separators=(",", ":")))
        sys.exit(2)
