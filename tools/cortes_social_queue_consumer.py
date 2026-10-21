#!/usr/bin/env python3
"""One-job Neon queue consumer for CORTES Pinterest/LinkedIn video masters.

Account identity, credentials and live-publish arm gate MUST be verified
before claiming any job. The canonical Neon queue owns leases, fencing and
idempotency; this process does not create another ledger or reset unknown jobs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "social_adapters"))

from cortes_neon_queue_client import call
from video_social import pinterest, linkedin, ConfigRequired, PlatformLimit, PublishUncertain

_ALLOWED_ORIGINS = {"anthares.us", "www.anthares.us"}


def prerequisites(platform, account):
    if platform not in ("pinterest", "linkedin"):
        raise ValueError("unsupported_platform")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{2,80}", account):
        raise ValueError("invalid_account_id")
    if os.getenv("ANTHARES_SOCIAL_COMMIT") != "1":
        raise ConfigRequired("ANTHARES_SOCIAL_COMMIT=1 required")
    if not os.getenv("ANTHARES_DEVICE_TOKEN", "").strip():
        raise ConfigRequired("ANTHARES_DEVICE_TOKEN")
    required = {
        "pinterest": ("PINTEREST_ACCESS_TOKEN", "PINTEREST_BOARD_ID",
                      "PINTEREST_COVER_IMAGE_URL"),
        "linkedin": ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN"),
    }[platform]
    for name in required:
        if not os.getenv(name, "").strip():
            raise ConfigRequired(name)


def _safe_job(row, platform, account):
    if not isinstance(row, dict) or row.get("target_key") != platform + ":" + account:
        raise ValueError("queue_target_mismatch")
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("queue_payload_missing")
    if row.get("duration_class") != "short":
        raise ValueError("queue_duration_class_mismatch")
    url = str(payload.get("media_url") or payload.get("video_url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_ORIGINS or parsed.username or parsed.password:
        raise ValueError("queue_media_origin_invalid")
    time_ms = payload.get("rendered_duration_ms")
    seconds = payload.get("duration_seconds")
    if time_ms is not None and not 30 <= int(time_ms) / 1000 <= 90:
        raise ValueError("queue_rendered_duration_invalid")
    if seconds is not None and not 30 <= float(seconds) <= 90:
        raise ValueError("queue_duration_invalid")
    title = str(payload.get("title") or payload.get("video_title") or "").strip()
    if not title:
        raise ValueError("queue_title_missing")
    return {
        "platform": platform, "account_id": account, "media_url": url,
        "media_type": "video", "title": title,
        "description": str(payload.get("description") or ""),
        "cover_image_url": str(payload.get("cover_image_url") or ""),
    }


def once(platform, account):
    prerequisites(platform, account)
    target = platform + ":" + account
    owner = "social_video:" + platform + ":" + os.getenv("ANTHARES_DEVICE_ID", "DESKTOP-FTDK0HP")
    leased = call("lease", {"target_key": target, "owner": owner, "lease_seconds": 3600})
    if not leased.get("ok"):
        raise RuntimeError("queue_lease_rejected")
    if not leased.get("job"):
        return {"status": "IDLE", "target_key": target,
                "limit_reached": leased.get("daily_limit_reached", False)}
    row = leased["job"]
    fence = {"id": row["id"], "owner": owner, "lease_generation": row["lease_generation"]}
    try:
        payload = _safe_job(row, platform, account)
        publisher = {"pinterest": pinterest, "linkedin": linkedin}[platform]
        prepared = publisher(payload, publish=False)
        if prepared.get("status") != "READY":
            raise ConfigRequired("provider_preflight_not_ready")
    except Exception:
        # Post has not started. This returns the leased job to queue without
        # incrementing publication state; the operator should fix configuration.
        call("fail", fence)
        raise
    started = call("start", fence)
    if not started.get("ok"):
        raise RuntimeError("stale_or_invalid_queue_fence")
    try:
        outcome = publisher(payload, publish=True)
        if outcome.get("status") != "CONFIRMED" or not outcome.get("remote_id"):
            raise PublishUncertain("remote_publication_not_verified")
        evidence = outcome.get("confirmation_evidence") or {}
        if not evidence.get("verified_id"):
            raise PublishUncertain("remote_verification_missing")
        confirmed = call("confirm", {
            **fence,
            "remote_id": outcome["remote_id"],
            "confirmation_evidence": {
                "kind": "social_video_verified_remote_id",
                "platform": platform,
                "verified_id": evidence["verified_id"],
                "permalink": evidence.get("permalink", ""),
            },
        })
        if not confirmed.get("ok"):
            raise PublishUncertain("neon_confirmation_failed")
        return {"status": "CONFIRMED", "target_key": target,
                "remote_id": outcome["remote_id"]}
    except Exception:
        # A call might already have created a public post. Mark UNCERTAIN and
        # reconcile independently; NEVER allow blind retry or alternate executor.
        try:
            call("fail", fence)
        except Exception:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description="Consume one fenced social video job")
    parser.add_argument("--platform", choices=("pinterest", "linkedin"), required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--preflight", action="store_true",
                        help="Only check arming and secret presence; no queue calls")
    args = parser.parse_args()
    try:
        prerequisites(args.platform, args.account)
        result = {"status": "READY", "platform": args.platform} if args.preflight else once(args.platform, args.account)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except ConfigRequired as exc:
        print(json.dumps({"status": "AUTH_OR_CONFIG_REQUIRED", "missing": str(exc)}))
        return 3
    except PlatformLimit:
        print('{"status":"BLOCKED_PLATFORM_LIMIT"}')
        return 4
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_OR_UNCERTAIN", "reason": type(exc).__name__}))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
