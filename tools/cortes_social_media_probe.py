"""Read-only HTTPS source-MP4 availability guard for CORTES cloud publishers.

A 404/410 is a definite missing file and may be set aside for repair before
remote publication starts. All other failures are transient and retryable.
Never log media responses, secrets, video bytes or personal identifiers.
"""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

ORIGINS = {"anthares.us", "www.anthares.us"}


def available(url: str, opener=urllib.request.urlopen) -> bool:
    uri = urllib.parse.urlparse(str(url or ""))
    if uri.scheme != "https" or uri.hostname not in ORIGINS or uri.username or uri.password:
        raise ValueError("SOURCE_MEDIA_ORIGIN_DENIED")
    req = urllib.request.Request(url, method="GET", headers={
        "Range": "bytes=0-7", "Accept": "video/mp4",
        "User-Agent": "AntharesCortesMediaPreflight/1.0"})
    try:
        with opener(req, timeout=20) as resp:
            if getattr(resp, "status", 0) not in (200, 206):
                raise RuntimeError("SOURCE_MEDIA_UNEXPECTED_HTTP")
            ctype = str(resp.headers.get("Content-Type") or "").lower()
            if not ctype.startswith("video/mp4") and not ctype.startswith("application/octet-stream"):
                raise RuntimeError("SOURCE_MEDIA_WRONG_TYPE")
            if len(resp.read(8)) < 8:
                raise RuntimeError("SOURCE_MEDIA_TOO_SHORT")
        return True
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return False
        raise RuntimeError("SOURCE_MEDIA_TEMPORARY_HTTP") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("SOURCE_MEDIA_TEMPORARY_UNAVAILABLE") from None
