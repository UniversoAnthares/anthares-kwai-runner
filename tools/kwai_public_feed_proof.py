#!/usr/bin/env python3
"""Independent read-only Kwai public feed + source-video proof.

No Android clipboard, private Kwai credentials, browser profile or published
content mutation. A success requires a unique Kwai photo ID, exact public
author, matching caption for new posts, and multiple source-video frame matches.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import pathlib
import re
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request

HANDLE = os.getenv("KWAI_EXPECTED_ACCOUNT","lucasrosalem").strip().lstrip("@").lower()
if HANDLE not in ("lucasrosalem","universoanthares"):raise RuntimeError("KWAI_PUBLIC_FEED_ACCOUNT_INVALID")
PROFILE = f"https://www.kwai.com/@{HANDLE}"
MAX_MEDIA_BYTES = 70 * 1024 * 1024


class ProofError(RuntimeError):
    pass


def normalized(value: str) -> str:
    value = html.unescape(str(value or ""))
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(ch for ch in value if ch.isalnum())


def get_feed(limit: int = 22) -> list[dict]:
    from playwright.sync_api import sync_playwright

    browser = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome", headless=True,
            args=["--mute-audio", "--disable-sync", "--disable-extensions",
                  "--no-first-run", "--disable-background-networking"])
        try:
            page = browser.new_page(locale="pt-BR", user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"))
            response = page.goto(PROFILE, wait_until="domcontentloaded",
                                 timeout=25000)
            if response is None or response.status != 200:
                raise ProofError("public_profile_http_unavailable")
            data = page.evaluate("""(limit) => {
                const a=window.__NUXT__?.data?.[0]?.feedsData?.feeds;
                if(!Array.isArray(a))return null;
                return a.slice(0,limit).map(x=>({
                    photo_id: String(x.photo_id_str||''),
                    account: String(x.kwai_id||''),
                    author: String(x.user_name||''),
                    caption: String(x.caption||''),
                    created_ms: Number(x.timestamp||0),
                    media_url: Array.isArray(x.main_mv_urls)
                      ? String(x.main_mv_urls[0]?.url||'') : ''
                }));
            }""", min(60, max(1, limit)))
            if not isinstance(data, list):
                raise ProofError("kwai_public_feed_missing")
            result = []
            for x in data:
                if not re.fullmatch(r"\d{16,21}", x.get("photo_id", "")):
                    continue
                if x.get("account", "").lower() != HANDLE:
                    continue
                if not isinstance(x.get("created_ms"), (int, float)):
                    continue
                result.append(x)
            if not result:
                raise ProofError("kwai_public_feed_empty_or_wrong_account")
            return result
        finally:
            browser.close()


def scan_public_profile_window(
    *, started_ms: int, caption: str, before_ms: int = 8 * 60 * 1000,
    after_ms: int = 18 * 60 * 1000, settle_ms: int = 30 * 60 * 1000,
    max_pages: int = 24, baseline_ids: list[str] | None = None,
) -> dict:
    """Independent, read-only, paginated profile inventory for uncertain posts.

    A missing video is a failure ONLY after the listing has reached older
    than the target interval, its response sequence is complete and the
    external publication grace period has elapsed. This does not authorize
    retry/re-lease of uncertain posts or replace the source-frame proof.
    """
    if not isinstance(started_ms, int) or started_ms < 1_600_000_000_000:
        raise ProofError("scan_start_time_invalid")
    if not normalized(caption) or len(normalized(caption)) < 15:
        raise ProofError("scan_caption_invalid")
    if not 1 <= max_pages <= 40:
        raise ProofError("scan_max_pages_invalid")
    from playwright.sync_api import sync_playwright
    low = started_ms - before_ms
    high = started_ms + after_ms
    rows = {}
    pages = []
    errors = []
    collected = set()

    def add_page(feeds, cursor, source):
        if not isinstance(feeds, list):
            errors.append("profile_page_invalid")
            return
        cursor_key = str(cursor or "")
        if cursor_key in collected and source != "initial":
            return
        collected.add(cursor_key)
        parsed = []
        for x in feeds:
            try:
                item = {
                    "photo_id": str(x.get("photo_id_str") or ""),
                    "account": str(x.get("kwai_id") or "").lower(),
                    "author": str(x.get("user_name") or ""),
                    "caption": str(x.get("caption") or ""),
                    "created_ms": int(x.get("timestamp") or 0),
                    "media_url": str((x.get("main_mv_urls") or [{}])[0].get("url") or ""),
                }
                if (re.fullmatch(r"[0-9]{16,21}", item["photo_id"])
                        and item["account"] == HANDLE
                        and item["created_ms"] > 0):
                    parsed.append(item)
                    rows[item["photo_id"]] = item
            except (TypeError, AttributeError, ValueError, IndexError):
                continue
        if not parsed:
            errors.append("profile_page_missing_valid_posts")
            return
        times = [x["created_ms"] for x in parsed]
        if times != sorted(times, reverse=True):
            errors.append("profile_page_not_chronological")
        if pages and max(times) > pages[-1]["oldest_ms"]:
            errors.append("profile_page_out_of_order")
        pages.append({"source": source, "count": len(parsed),
                      "newest_ms": max(times), "oldest_ms": min(times),
                      "cursor": cursor_key})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True,
            args=["--mute-audio", "--disable-sync", "--disable-extensions",
                  "--no-first-run", "--disable-background-networking"])
        try:
            page = browser.new_page(locale="pt-BR", user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"))
            def capture(response):
                if "/rest/o/w/pc/feed/profile" not in response.url:
                    return
                try:
                    data = response.json()
                    if response.status != 200 or data.get("result") != 1:
                        errors.append("profile_api_bad_response")
                        return
                    add_page(data.get("feeds"), data.get("cursor"), "pagination")
                except (ValueError, TypeError, Exception):
                    errors.append("profile_api_unreadable")
            page.on("response", capture)
            response = page.goto(PROFILE, wait_until="domcontentloaded", timeout=25000)
            if response is None or response.status != 200:
                raise ProofError("public_profile_http_unavailable")
            initial = page.evaluate("""() => {
                const value = window.__NUXT__?.data?.[0]?.feedsData;
                return value ? {feeds:value.feeds, cursor:value.cursor} : null;
            }""")
            if not isinstance(initial, dict):
                raise ProofError("public_profile_initial_inventory_missing")
            add_page(initial.get("feeds"), initial.get("cursor"), "initial")
            for _ in range(max_pages - 1):
                if pages and pages[-1]["oldest_ms"] <= low:
                    break
                count = len(pages)
                page.evaluate("""() => {
                    const el = document.querySelector('#main-container');
                    if (el) el.scrollTop = el.scrollHeight;
                }""")
                page.wait_for_timeout(800)
                if len(pages) == count:
                    page.wait_for_timeout(500)
                if len(pages) == count:
                    errors.append("profile_pagination_stopped")
                    break
        finally:
            browser.close()
    listing = sorted(rows.values(), key=lambda x: x["created_ms"], reverse=True)
    if not listing:
        raise ProofError("public_profile_inventory_empty")
    oldest = listing[-1]["created_ms"]
    newest = listing[0]["created_ms"]
    coverage = oldest <= low and not errors
    wanted = normalized(caption)
    baseline = set(baseline_ids or [])
    matches = []
    for row in listing:
        if row["photo_id"] in baseline or not low <= row["created_ms"] <= high:
            continue
        actual = normalized(row["caption"])
        caption_match = len(actual) >= 25 and (
            wanted[:min(len(wanted), 62)] in actual
            or actual[:min(len(actual), 62)] in wanted)
        if caption_match:
            matches.append({"photo_id": row["photo_id"],
                            "public_url": PROFILE + "/video/" + row["photo_id"],
                            "created_ms": row["created_ms"],
                            "caption": row["caption"], "author": row["author"],
                            "media_url": row["media_url"],
                            "caption_match": True})
    now_ms = int(time.time() * 1000)
    if matches:
        status = "PUBLIC_CANDIDATE_REQUIRES_SOURCE_MEDIA_PROOF"
    elif coverage and now_ms >= high + settle_ms:
        status = "FAILED_ABSENT_FROM_COVERED_PUBLIC_PROFILE"
    elif coverage:
        status = "PENDING_PROPAGATION_GRACE"
    else:
        status = "INCOMPLETE_PROFILE_COVERAGE"
    return {"kind": "kwai_paginated_public_profile_window_v1",
            "account": HANDLE, "status": status, "coverage_complete": coverage,
            "window_start_ms": low, "window_end_ms": high,
            "checked_at_ms": now_ms, "newest_ms": newest,
            "oldest_ms": oldest, "items_scanned": len(listing),
            "pages_scanned": len(pages), "errors": errors,
            "matches": matches}


_LAST_FALLBACK_SCAN_MS = 0

def sha256_file(path: pathlib.Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 512), b""):
            sha.update(block)
    return sha.hexdigest()


def download_public_media(url: str, target: pathlib.Path) -> pathlib.Path:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ProofError("invalid_media_scheme")
    host = parsed.hostname.lower()
    if host not in {"anthares.us", "www.anthares.us"} and not (
        host.endswith(".kwai.net") or host.endswith(".kwai.com")):
        raise ProofError("unexpected_media_origin")
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (AntharesPublicProof/1.0)"})
    try:
        with urllib.request.urlopen(request, timeout=45) as stream:
            if stream.status != 200:
                raise ProofError("media_http_not_ok")
            size = 0
            with target.open("wb") as destination:
                while True:
                    chunk = stream.read(1024 * 256)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_MEDIA_BYTES:
                        raise ProofError("media_size_limit")
                    destination.write(chunk)
    except (OSError, ValueError) as exc:
        raise ProofError("media_download_failed") from exc
    if target.stat().st_size < 2048:
        raise ProofError("media_empty")
    return target


def sampled_features(path: pathlib.Path):
    import cv2
    video = cv2.VideoCapture(str(path))
    fps = video.get(cv2.CAP_PROP_FPS)
    frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frames / fps if fps else 0
    if duration < 4 or duration > 1500:
        video.release()
        raise ProofError("media_duration_out_of_bounds")
    sift = cv2.SIFT_create(nfeatures=1250)
    result = []
    for fraction in (0.12, 0.28, 0.44, 0.60, 0.76, 0.90):
        video.set(cv2.CAP_PROP_POS_MSEC, duration * 1000 * fraction)
        valid, image = video.read()
        if not valid:
            continue
        height, width = image.shape[:2]
        factor = 460 / max(height, width)
        image = cv2.resize(image, (max(1, int(width * factor)),
                                    max(1, int(height * factor))))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result.append(sift.detectAndCompute(gray, None))
    video.release()
    if len(result) < 4:
        raise ProofError("insufficient_decodable_media_frames")
    return duration, result


def feature_inliers(first, second) -> int:
    import cv2
    import numpy as np
    key1, desc1 = first
    key2, desc2 = second
    if desc1 is None or desc2 is None or min(len(desc1), len(desc2)) < 12:
        return 0
    pairs = cv2.BFMatcher().knnMatch(desc1, desc2, k=2)
    close = [a for a, b in pairs if a.distance < .70 * b.distance]
    if len(close) < 9:
        return len(close)
    pts1 = np.float32([key1[m.queryIdx].pt for m in close]).reshape(-1, 1, 2)
    pts2 = np.float32([key2[m.trainIdx].pt for m in close]).reshape(-1, 1, 2)
    try:
        _, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5)
    except cv2.error:
        return 0
    return int(mask.sum()) if mask is not None else 0


def compare_media(source: pathlib.Path, public: pathlib.Path) -> dict:
    length_source, a = sampled_features(source)
    length_public, b = sampled_features(public)
    best = [max(feature_inliers(x, y) for y in b) for x in a]
    qualifying = sum(score >= 240 for score in best)
    if qualifying < 4:
        raise ProofError("public_video_content_does_not_match_source")
    return {
        "kind": "sift_source_to_public_cdn_v1",
        "source_best_inliers": best,
        "qualifying_distinct_frames": qualifying,
        "source_duration_seconds": round(length_source, 3),
        "public_duration_seconds": round(length_public, 3),
    }


def prove(
    *, job_id: str, caption: str, expected_sha: str,
    source_file: str = "", source_url: str = "",
    baseline_ids: list[str] | None = None,
    started_ms: int = 0, allow_placeholder: bool = False,
) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9._:-]{5,180}", job_id):
        raise ProofError("job_id_invalid")
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha):
        raise ProofError("source_digest_invalid")
    title_key = normalized(caption)
    if len(title_key) < 15:
        raise ProofError("expected_caption_invalid")
    feed = get_feed(30)
    baseline = set(baseline_ids or [])
    now_ms = int(time.time() * 1000)
    eligible = []
    for row in feed:
        if row["photo_id"] in baseline:
            continue
        if row["account"].lower() != HANDLE:
            continue
        if (HANDLE=="lucasrosalem" and normalized(row["author"]) != normalized("Lucas Rosalem")) or (HANDLE=="universoanthares" and not normalized(row["author"])):
            continue
        posted = int(row["created_ms"])
        if posted > now_ms + 2 * 60 * 1000:
            continue
        if started_ms:
            if posted < started_ms - 8 * 60 * 1000 or posted > started_ms + 18 * 60 * 1000:
                continue
        else:
            if posted < now_ms - 30 * 60 * 1000:
                continue
        actual = normalized(row["caption"])
        matching_caption = len(actual) >= 25 and (
            title_key[:min(len(title_key), 62)] in actual
            or actual[:min(len(actual), 62)] in title_key)
        placeholder = allow_placeholder and row["caption"].strip() == "..."
        if not matching_caption and not placeholder:
            continue
        eligible.append((row, matching_caption))
    # Redundant on-profile chronological scan is deliberately throttled:
    # the original newest-post check remains primary and inexpensive.
    if not eligible and started_ms and now_ms - started_ms >= 120000:
        global _LAST_FALLBACK_SCAN_MS
        if now_ms - _LAST_FALLBACK_SCAN_MS >= 60000:
            _LAST_FALLBACK_SCAN_MS = now_ms
            fallback = scan_public_profile_window(
                started_ms=started_ms, caption=caption,
                baseline_ids=list(baseline))
            for item in fallback["matches"]:
                eligible.append(({
                    "photo_id": item["photo_id"], "caption": item["caption"],
                    "author": item["author"], "account": HANDLE,
                    "created_ms": item["created_ms"],
                    "media_url": item["media_url"]}, True))
            if not eligible and fallback["status"] == "FAILED_ABSENT_FROM_COVERED_PUBLIC_PROFILE":
                raise ProofError("failed_absent_from_covered_public_profile")
    if not eligible:
        raise ProofError("no_new_public_post_with_caption_and_account")
    with tempfile.TemporaryDirectory(prefix="kwai-public-media-proof-") as temp:
        tmp = pathlib.Path(temp)
        source = pathlib.Path(source_file) if source_file else tmp / "source.mp4"
        if not source.is_file():
            if not source_url:
                raise ProofError("source_media_unavailable")
            download_public_media(source_url, source)
        if sha256_file(source) != expected_sha:
            raise ProofError("source_media_digest_mismatch")
        matches = []
        for row, caption_match in eligible:
            try:
                published = tmp / f"public-{row['photo_id']}.mp4"
                download_public_media(row["media_url"], published)
                match = compare_media(source, published)
                match["public_media_sha256"] = sha256_file(published)
                matches.append((row, caption_match, match))
            except ProofError:
                continue
    if len(matches) != 1:
        raise ProofError("no_unique_public_media_match")
    row, caption_match, match = matches[0]
    url = f"{PROFILE}/video/{row['photo_id']}"
    return {
        "ok": True,
        "kind": "kwai_public_profile_source_frame_proof_v1",
        "verified_publication_job_id": job_id,
        "public_url": url,
        "expected_account": HANDLE,
        "actual_author_handle": HANDLE,
        "caption": caption,
        "actual_public_caption": row["caption"],
        "title_match": caption_match,
        "placeholder_caption_legacy_recovery": bool(not caption_match),
        "media_sha256": expected_sha,
        "public_media_sha256": match["public_media_sha256"],
        "media_match": match,
        "photo_id": row["photo_id"],
        "public_post_timestamp_ms": int(row["created_ms"]),
        "checked_at_epoch_ms": int(time.time() * 1000),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--source-file", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--started-ms", type=int, default=0)
    parser.add_argument("--baseline-file", default="")
    parser.add_argument("--allow-placeholder", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    baseline = []
    if args.baseline_file:
        rows = json.loads(pathlib.Path(args.baseline_file).read_text(encoding="utf-8"))
        baseline = [str(x) for x in rows.get("photo_ids", [])]
    result = prove(
        job_id=args.job_id, caption=args.caption,
        expected_sha=args.expected_sha.lower(),
        source_file=args.source_file, source_url=args.source_url,
        baseline_ids=baseline, started_ms=args.started_ms,
        allow_placeholder=args.allow_placeholder)
    path = pathlib.Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    os.replace(temporary, path)
    print("KWAI_PUBLIC_MEDIA_PROOF=PASS JOB=" + args.job_id
          + " PHOTO_ID=" + result["photo_id"]
          + " MATCHED_FRAMES=" + str(result["media_match"]["qualifying_distinct_frames"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

