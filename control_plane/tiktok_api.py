"""Minimal official TikTok Content Posting API adapter.

Secrets are accepted only as call arguments and are never returned, persisted or
included in raised error messages. The adapter deliberately surfaces authorization
and audit restrictions instead of attempting to bypass them.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable
from urllib import error, request

BASE_URL = "https://open.tiktokapis.com"
CREATOR_INFO_PATH = "/v2/post/publish/creator_info/query/"
DIRECT_POST_PATH = "/v2/post/publish/video/init/"
STATUS_PATH = "/v2/post/publish/status/fetch/"


@dataclass(frozen=True)
class TikTokApiError(RuntimeError):
    code: str
    message: str = ""
    log_id: str = ""
    http_status: int | None = None

    def __str__(self) -> str:
        parts = [self.code or "tiktok_api_error"]
        if self.http_status is not None:
            parts.append(f"http={self.http_status}")
        if self.log_id:
            parts.append(f"log_id={self.log_id}")
        return ":".join(parts)


def classify_error(code: str) -> str:
    value = (code or "").strip().lower()
    if value == "unaudited_client_can_only_post_to_private_accounts":
        return "app_audit_required_for_public_posting"
    if value in {"scope_not_authorized", "access_token_invalid", "access_token_expired"}:
        return "oauth_authorization_required"
    if value in {"url_ownership_unverified", "url_ownership_verification_failed"}:
        return "video_domain_verification_required"
    if value in {"spam_risk_too_many_posts", "spam_risk_user_banned_from_posting"}:
        return "platform_posting_restriction"
    return "api_error"


def _default_transport(path: str, payload: dict, access_token: str) -> tuple[int, dict]:
    if not access_token or not access_token.strip():
        raise ValueError("access_token_required")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = request.Request(
        BASE_URL + path,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": {"code": "http_error", "message": ""}}
        return exc.code, parsed


def _post(
    path: str,
    payload: dict,
    access_token: str,
    *,
    transport: Callable[[str, dict, str], tuple[int, dict]] = _default_transport,
) -> dict:
    status, response = transport(path, payload, access_token)
    if not isinstance(response, dict):
        raise TikTokApiError("invalid_response", http_status=status)
    err = response.get("error") or {}
    code = str(err.get("code") or "")
    if status < 200 or status >= 300 or code not in {"", "ok"}:
        raise TikTokApiError(
            code or "http_error",
            message=str(err.get("message") or ""),
            log_id=str(err.get("log_id") or ""),
            http_status=status,
        )
    data = response.get("data")
    if not isinstance(data, dict):
        raise TikTokApiError("missing_data", http_status=status)
    return data


def query_creator_info(access_token: str, *, transport=_default_transport) -> dict:
    data = _post(CREATOR_INFO_PATH, {}, access_token, transport=transport)
    return {
        "creator_username": data.get("creator_username"),
        "creator_nickname": data.get("creator_nickname"),
        "privacy_level_options": list(data.get("privacy_level_options") or []),
        "comment_disabled": bool(data.get("comment_disabled", False)),
        "duet_disabled": bool(data.get("duet_disabled", False)),
        "stitch_disabled": bool(data.get("stitch_disabled", False)),
        "max_video_post_duration_sec": data.get("max_video_post_duration_sec"),
    }


def init_direct_post_from_url(
    access_token: str,
    *,
    video_url: str,
    title: str,
    privacy_level: str,
    disable_comment: bool = False,
    disable_duet: bool = False,
    disable_stitch: bool = False,
    video_cover_timestamp_ms: int = 1000,
    transport=_default_transport,
) -> str:
    if not video_url.startswith("https://"):
        raise ValueError("https_video_url_required")
    if not privacy_level:
        raise ValueError("privacy_level_required")
    payload = {
        "post_info": {
            "title": title,
            "privacy_level": privacy_level,
            "disable_comment": bool(disable_comment),
            "disable_duet": bool(disable_duet),
            "disable_stitch": bool(disable_stitch),
            "video_cover_timestamp_ms": int(video_cover_timestamp_ms),
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": video_url,
        },
    }
    data = _post(DIRECT_POST_PATH, payload, access_token, transport=transport)
    publish_id = str(data.get("publish_id") or "").strip()
    if not publish_id:
        raise TikTokApiError("publish_id_missing")
    return publish_id


def fetch_publish_status(access_token: str, publish_id: str, *, transport=_default_transport) -> dict:
    if not publish_id or not publish_id.strip():
        raise ValueError("publish_id_required")
    data = _post(STATUS_PATH, {"publish_id": publish_id}, access_token, transport=transport)
    return {
        "status": data.get("status"),
        "fail_reason": data.get("fail_reason"),
        "publicaly_available_post_id": list(data.get("publicaly_available_post_id") or []),
        "uploaded_bytes": data.get("uploaded_bytes"),
    }


def preflight(access_token: str, expected_username: str, *, transport=_default_transport) -> dict:
    info = query_creator_info(access_token, transport=transport)
    actual = str(info.get("creator_username") or "").lstrip("@").lower()
    expected = str(expected_username or "").lstrip("@").lower()
    identity_verified = bool(expected and actual == expected)
    return {
        "identity_verified": identity_verified,
        "creator_username": info.get("creator_username"),
        "privacy_level_options": info.get("privacy_level_options", []),
        "max_video_post_duration_sec": info.get("max_video_post_duration_sec"),
        "token_exported": False,
    }
