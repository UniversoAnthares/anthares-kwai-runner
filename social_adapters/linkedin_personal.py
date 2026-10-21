"""Official LinkedIn member-video posting adapter (separate from company page).

Uses LinkedIn OAuth w_member_social for the authenticated *member*, NOT the
Buffer company channel. Cloud-only; no credentials, no network call on dry-run.
Native Video API and Posts API. A publication is confirmed only by retrieving
its exact PUBLIC post and author. Never resubmit an uncertain post.

Authentication is deliberately fail-closed until the owner authorizes this
separate member scope and an immutable identity is pinned in Secrets Manager.
"""
from __future__ import annotations
import io
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from anthares_publisher.linkedin_editorial import linkedin_caption

BASE = "https://api.linkedin.com"
REST_VERSION = "202609"
MAX_MEDIA_BYTES = 160 * 1024 * 1024
TARGET = "linkedin:personal"


class PersonalAuthRequired(RuntimeError):
    pass


class PersonalUncertain(RuntimeError):
    pass


class PersonalQuota(RuntimeError):
    pass


def cloud_only():
    if (os.getenv("GITHUB_ACTIONS") != "true" or
        os.getenv("RUNNER_ENVIRONMENT") != "github-hosted" or
        os.getenv("RUNNER_OS") != "Linux"):
        raise PersonalAuthRequired("LINKEDIN_PERSONAL_CLOUD_REQUIRED")


def key():
    token = os.getenv("LINKEDIN_PERSONAL_ACCESS_TOKEN", "").strip()
    if not token:
        raise PersonalAuthRequired("LINKEDIN_PERSONAL_OAUTH_REQUIRED")
    return token


def api(method, url, body=None, *, token=None, response_headers=False):
    if not url.startswith(BASE + "/"):
        raise ValueError("LINKEDIN_EXTERNAL_API_URL_NOT_ALLOWED")
    headers = {
        "Authorization": "Bearer " + (token or key()),
        "Accept": "application/json",
        "Linkedin-Version": REST_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url, method=method, headers=headers,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            raw = r.read(2 * 1024 * 1024)
            data = json.loads(raw.decode("utf-8")) if raw.strip() else {}
            if response_headers:
                return data, dict(r.headers.items())
            return data
    except urllib.error.HTTPError as exc:
        if exc.code in (429, 403):
            raise PersonalQuota("LINKEDIN_ACCESS_OR_QUOTA_" + str(exc.code)) from None
        raise PersonalUncertain("LINKEDIN_API_HTTP_" + str(exc.code)) from None
    except (OSError, ValueError, TimeoutError):
        raise PersonalUncertain("LINKEDIN_API_RESPONSE_UNCERTAIN") from None


def person_identity():
    cloud_only()
    data = api("GET", BASE + "/v2/userinfo")
    sub = str(data.get("sub") or "")
    pinned = str(os.getenv("LINKEDIN_PERSONAL_SUB") or "").strip()
    if not pinned or not re.fullmatch(r"[A-Za-z0-9_-]{3,120}", pinned):
        raise PersonalAuthRequired("LINKEDIN_MEMBER_SUB_NOT_PINNED")
    if sub != pinned:
        raise PersonalAuthRequired("LINKEDIN_PERSONAL_ACCOUNT_MISMATCH")
    return "urn:li:person:" + pinned


def media_url(uri):
    target = urllib.parse.urlparse(str(uri))
    if (target.scheme != "https" or target.hostname not in ("anthares.us", "www.anthares.us")
            or target.username or target.password or target.port
            or not target.path.lower().endswith(".mp4")):
        raise ValueError("LINKEDIN_PERSONAL_INVALID_MASTER")
    return target.geturl()


class BlockRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("LINKEDIN_MEDIA_REDIRECT_BLOCKED")


def download_master(uri):
    uri = media_url(uri)
    opener = urllib.request.build_opener(BlockRedirect)
    with opener.open(urllib.request.Request(uri, headers={"Accept": "video/mp4"}), timeout=45) as response:
        claimed = response.headers.get("Content-Length", "")
        if claimed.isdigit() and int(claimed) > MAX_MEDIA_BYTES:
            raise ValueError("LINKEDIN_MEDIA_TOO_LARGE")
        with tempfile.TemporaryFile() as f:
            size = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_MEDIA_BYTES:
                    raise ValueError("LINKEDIN_MEDIA_TOO_LARGE")
                f.write(chunk)
            if size < 1024:
                raise ValueError("LINKEDIN_MEDIA_EMPTY")
            f.seek(0)
            return f.read()


def upload_video(payload, author):
    video = download_master(payload["media_url"])
    initialized = api("POST", BASE + "/rest/videos?action=initializeUpload",
                      {"initializeUploadRequest": {"owner": author,
                       "fileSizeBytes": len(video), "uploadCaptions": False,
                       "uploadThumbnail": False}}).get("value") or {}
    urn = str(initialized.get("video") or "")
    steps = initialized.get("uploadInstructions") or []
    if not re.fullmatch(r"urn:li:video:[A-Za-z0-9_-]+", urn) or not steps:
        raise PersonalUncertain("LINKEDIN_UPLOAD_INITIALIZATION_UNCERTAIN")
    uploaded = []
    for step in steps:
        link = urllib.parse.urlparse(str(step.get("uploadUrl") or ""))
        if (link.scheme != "https" or not (link.hostname or "").endswith(".linkedin.com")
                or link.username or link.password or link.port):
            raise PersonalUncertain("LINKEDIN_UPLOAD_TARGET_INVALID")
        a, b = int(step["firstByte"]), int(step["lastByte"])
        if a < 0 or b < a or b >= len(video) or b - a + 1 > 10 * 1024 * 1024:
            raise PersonalUncertain("LINKEDIN_UPLOAD_PART_RANGE_INVALID")
        req = urllib.request.Request(link.geturl(), data=video[a:b + 1],
                                     headers={"Content-Type": "application/octet-stream"},
                                     method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=70) as response:
                etag = str(response.headers.get("ETag") or "").strip(' "')
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            raise PersonalUncertain("LINKEDIN_VIDEO_UPLOAD_RESULT_UNCERTAIN") from None
        if not etag:
            raise PersonalUncertain("LINKEDIN_VIDEO_ETAG_MISSING")
        uploaded.append(etag)
    api("POST", BASE + "/rest/videos?action=finalizeUpload", {
        "finalizeUploadRequest": {
            "video": urn, "uploadToken": str(initialized.get("uploadToken") or ""),
            "uploadedPartIds": uploaded,
        }})
    return urn


def create_public_video(payload):
    cloud_only()
    if os.getenv("LINKEDIN_PERSONAL_COMMIT") != "1":
        return {"status": "DRY_RUN", "target_key": TARGET}
    author = person_identity()
    if payload.get("target_key") != TARGET:
        raise ValueError("LINKEDIN_PERSONAL_WRONG_DESTINATION")
    duration = float(payload.get("duration_seconds") or 0)
    if not 30 <= duration <= 90:
        raise ValueError("LINKEDIN_PERSONAL_INVALID_DURATION")
    video_urn = upload_video(payload, author)
    caption = linkedin_caption(payload["title"], str(payload.get("description") or ""))
    content = {
        "author": author,
        "commentary": caption,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"media": {"title": str(payload["title"])[:120],
                              "id": video_urn}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    response, headers = api("POST", BASE + "/rest/posts", content, response_headers=True)
    post = str(headers.get("x-restli-id") or headers.get("X-RestLi-Id") or
               response.get("id") or "")
    if not re.fullmatch(r"urn:li:(?:ugcPost|share):[0-9]+", post):
        raise PersonalUncertain("LINKEDIN_PERSONAL_POST_ID_UNKNOWN")
    # The record stays uncertain if LinkedIn is still processing video.
    verification = api("GET", BASE + "/rest/posts/" + urllib.parse.quote(post, safe=""))
    if (verification.get("id") != post or verification.get("author") != author or
        verification.get("visibility") != "PUBLIC" or
        verification.get("lifecycleState") != "PUBLISHED"):
        return {"status": "UNCERTAIN", "target_key": TARGET, "remote_id": post}
    external_url = "https://www.linkedin.com/feed/update/" + post
    return {"status": "CONFIRMED", "target_key": TARGET, "remote_id": post,
            "external_link": external_url}
