"""Fail-closed publication evidence and media policy for Anthares X.

This module has no posting credentials or side effects. Production code must
never equate an issue closure, upload, scheduled job or attempted click with a
verified X video post.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

ACCOUNT = "lucasyahn"
POST_RE = re.compile(r"https://(?:www\.)?(?:x\.com|twitter\.com)/lucasyahn/status/([0-9]{10,25})(?:[/?#][^\s]*)?", re.I)
MIN_SECONDS, MAX_SECONDS = 300.0, 840.0


def verified_post_url(text: str, account: str = ACCOUNT) -> str | None:
    if account != ACCOUNT:
        return None
    match = POST_RE.search(text or "")
    if not match:
        return None
    return "https://x.com/lucasyahn/status/" + match.group(1)


def _issue_payload(body):
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", body or "", re.S | re.I)
    if not match:
        return {}
    try:
        result = json.loads(match.group(1))
        return result if isinstance(result, dict) else {}
    except (ValueError, TypeError):
        return {}


def confirmed_today(issue, comments, local_day, tz):
    """Require account-bound video proof in a confirmation comment from today."""
    if not str(issue.get("title", "")).startswith("[X-PUBLISH]"):
        return set()
    p = _issue_payload(issue.get("body"))
    if p.get("test_fixture") or p.get("platform") != "x" or p.get("account") != ACCOUNT:
        return set()
    result = set()
    for c in comments:
        body = str(c.get("body") or "")
        if ((c.get("user") or {}).get("login") != "github-actions[bot]"
                or "X_VIDEO_CONFIRMED_V1" not in body):
            continue
        try:
            line = next(line for line in body.splitlines() if line.startswith("{"))
            proof = json.loads(line)
        except (StopIteration, ValueError):
            continue
        if (proof.get("kind") != "X_VIDEO_CONFIRMED_V1"
                or proof.get("account") != ACCOUNT
                or proof.get("video_verified") is not True):
            continue
        url = verified_post_url(str(proof.get("post_url") or ""))
        if not url:
            continue
        ts = c.get("created_at")
        try:
            stamped = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
        except (ValueError, AttributeError):
            continue
        if stamped.date() == local_day:
            result.add(url)
    return result


def gate(issues, comments_by_number, now, target=10, max_inflight=2):
    """Stale tasks need reconciliation and QA, without blocking newer source jobs."""
    local_day = now.date()
    confirmed = set()
    recent_pending = []
    stale = []
    windows_by_source = {}
    for issue in issues:
        if issue.get("pull_request"):
            continue
        title = str(issue.get("title") or "")
        if not (title.startswith("[X-PUBLISH]") or title.startswith("[X-MICROCUT]")):
            continue
        number = int(issue["number"])
        payload = _issue_payload(issue.get("body"))
        if payload.get("test_fixture"):
            continue
        source = payload.get("source_id") or (payload.get("source") or {}).get("video_id")
        if source and (title.startswith("[X-MICROCUT]") or title.startswith("[X-PUBLISH]")):
            try:
                start = int(payload.get("scan_start"))
                if start >= 0:
                    windows_by_source.setdefault(str(source), set()).add(start)
            except (ValueError, TypeError):
                pass
        confirmed |= confirmed_today(issue, comments_by_number.get(number, []), local_day, now.tzinfo)
        if issue.get("state") != "open":
            continue
        try:
            created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")).astimezone(now.tzinfo)
        except (ValueError, KeyError, AttributeError):
            stale.append(number)
            continue
        if now - created > timedelta(hours=3):
            stale.append(number)
        else:
            recent_pending.append(number)
    capacity = target - len(confirmed) - len(recent_pending)
    return {
        "confirmed": len(confirmed),
        "inflight": len(recent_pending),
        "stale_issue_numbers": stale,
        "source_windows": {source: sorted(windows) for source, windows in windows_by_source.items()},
        "due": capacity > 0 and len(recent_pending) < max_inflight,
        "capacity": max(0, capacity),
    }


def validate_video(path: str) -> dict:
    """Validate actual encoded media, before any irreversible action on X."""
    info = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,width,height:format=duration", "-of", "json", path
    ], text=True, capture_output=True, check=True, timeout=30)
    data = json.loads(info.stdout)
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    if not streams:
        raise ValueError("X_MEDIA_VIDEO_MISSING")
    width, height = int(streams[0].get("width") or 0), int(streams[0].get("height") or 0)
    duration = float((data.get("format") or {}).get("duration") or 0)
    if width <= height or height < 240 or abs(width / height - 16 / 9) > .04:
        raise ValueError("X_MEDIA_REQUIRES_16_9_HORIZONTAL")
    if not MIN_SECONDS <= duration <= MAX_SECONDS:
        raise ValueError("X_MEDIA_REQUIRES_5_TO_14_MINUTES")
    return {"width": width, "height": height, "duration": duration}


if __name__ == "__main__":
    raise SystemExit("Import this guard from a publisher; do not publish from this module.")
