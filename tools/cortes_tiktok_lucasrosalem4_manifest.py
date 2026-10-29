#!/usr/bin/env python3
"""Validate the @lucasrosalem4 source manifest in canonical Neon, without PC storage.

The primary publisher already persists immutable clip URLs in Neon. The
GitHub-hosted workflow reads its signed, account-isolated source-manifest
endpoint; no local queue, manifest, media or publishing state is created here.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

AUDIENCE = "https://anthares-remote-primary.vercel.app/api/cortes-tiktok"
SOURCE = "https://br-crimson-unit-b89nau08-cortestiktok.compute.c-14.us-east-1.aws.neon.tech/"
ACCOUNT = "lucasrosalem4"
SEGMENT = re.compile(r"^g[0-9]+:([A-Za-z0-9_-]{6,60}):[0-9]+:[0-9]+$")


def request_json(url, token=None, timeout=25):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if "json" not in str(response.headers.get("Content-Type") or "").lower():
            raise RuntimeError("SECONDARY_MANIFEST_INVALID_CONTENT_TYPE")
        data = json.load(response)
    if not isinstance(data, dict):
        raise RuntimeError("SECONDARY_MANIFEST_JSON_OBJECT_REQUIRED")
    return data


def oidc():
    base = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    authorization = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not base or not authorization or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("SECONDARY_MANIFEST_CANONICAL_GITHUB_IDENTITY_REQUIRED")
    url = base + ("&" if "?" in base else "?") + urllib.parse.urlencode({"audience": AUDIENCE})
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + authorization,
                                               "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                result = json.load(response)
            value = str(result.get("value") or "")
            if 200 <= len(value) <= 16000:
                return value
            raise RuntimeError("SECONDARY_MANIFEST_JWT_UNAVAILABLE")
        except urllib.error.HTTPError as error:
            if error.code not in (500, 502, 503, 504) or attempt == 3:
                raise
        except (urllib.error.URLError, OSError):
            if attempt == 3:
                raise
        time.sleep((2, 5, 10)[attempt])
    raise RuntimeError("SECONDARY_MANIFEST_OIDC_RETRIES_EXHAUSTED")


def valid_clip(clip):
    if not isinstance(clip, dict):
        return False
    match = SEGMENT.fullmatch(str(clip.get("segment_id") or ""))
    if not match or str(clip.get("source_id") or "") != match.group(1):
        return False
    url = urllib.parse.urlsplit(str(clip.get("media_url") or ""))
    if url.scheme != "https" or url.hostname not in ("anthares.us", "www.anthares.us"):
        return False
    if not url.path.startswith("/wp-content/uploads/") or url.username or url.password:
        return False
    try:
        return 30 <= float(clip.get("duration_seconds") or 0) <= 90 and len(str(clip.get("title") or "")) >= 8
    except (TypeError, ValueError):
        return False


def validate_remote_manifest(response, expected_day=None):
    """Prove source integrity without caching, merging or writing a manifest."""
    if not isinstance(response, dict) or not response.get("ok") or response.get("account") != ACCOUNT:
        raise RuntimeError("SECONDARY_MANIFEST_UPSTREAM_ACCOUNT_UNVERIFIED")
    day = str(response.get("date") or "")
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", day):
        raise RuntimeError("SECONDARY_MANIFEST_DAY_INVALID")
    today = expected_day or datetime.now(ZoneInfo("America/Campo_Grande")).strftime("%Y-%m-%d")
    if day != today:
        raise RuntimeError("SECONDARY_MANIFEST_NEON_LOCAL_DAY_MISMATCH")
    received = response.get("clips")
    if not isinstance(received, list) or len(received) > 100:
        raise RuntimeError("SECONDARY_MANIFEST_CAP_OR_FORMAT_INVALID")
    count = response.get("clip_count")
    if type(count) is not int or count != len(received):
        raise RuntimeError("SECONDARY_MANIFEST_REMOTE_COUNT_MISMATCH")
    seen = set()
    for clip in received:
        if not valid_clip(clip):
            raise RuntimeError("SECONDARY_MANIFEST_CLIP_VALIDATION_FAILED")
        segment = clip["segment_id"]
        if segment in seen:
            raise RuntimeError("SECONDARY_MANIFEST_DUPLICATE_SEGMENT")
        seen.add(segment)
    return {"day": day, "count": len(received)}


def main():
    response = request_json(SOURCE + "?action=source-manifest", oidc())
    verified = validate_remote_manifest(response)
    print("SECONDARY_TIKTOK_NEON_SOURCE_VERIFIED count=" + str(verified["count"])
          + " day=" + verified["day"] + " storage=remote_only read_only=1", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("SECONDARY_TIKTOK_MANIFEST_ERROR=" + type(exc).__name__, file=sys.stderr, flush=True)
        sys.exit(2)
