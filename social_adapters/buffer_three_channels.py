#!/usr/bin/env python3
"""CORTES Buffer adapter for Instagram, Pinterest and LinkedIn.

A Buffer API credential is injected securely by the Bitwarden GitHub action.
This module does not claim Neon jobs, schedule recurring jobs or confirm posts.
Writes are impossible unless ANTHARES_SOCIAL_COMMIT=1 and a real channel ID is
explicitly pinned. Buffer queue acceptance is NOT proof of social publication.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from anthares_publisher.editorial import branded_title, add_site_to_keywords

ENDPOINT = "https://api.buffer.com"
SERVICES = ("instagram", "pinterest", "linkedin")
LABEL = "Universo Anthares"
LINKEDIN_COMPANY = "145345334"


class BufferBlocked(RuntimeError):
    pass


def api(query: str, token: str | None = None) -> dict:
    secret = (token or os.getenv("BUFFER_API_KEY") or "").strip()
    if not secret:
        raise BufferBlocked("BUFFER_API_KEY_MISSING")
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query}, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization": "Bearer " + secret, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "AntharesBufferCortes/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise BufferBlocked("BUFFER_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise BufferBlocked("BUFFER_RESPONSE_UNCERTAIN") from None
    if not isinstance(result, dict) or result.get("errors") or not isinstance(result.get("data"), dict):
        raise BufferBlocked("BUFFER_GRAPHQL_OR_DATA_ERROR")
    return result["data"]


def channels(token: str | None = None) -> list[dict]:
    account = api("query { account { organizations { id name } } }", token).get("account") or {}
    output = []
    for organization in account.get("organizations") or []:
        org_id = str(organization.get("id") or "")
        if not org_id:
            continue
        query = ("query { channels(input: { organizationId: " + json.dumps(org_id) +
                 " }) { id name displayName service externalLink type isDisconnected isLocked isQueuePaused } }")
        output.extend(api(query, token).get("channels") or [])
    return output


def validate_channel(platform: str, channel_id: str, available: list[dict]) -> dict:
    if platform not in SERVICES:
        raise BufferBlocked("UNSUPPORTED_PLATFORM")
    if not channel_id:
        raise BufferBlocked("BUFFER_CHANNEL_ID_REQUIRED")
    exact = [x for x in available if str(x.get("id") or "") == channel_id]
    if len(exact) != 1:
        raise BufferBlocked("BUFFER_CHANNEL_NOT_FOUND_OR_AMBIGUOUS")
    entry = exact[0]
    service = str(entry.get("service") or "").lower()
    if service != platform:
        raise BufferBlocked("BUFFER_SERVICE_MISMATCH")
    if entry.get("isQueuePaused") or entry.get("isLocked") or entry.get("isDisconnected"):
        raise BufferBlocked("BUFFER_CHANNEL_UNAVAILABLE")
    name = " ".join(str(entry.get("displayName") or entry.get("name") or "").casefold().split())
    # Names must be verified with the connected social account. Do not match
    # a personal LinkedIn profile when the page is the required target.
    if platform == "linkedin":
        if name != LABEL.casefold():
            raise BufferBlocked("LINKEDIN_PAGE_NAME_MISMATCH")
        link = str(entry.get("externalLink") or "").strip()
        uri = urllib.parse.urlparse(link if "://" in link else "https://" + link)
        if (uri.hostname or "").lower() not in ("linkedin.com", "www.linkedin.com") or uri.path.rstrip("/") not in ("/company/" + LINKEDIN_COMPANY, "/company/universo-anthares"):
            raise BufferBlocked("LINKEDIN_PAGE_URL_UNVERIFIED")
        if str(entry.get("type") or "").lower() not in ("page", "company"):
            raise BufferBlocked("LINKEDIN_CHANNEL_NOT_PAGE")
    if platform == "instagram" and "universoanthares" not in name.replace(" ", ""):
        raise BufferBlocked("INSTAGRAM_IDENTITY_UNVERIFIED")
    if platform == "pinterest" and "anthares" not in name.replace(" ", ""):
        raise BufferBlocked("PINTEREST_IDENTITY_UNVERIFIED")
    return entry


def prepare(payload: dict) -> dict:
    platform = str(payload.get("platform") or "").lower()
    if platform not in SERVICES:
        raise BufferBlocked("UNSUPPORTED_PLATFORM")
    uri = urllib.parse.urlparse(str(payload.get("media_url") or payload.get("video_url") or ""))
    if (uri.scheme != "https" or uri.hostname not in ("anthares.us", "www.anthares.us")
            or uri.username or uri.password or not uri.path.lower().endswith(".mp4")):
        raise BufferBlocked("MASTER_MP4_URL_INVALID")
    title = str(payload.get("title") or payload.get("video_title") or "").strip()
    if not title:
        raise BufferBlocked("TITLE_MISSING")
    if payload.get("duration_seconds") is not None:
        try:
            duration = float(payload["duration_seconds"])
        except (ValueError, TypeError):
            raise BufferBlocked("DURATION_INVALID")
        if not 30 <= duration <= 90:
            raise BufferBlocked("DURATION_OUT_OF_SHORT_RANGE")
    text = add_site_to_keywords(branded_title(title) + "\n" + str(payload.get("description") or "").strip())
    if len(text) > 2200:
        raise BufferBlocked("CAPTION_TOO_LONG_REQUIRES_EDITORIAL_TRUNCATION")
    return {"platform": platform, "media_url": uri.geturl(), "caption": text}


def schedule(payload: dict, *, token: str | None = None) -> dict:
    post = prepare(payload)
    if os.getenv("ANTHARES_SOCIAL_COMMIT", "") != "1":
        return {"status": "DRY_RUN", **post}
    platform = post["platform"]
    channel_id = str(os.getenv("BUFFER_" + platform.upper() + "_CHANNEL_ID") or "").strip()
    validate_channel(platform, channel_id, channels(token))
    # Queuing a Pinterest video or Instagram Reel may require additional
    # network-specific metadata in the Buffer API. Never silently switch to
    # notification publishing or another account when rejected.
    mutation = """mutation CortesBufferVideo {
      createPost(input: {
        text: CAPTION
        channelId: CHANNEL
        schedulingType: automatic
        mode: addToQueue
        assets: [{ video: { url: MEDIA } }]
      }) {
        ... on PostActionSuccess { post { id } }
        ... on MutationError { message }
      }
    }"""
    mutation = (mutation.replace("CAPTION", json.dumps(post["caption"], ensure_ascii=False))
               .replace("CHANNEL", json.dumps(channel_id))
               .replace("MEDIA", json.dumps(post["media_url"])))
    result = api(mutation, token).get("createPost") or {}
    identifier = str((result.get("post") or {}).get("id") or "")
    if not identifier:
        raise BufferBlocked("BUFFER_SCHEDULE_REJECTED_OR_UNCERTAIN")
    return {"status": "SCHEDULED_IN_BUFFER", "platform": platform,
            "remote_id": identifier, "confirmed_on_social_network": False}


def main() -> int:
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "dry-run"
        if mode == "list":
            data = channels()
            print(json.dumps([{k: c.get(k) for k in ("id","name","service","displayName","isQueuePaused","externalLink","type","isDisconnected","isLocked")} for c in data], ensure_ascii=False))
            return 0
        if mode not in ("dry-run", "schedule"):
            raise BufferBlocked("INVALID_MODE")
        payload = json.load(sys.stdin)
        if mode == "dry-run":
            os.environ["ANTHARES_SOCIAL_COMMIT"] = "0"
        result = schedule(payload)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except BufferBlocked as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
