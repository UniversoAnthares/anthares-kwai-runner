"""TinyFish-first supplementary reads of public URLs.

This reader never confirms media publication. Author/content/media proof remains
with the platform-specific verifier, which runs independently on every attempt.
No secrets, cookies, private URLs, or response bodies are logged.
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable


def _host(url: str) -> str:
    p = urllib.parse.urlsplit(str(url))
    hostname = (p.hostname or "").lower().rstrip(".")
    if p.scheme != "https" or not hostname or p.username or p.password:
        raise ValueError("url_not_public_https")
    if hostname in ("localhost",) or hostname.endswith((".localhost", ".local", ".internal")):
        raise ValueError("local_url_not_allowed")
    try:
        ipaddress.ip_address(hostname)
        raise ValueError("ip_literal_not_allowed")
    except ValueError as exc:
        if str(exc) == "ip_literal_not_allowed":
            raise
    if not re.fullmatch(r"[a-z0-9.-]+", hostname) or "." not in hostname:
        raise ValueError("invalid_hostname")
    return hostname


def _safe_url(url: str) -> str:
    """Remove tokens and tracking query parameters from observations."""
    split = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((split.scheme, split.netloc, split.path, "", ""))


def _allowed_redirect(start_host: str, final_url: str, allowed_hosts: Iterable[str]) -> bool:
    return _host(final_url) in (set(allowed_hosts) or {start_host})


def _normalize(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    value = unicodedata.normalize("NFKD", value).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        ch for ch in value if not unicodedata.combining(ch)
    )))


def _result(url: str, provider: str, ok: bool, reason: str, text: str = "",
            fragments: Iterable[str] = ()) -> dict:
    normalized = _normalize(text)
    checked = {frag: (_normalize(frag) in normalized) for frag in fragments if frag}
    return {
        "url": _safe_url(url), "provider": provider, "ok": bool(ok),
        "reason": reason, "length": len(text),
        "markers_matched": checked,
    }


def probe_public_page(
    url: str, fragments: Iterable[str] = (), *, fallback: bool = False,
    timeout: int = 12, allowed_hosts: Iterable[str] | None = None,
) -> dict:
    """TinyFish first, direct HTTPS fallback optionally.

    Success means that a public HTTP document was readable. Marker matches
    provide hints only, never authoritative proof of a published media item.
    """
    url = str(url)
    host = _host(url)
    allowed = set(allowed_hosts or ())
    if allowed and host not in allowed:
        raise ValueError("host_not_allowlisted")
    fragments = tuple(str(f) for f in fragments if f)
    key = (os.environ.get("TINYFISH_API_KEY") or "").strip()
    failure = "tinyfish_key_unconfigured"
    if key:
        payload = json.dumps({
            "urls": [url], "format": "html", "ttl": 0
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.fetch.tinyfish.ai",
            data=payload, method="POST",
            headers={"X-API-Key": key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as reply:
                body = reply.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise ValueError("tinyfish_response_too_large")
                doc = json.loads(body)
            rows = doc.get("results", []) if isinstance(doc, dict) else []
            if rows and not doc.get("errors") and isinstance(rows[0], dict):
                row = rows[0]
                final_url = row.get("final_url") or row.get("url") or url
                if not _allowed_redirect(host, final_url, allowed):
                    raise ValueError("tinyfish_redirect_host_mismatch")
                content = row.get("text") or ""
                if isinstance(content, str) and len(_normalize(content)) >= 60:
                    return _result(url, "tinyfish_fetch", True, "readable", content, fragments)
            failure = "tinyfish_empty_or_source_failed"
        except (ValueError, OSError, TimeoutError, urllib.error.URLError) as exc:
            failure = type(exc).__name__.lower()
    if not fallback:
        return _result(url, "tinyfish_fetch", False, failure, fragments=fragments)

    request = urllib.request.Request(
        url, headers={"User-Agent": "AntharesPublicProof/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            final_url = reply.geturl()
            if not _allowed_redirect(host, final_url, allowed):
                raise ValueError("fallback_redirect_host_mismatch")
            data = reply.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise ValueError("fallback_body_too_large")
            content = data.decode("utf-8", errors="replace")
            return _result(url, "https_fallback", bool(content.strip()), "readable", content, fragments)
    except (ValueError, OSError, TimeoutError, urllib.error.URLError) as exc:
        return _result(url, "https_fallback", False, type(exc).__name__.lower(), fragments=fragments)


def supplementary_public_observation(url: str, fragments: Iterable[str] = (), *, allowed_hosts: Iterable[str]) -> dict:
    """Best-effort public read, never authoritative publication evidence."""
    try:
        return probe_public_page(url, fragments, fallback=True, timeout=5,
                                 allowed_hosts=tuple(allowed_hosts))
    except Exception:
        return {"provider": "public_read", "ok": False,
                "reason": "supplementary_read_unavailable"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--marker", action="append", default=[])
    parser.add_argument("--fallback", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = probe_public_page(args.url, args.marker, fallback=args.fallback)
    except ValueError as exc:
        result = {"provider": "validation", "ok": False, "reason": str(exc)}
    data = json.dumps(result, ensure_ascii=False, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(data + "\n")
    else:
        print(data)
    return 0 if result["ok"] and all(result.get("markers_matched", {}).values()) else 1


if __name__ == "__main__":
    sys.exit(main())
