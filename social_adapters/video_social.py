#!/usr/bin/env python3
"""Fail-closed Pinterest video Pins and LinkedIn native video posts.

Run from an already fenced, account-scoped queue consumer. Production posts
require ANTHARES_SOCIAL_COMMIT=1; this module never claims/acks a queue job.
No implicit retry is allowed once a media upload or post creation has begun.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from anthares_publisher.editorial import prepare_publication_metadata


class ConfigRequired(RuntimeError):
    pass


class PlatformLimit(RuntimeError):
    pass


class PublishUncertain(RuntimeError):
    pass


def env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigRequired(name)
    return value


def _request(url, *, token=None, method="GET", body=None, headers=None, timeout=60):
    hdr = {"Accept": "application/json", "User-Agent": "anthares-publisher/1"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    if body is not None and not isinstance(body, bytes):
        body = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        hdr["Content-Type"] = "application/json"
    hdr.update(headers or {})
    request = urllib.request.Request(url, data=body, headers=hdr, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            data = json.loads(raw.decode("utf-8")) if raw else {}
            return data, dict(response.headers)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise PlatformLimit("BLOCKED_PLATFORM_LIMIT HTTP_429") from exc
        # Avoid leaking token-bearing URLs or server-side response data into logs.
        raise PublishUncertain("REMOTE_HTTP_" + str(exc.code)) from exc


@contextmanager
def media_file(payload):
    file_path = str(payload.get("media_path") or "").strip()
    if file_path:
        path = pathlib.Path(file_path).resolve(strict=True)
        if path.suffix.lower() not in (".mp4", ".mov", ".m4v"):
            raise ValueError("unsupported_video_format")
        if path.stat().st_size <= 0:
            raise ValueError("video_empty")
        yield path
        return
    url = str(payload.get("media_url") or "").strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ConfigRequired("https_media_url_or_media_path")
    with tempfile.TemporaryDirectory(prefix="anthares-social-") as folder:
        path = pathlib.Path(folder) / "master.mp4"
        try:
            with urllib.request.urlopen(url, timeout=45) as response, open(path, "wb") as target:
                while True:
                    part = response.read(1024 * 1024)
                    if not part:
                        break
                    if target.tell() + len(part) > 500_000_000:
                        raise ValueError("video_exceeds_500MB")
                    target.write(part)
        except urllib.error.URLError as exc:
            raise PublishUncertain("media_download_failed") from exc
        if path.stat().st_size <= 0:
            raise ValueError("video_empty")
        yield path


def pinterest(payload, publish=False):
    account = str(payload.get("account_id") or "primary").strip().lower()
    key = "pinterest:" + account
    token = env("PINTEREST_ACCESS_TOKEN")
    board = env("PINTEREST_BOARD_ID")
    cover = str(payload.get("cover_image_url") or os.getenv("PINTEREST_COVER_IMAGE_URL") or "").strip()
    if not cover.startswith("https://"):
        raise ConfigRequired("PINTEREST_COVER_IMAGE_URL")
    if not (payload.get("media_path") or payload.get("media_url")):
        raise ConfigRequired("media_path_or_media_url")
    metadata = prepare_publication_metadata(payload, title_limit=100)
    if not publish:
        return {"status": "READY", "destination_key": key, "title": metadata["title"]}
    base = "https://api.pinterest.com/v5"
    with media_file(payload) as path:
        init, _ = _request(base + "/media", token=token, method="POST", body={"media_type": "video"})
        media_id = str(init.get("media_id") or "")
        upload_url = str(init.get("upload_url") or "")
        params = init.get("upload_parameters") or {}
        host = (urllib.parse.urlparse(upload_url).hostname or "").lower()
        if not media_id or not host.endswith("amazonaws.com") or not isinstance(params, dict):
            raise PublishUncertain("pinterest_media_registration_incomplete")
        # Presigned S3 multipart upload, using exactly the server-provided fields.
        args = ["curl", "--fail", "--silent", "--show-error", "--max-time", "600", "-X", "POST"]
        for name, value in params.items():
            args.extend(["--form-string", str(name) + "=" + str(value)])
        args.extend(["-F", "file=@" + str(path), upload_url])
        try:
            subprocess.run(args, check=True, capture_output=True, timeout=630)
        except (subprocess.SubprocessError, OSError) as exc:
            raise PublishUncertain("pinterest_media_upload_uncertain") from exc
        for _ in range(30):
            state, _ = _request(base + "/media/" + urllib.parse.quote(media_id, safe=""), token=token)
            status = str(state.get("status") or "").lower()
            if status == "succeeded":
                break
            if status == "failed":
                raise PublishUncertain("pinterest_media_processing_failed")
            time.sleep(10)
        else:
            raise PublishUncertain("pinterest_media_processing_timeout")
        pin, _ = _request(base + "/pins", token=token, method="POST", body={
            "title": metadata["title"],
            "description": metadata["description"],
            "link": "https://www.anthares.us",
            "board_id": board,
            "media_source": {"source_type": "video_id", "cover_image_url": cover, "media_id": media_id},
        })
    pin_id = str(pin.get("id") or "")
    if not pin_id:
        raise PublishUncertain("pinterest_post_id_missing")
    verified, _ = _request(base + "/pins/" + urllib.parse.quote(pin_id, safe=""), token=token)
    if str(verified.get("id") or "") != pin_id:
        raise PublishUncertain("pinterest_readback_unverified")
    return {"status": "CONFIRMED", "destination_key": key, "remote_id": pin_id,
            "confirmation_evidence": {"verified_id": pin_id, "permalink": "https://www.pinterest.com/pin/" + pin_id + "/"}}


def _linkedin_headers():
    return {"Linkedin-Version": os.getenv("LINKEDIN_API_VERSION", "202606"),
            "X-Restli-Protocol-Version": "2.0.0"}


def linkedin(payload, publish=False):
    account = str(payload.get("account_id") or "primary").strip().lower()
    key = "linkedin:" + account
    token = env("LINKEDIN_ACCESS_TOKEN")
    owner = env("LINKEDIN_AUTHOR_URN")
    if not owner.startswith(("urn:li:person:", "urn:li:organization:")):
        raise ConfigRequired("LINKEDIN_AUTHOR_URN")
    if not (payload.get("media_path") or payload.get("media_url")):
        raise ConfigRequired("media_path_or_media_url")
    metadata = prepare_publication_metadata(payload, title_limit=200)
    if not publish:
        return {"status": "READY", "destination_key": key, "title": metadata["title"]}
    headers = _linkedin_headers()
    base = "https://api.linkedin.com/rest"
    with media_file(payload) as path:
        size = path.stat().st_size
        if size > 500_000_000 or size < 75_000:
            raise ValueError("linkedin_video_size_out_of_bounds")
        init, _ = _request(base + "/videos?action=initializeUpload", token=token, method="POST",
            headers=headers, body={"initializeUploadRequest": {
                "owner": owner, "fileSizeBytes": size,
                "uploadCaptions": False, "uploadThumbnail": False}})
        value = init.get("value") or {}
        video = str(value.get("video") or "")
        instructions = value.get("uploadInstructions") or []
        if not video or not instructions:
            raise PublishUncertain("linkedin_initialize_upload_incomplete")
        part_ids = []
        with path.open("rb") as fh:
            for part in instructions:
                first = int(part["firstByte"])
                last = int(part["lastByte"])
                url = str(part["uploadUrl"])
                if (urllib.parse.urlparse(url).hostname or "").lower() not in ("www.linkedin.com", "api.linkedin.com"):
                    raise PublishUncertain("linkedin_upload_host_invalid")
                if first < 0 or last < first or last >= size:
                    raise PublishUncertain("linkedin_upload_range_invalid")
                fh.seek(first)
                chunk = fh.read(last-first+1)
                _, response_headers = _request(url, method="PUT", body=chunk,
                    headers={"Content-Type": "application/octet-stream"}, timeout=180)
                etag = next((v for k,v in response_headers.items() if k.lower() == "etag"), "")
                if not etag:
                    raise PublishUncertain("linkedin_part_etag_missing")
                part_ids.append(etag.strip('"'))
        _request(base + "/videos?action=finalizeUpload", token=token, method="POST",
            headers=headers, body={"finalizeUploadRequest": {
                "video": video, "uploadToken": value.get("uploadToken") or "",
                "uploadedPartIds": part_ids}})
        # Video must finish processing before it can be referenced in a post.
        video_url = base + "/videos/" + urllib.parse.quote(video, safe="")
        for _ in range(30):
            resource, _ = _request(video_url, token=token, headers=headers)
            status = str(resource.get("status") or "").upper()
            if status == "AVAILABLE":
                break
            if status in ("PROCESSING_FAILED", "FAILED"):
                raise PublishUncertain("linkedin_media_processing_failed")
            time.sleep(10)
        else:
            raise PublishUncertain("linkedin_media_processing_timeout")
        post, post_headers = _request(base + "/posts", token=token, method="POST", headers=headers,
            body={"author": owner, "commentary": metadata["description"],
                  "visibility": "PUBLIC",
                  "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                                   "thirdPartyDistributionChannels": []},
                  "content": {"media": {"title": metadata["title"], "id": video}},
                  "lifecycleState": "PUBLISHED",
                  "isReshareDisabledByAuthor": False})
    remote_id = next((v for k,v in post_headers.items() if k.lower() == "x-restli-id"), "")
    if not remote_id:
        raise PublishUncertain("linkedin_post_id_missing")
    verified, _ = _request(base + "/posts/" + urllib.parse.quote(remote_id, safe=""), token=token, headers=headers)
    if str(verified.get("id") or "") != remote_id:
        raise PublishUncertain("linkedin_post_readback_unverified")
    return {"status": "CONFIRMED", "destination_key": key, "remote_id": remote_id,
            "confirmation_evidence": {"verified_id": remote_id, "video": video}}


def main():
    try:
        payload = json.load(sys.stdin)
        platform = str(payload.get("platform") or "").strip().lower()
        if platform not in ("pinterest", "linkedin"):
            raise ValueError("unsupported_platform")
        key = platform + ":" + str(payload.get("account_id") or "primary").strip().lower()
        fn = {"pinterest": pinterest, "linkedin": linkedin}[platform]
        out = fn(payload, publish=os.getenv("ANTHARES_SOCIAL_COMMIT") == "1")
    except ConfigRequired as exc:
        out = {"status": "AUTH_OR_CONFIG_REQUIRED", "destination_key": locals().get("key", ""), "missing": str(exc)}
    except PlatformLimit:
        out = {"status": "BLOCKED_PLATFORM_LIMIT", "destination_key": locals().get("key", "")}
    except PublishUncertain as exc:
        out = {"status": "UNCERTAIN", "destination_key": locals().get("key", ""), "reason": str(exc)}
    print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
