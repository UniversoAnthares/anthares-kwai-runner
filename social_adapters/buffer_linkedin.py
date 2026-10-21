#!/usr/bin/env python3
"""Buffer's supported GraphQL API for CORTES native LinkedIn video scheduling.

This CLI deliberately distinguishes SCHEDULED_IN_BUFFER from CONFIRMED_ON_LINKEDIN.
A separately reconciled remote publication URL is required before a Neon job
can be marked confirmed. A Buffer scheduling response is NEVER final evidence.
No browser scraping, cookies, account-token extraction or automatic retries.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from anthares_publisher.editorial import branded_title, add_site_to_keywords

GRAPHQL_URL = "https://api.buffer.com"
LINKEDIN_PAGE_ID = "145345334"
LINKEDIN_PAGE_NAME = "Universo Anthares"
SUFFIX = " ● Universo Anthares"
MAX_CAPTION = 3000


class NotConfigured(RuntimeError):
    pass


class ProviderUncertain(RuntimeError):
    pass


class ProviderRejected(RuntimeError):
    pass


def _env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise NotConfigured(name)
    return value


def _request(query: str, *, token: str | None = None) -> dict:
    """One request only. Do not retry writes automatically after transport errors."""
    key = token or _env("BUFFER_API_KEY")
    body = json.dumps({"query": query}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL, method="POST", data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "AntharesCortesBuffer/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise NotConfigured("BUFFER_API_KEY_OR_PERMISSIONS") from exc
        raise ProviderUncertain("buffer_http_" + str(exc.code)) from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise ProviderUncertain("buffer_transport_or_json_failure") from exc
    if not isinstance(result, dict):
        raise ProviderUncertain("buffer_json_invalid")
    errors = result.get("errors") or []
    if errors:
        # Only sanitized error codes are used, not remote error strings.
        raise ProviderRejected("buffer_graphql_errors")
    return result.get("data") or {}


def _organizations() -> list[dict]:
    doc = "query CortesOrgs { account { organizations { id name } } }"
    account = _request(doc).get("account") or {}
    return account.get("organizations") or []


def _channels(organization_id: str) -> list[dict]:
    org = json.dumps(organization_id)
    query = f"""query CortesChannels {{
        channels(input: {{organizationId: {org}}}) {{
          id name displayName service externalLink isQueuePaused
        }}
    }}"""
    return _request(query).get("channels") or []


def resolve_linkedin_channel() -> str:
    """Validate an operator-pinned Buffer ID against the company Page, not a profile."""
    expected_id = _env("BUFFER_LINKEDIN_CHANNEL_ID")
    organizations = _organizations()
    if not organizations:
        raise NotConfigured("BUFFER_ORGANIZATION_HAS_NO_CHANNELS")
    matches = []
    for org in organizations:
        if not org.get("id"):
            continue
        for channel in _channels(str(org["id"])):
            if str(channel.get("id") or "") != expected_id:
                continue
            if str(channel.get("service") or "").lower() != "linkedin":
                raise ProviderRejected("buffer_channel_is_not_linkedin")
            if channel.get("isQueuePaused"):
                raise ProviderRejected("buffer_linkedin_queue_paused")
            display = str(channel.get("displayName") or channel.get("name") or "").strip()
            link = str(channel.get("externalLink") or "").strip()
            if display.lower() != LINKEDIN_PAGE_NAME.lower():
                raise ProviderRejected("buffer_wrong_linkedin_page_name")
            if link:
                parsed = urllib.parse.urlparse(link if "://" in link else "https://" + link)
                if (parsed.hostname or "").lower() not in ("linkedin.com", "www.linkedin.com"):
                    raise ProviderRejected("buffer_linkedin_external_host_invalid")
                allowed = {"/company/" + LINKEDIN_PAGE_ID,
                           "/company/universo-anthares",
                           "/company/universo-anthares/"}
                if parsed.path.rstrip("/") not in {x.rstrip("/") for x in allowed}:
                    raise ProviderRejected("buffer_wrong_linkedin_page_url")
            matches.append(channel)
    if len(matches) != 1:
        raise NotConfigured("BUFFER_LINKEDIN_CHANNEL_NOT_VERIFIED")
    return expected_id


def video_caption(title: str, description: str = "") -> str:
    headline = branded_title(title)
    body = str(description or "").strip()
    if body.startswith(str(title).strip()):
        body = body[len(str(title).strip()):].strip()
    # URL and hashtags belong in description, not inside the brand suffix.
    text = add_site_to_keywords(headline + ("\n" + body if body else ""))
    if len(text) > MAX_CAPTION:
        raise ValueError("buffer_caption_too_long")
    return text


def _verify_media_url(value: str) -> str:
    parsed = urllib.parse.urlparse(str(value).strip())
    if parsed.scheme != "https" or parsed.hostname not in ("anthares.us", "www.anthares.us"):
        raise ValueError("buffer_media_must_be_public_anthares_https")
    if parsed.username or parsed.password or not parsed.path.lower().endswith(".mp4"):
        raise ValueError("buffer_media_invalid_url")
    return parsed.geturl()


def plan(payload: dict) -> dict:
    if str(payload.get("platform") or "linkedin").lower() != "linkedin":
        raise ValueError("buffer_adapter_only_linkedin")
    if str(payload.get("account_id") or "primary") != "primary":
        raise ValueError("buffer_account_not_verified")
    if payload.get("duration_class") and payload["duration_class"] != "short":
        raise ValueError("buffer_only_short_clips")
    if payload.get("duration_seconds") is not None:
        if not 30 <= float(payload["duration_seconds"]) <= 90:
            raise ValueError("buffer_clip_duration_invalid")
    media_url = _verify_media_url(payload.get("media_url") or payload.get("video_url") or "")
    title = str(payload.get("title") or payload.get("video_title") or "").strip()
    if not title:
        raise ValueError("buffer_title_required")
    return {
        "platform": "linkedin",
        "account_id": "primary",
        "media_url": media_url,
        "caption": video_caption(title, str(payload.get("description") or "")),
    }


def schedule_video(payload: dict) -> dict:
    prepared = plan(payload)
    if os.getenv("ANTHARES_SOCIAL_COMMIT") != "1":
        return {"status": "DRY_RUN", "caption": prepared["caption"],
                "media_url": prepared["media_url"]}
    channel_id = resolve_linkedin_channel()
    query = f"""mutation CortesBufferSchedule {{
      createPost(input: {{
        text: {json.dumps(prepared["caption"], ensure_ascii=False)}
        channelId: {json.dumps(channel_id)}
        schedulingType: automatic
        mode: addToQueue
        assets: [{{ video: {{ url: {json.dumps(prepared["media_url"])} }} }}]
      }}) {{
        ... on PostActionSuccess {{ post {{ id text dueAt }} }}
        ... on MutationError {{ message }}
      }}
    }}"""
    # No retry and no automatic Neon confirmation after submission.
    response = _request(query).get("createPost") or {}
    if response.get("post", {}).get("id"):
        post = response["post"]
        return {
            "status": "SCHEDULED_IN_BUFFER",
            "remote_id": str(post["id"]),
            "due_at": str(post.get("dueAt") or ""),
            "confirmation_evidence": None,
            "requires_linkedin_readback": True,
        }
    raise ProviderRejected("buffer_create_post_rejected_or_missing_id")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = schedule_video(payload)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except NotConfigured as exc:
        print(json.dumps({"status": "AUTH_OR_CHANNEL_REQUIRED", "missing": str(exc)}))
        return 3
    except (ProviderUncertain, ProviderRejected) as exc:
        print(json.dumps({"status": "UNCERTAIN_OR_REJECTED", "reason": str(exc)}))
        return 4
    except (ValueError, TypeError, KeyError):
        print('{"status":"INVALID_JOB"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
