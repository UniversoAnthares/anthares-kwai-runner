#!/usr/bin/env python3
"""KW-09: stage one canonical Kwai media file on Android, without publishing.

Runs only from the existing Kwai GitHub Actions OIDC publisher workflow.
The Neon lease is always released with its generation fence before exit.
Android receives public media coordinates through an authenticated MacroDroid
webhook. The phone-side macro MUST be stage-only: no Kwai share/post action.
"""
import hashlib
import json
import os
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from cortes_kwai_neon_cloud import QueueError, request


def validated_webhook():
    value = os.environ.get("KW09_MACRODROID_STAGE_WEBHOOK", "").strip()
    try:
        url = urlsplit(value)
    except ValueError as exc:
        raise QueueError("KW09_STAGE_WEBHOOK_INVALID") from exc
    if (url.scheme != "https" or url.hostname != "trigger.macrodroid.com"
            or url.username or url.password or url.port or url.query or url.fragment
            or not re.fullmatch(
                r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/kw09_stage_only",
                url.path)):
        raise QueueError("KW09_STAGE_WEBHOOK_UNCONFIGURED_OR_INVALID")
    return value


def source_content_sha256(source_url):
    """Hash MP4 bytes on hosted GitHub; never store media on the Windows PC."""
    h = hashlib.sha256()
    total = 0
    request = Request(source_url, headers={"User-Agent": "AntharesKW09HostedStage/1.0"})
    with urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise QueueError("KW09_STAGE_SOURCE_NOT_HTTP_200")
        while True:
            block = response.read(1024 * 512)
            if not block:
                break
            total += len(block)
            if total > 70 * 1024 * 1024:
                raise QueueError("KW09_STAGE_SOURCE_TOO_LARGE")
            h.update(block)
    if total < 2048:
        raise QueueError("KW09_STAGE_SOURCE_EMPTY")
    return h.hexdigest()


def stage_metadata(job):
    payload = job.get("payload") or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError) as exc:
            raise QueueError("KW09_STAGE_PAYLOAD_INVALID") from exc
    if not isinstance(payload, dict):
        raise QueueError("KW09_STAGE_PAYLOAD_INVALID")
    ident = str(job.get("id") or "")
    gen = job.get("lease_generation")
    url = str(payload.get("video_url") or "")
    sha = str(payload.get("content_sha256") or payload.get("media_content_sha256") or "").lower()
    parsed = urlsplit(url)
    checks = {
        "target": job.get("target_key") == "kwai:lucasrosalem",
        "account": payload.get("expected_account") == "lucasrosalem",
        "jobid": bool(re.fullmatch(r"kwai-cortes-[A-Za-z0-9._:-]{3,145}", ident)),
        "fence": isinstance(gen, int) and gen >= 1,
        "https": parsed.scheme == "https",
        "host": parsed.hostname in ("anthares.us", "www.anthares.us"),
        "authority": not (parsed.username or parsed.password or parsed.port or parsed.fragment),
        "filename": parsed.path.lower().endswith(".mp4"),
        "checksum": not sha or bool(re.fullmatch(r"[a-f0-9]{64}", sha)),
    }
    if not all(checks.values()):
        bad = "_".join(name for name, ok in checks.items() if not ok)
        raise QueueError("KW09_STAGE_IDENTITY_OR_MEDIA_INVALID_" + bad)
    # Neon media_sha256 may be the dispatch identity, not the MP4 content.
    # The Android must receive a real content checksum before fetching.
    if not sha:
        sha = source_content_sha256(url)
    return {
        "kw09_mode": "stage_only",
        "kw09_job_id": ident,
        "kw09_generation": str(gen),
        "kw09_video_url": url,
        "kw09_expected_sha256": sha,
        "kw09_expected_account": "lucasrosalem",
    }


def main():
    webhook = validated_webhook()
    receipt = None
    try:
        result = request("lease", {"lease_seconds":600})
        job = result.get("job")
        if job is None:
            print("KW09_ANDROID_STAGE_NO_ELIGIBLE_JOB")
            return 0
        receipt = {"id": str(job["id"]), "lease_generation": int(job["lease_generation"])}
        params = stage_metadata(job)
        # MacroDroid can consume a webhook query either as existing global
        # variables or as a dictionary. Support both import versions while the
        # Android receiver is being promoted, with identical validated values.
        params.update({f"kw09_stage_q({key})": value for key, value in tuple(params.items())})
        with urlopen(Request(webhook + "?" + urlencode(params), method="GET"),
                     timeout=20) as response:
            if response.status != 200:
                raise QueueError("KW09_ANDROID_WEBHOOK_DELIVERY_REJECTED")
        # HTTP 200 means the command was accepted, NOT that the phone fetched
        # the video or uploaded it to Kwai. Neither action is claimed here.
        print("KW09_ANDROID_STAGE_COMMAND_ACCEPTED")
        return 0
    finally:
        if receipt is not None:
            # Single-shot CAS. Do not retry ambiguous writes: unstarted leases
            # are automatically reclaimed after the 600-second fencing TTL.
            released = request("fail", receipt)
            if released.get("ok") is not True:
                raise QueueError("KW09_STAGE_LEASE_RELEASE_NOT_ACKNOWLEDGED")
            print("KW09_STAGE_NEON_FENCE_RELEASED")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (QueueError, ValueError, KeyError, OSError) as exc:
        print("KW09_STAGE_ERROR=" + str(exc).splitlines()[0][:130], file=sys.stderr)
        sys.exit(89)
