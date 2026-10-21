"""Render-independent X worker backed by the Cloudflare browser-state vault.

This module deliberately reuses the durable Anthares browser context whose
signing/encryption identity derives from ARA_SHARED.  It therefore needs no
legacy Render X_WORKER_TOKEN to restore the migrated runtime session.
"""
from __future__ import annotations

import os
import re
import tempfile
import time
import json
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.x_publication_safety import validate_video, verified_post_url
from x_durable_ledger import begin as durable_begin, confirm as durable_confirm

import requests
from flask import Flask, jsonify, request

import anthares_runtime_browser_local as runtime

app = Flask(__name__)
EXPECTED = os.getenv("EXPECTED_X_HANDLE", "lucasyahn").strip().lstrip("@").lower()
CLIENT_TOKEN = os.getenv("X_WORKER_TOKEN") or os.getenv("ARA_SHARED", "")


def _auth_ok() -> bool:
    bearer = request.headers.get("Authorization", "")
    allowed = {t for t in (CLIENT_TOKEN, os.getenv("ARA_SHARED", "")) if t}
    return bool(allowed) and bearer in {"Bearer " + t for t in allowed}


def _identity(page) -> str:
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1800)
    if "/login" in page.url or "/i/flow/login" in page.url or "/i/jf/onboarding" in page.url:
        raise RuntimeError("authentication required")
    link = page.locator('a[data-testid="AppTabBar_Profile_Link"]').first
    href = link.get_attribute("href") if link.count() else ""
    handle = (href or "").strip("/").split("/")[0].lower()
    if handle != EXPECTED:
        raise RuntimeError("identity mismatch")
    return handle


def _statuses(page, handle: str) -> set[str]:
    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    urls = set()
    links = page.locator('a[href*="/status/"]')
    for i in range(min(links.count(), 100)):
        href = links.nth(i).get_attribute("href") or ""
        matched = re.search(r"^/(?:%s)/status/(\d+)(?:/|$)" % re.escape(handle), href, re.I)
        if matched:
            urls.add(f"https://x.com/{handle}/status/{matched.group(1)}")
    return urls


def _safe_media_host(url: str) -> bool:
    try:
        p = urlparse(url)
        return (p.scheme == "https" and not p.username and not p.password
                and p.port in (None, 443) and p.hostname in {
                    "anthares.us", "www.anthares.us", "github.com",
                    "raw.githubusercontent.com", "release-assets.githubusercontent.com",
                    "objects.githubusercontent.com"})
    except (ValueError, TypeError):
        return False


def _download_media(url: str) -> str:
    if not _safe_media_host(url):
        raise RuntimeError("X_MEDIA_URL_UNTRUSTED")
    fd, path = tempfile.mkstemp(prefix="anthares-x-", suffix=".mp4")
    total = 0
    try:
        with os.fdopen(fd, "wb") as target, requests.get(
                url, timeout=(15, 90), allow_redirects=True, stream=True) as r:
            r.raise_for_status()
            if not _safe_media_host(r.url):
                raise RuntimeError("X_MEDIA_REDIRECT_UNTRUSTED")
            if "text/html" in (r.headers.get("content-type") or "").lower():
                raise RuntimeError("X_MEDIA_HTML_RESPONSE")
            for chunk in r.iter_content(256 * 1024):
                total += len(chunk)
                if total > 99_000_000:
                    raise RuntimeError("X_MEDIA_OVER_99MB")
                target.write(chunk)
        if total < 100_000:
            raise RuntimeError("X_MEDIA_TOO_SMALL")
        validate_video(path)
        return path
    except Exception:
        os.unlink(path)
        raise




@app.get("/health")
def health_route():
    h = runtime.health()
    return jsonify(
        ok=bool(h.get("healthy")),
        backend=h.get("backend"),
        browser_vault=True,
        vault_ready=bool(h.get("vault_enabled")),
        browser_ready=bool(h.get("chromium_running")),
        browser_preflight_required=bool(h.get("browser_preflight_required")),
        restore_status=h.get("restore_status"),
        render_dependency=False,
    ), (200 if h.get("healthy") else 503)


@app.get("/v1/runtime/browser/signing-public-key")
def signing_public_key():
    try:
        return jsonify(ok=True, jwk=runtime.public_jwk(), authority=os.getenv("ANTHARES_BROWSER_STATE_AUTHORITY", "runtime"), render_dependency=False)
    except Exception as exc:
        return jsonify(ok=False, error=type(exc).__name__), 503


@app.get("/post-status")
def post_status():
    if not _auth_ok():
        return jsonify(ok=False, error="unauthorized"), 401
    try:
        from x_durable_ledger import readback
        return jsonify(ok=True, **readback(request.args.get("idempotency_key", "")))
    except Exception as exc:
        return jsonify(ok=False, error=type(exc).__name__), 503


@app.get("/verify")
def verify_route():
    if not _auth_ok():
        return jsonify(ok=False, error="unauthorized"), 401
    try:
        with runtime._LOCK:
            _, page = runtime._ensure_browser()
            handle = _identity(page)
            persisted = runtime._persist()
        return jsonify(ok=True, handle=handle, durable=bool(persisted), browser_vault=True, render_dependency=False)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)[:500]), 503




@app.post("/post")
def post_route():
    if not _auth_ok():
        return jsonify(ok=False, error="unauthorized"), 401
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    media_url = str(data.get("media_url") or "").strip()
    key = str(data.get("idempotency_key") or "").strip()
    if not text or not media_url or not re.fullmatch(r"[A-Za-z0-9_.:-]{12,160}", key):
        return jsonify(ok=False, error="text/media_url/idempotency_key required"), 400
    if len(text) > 280:
        return jsonify(ok=False, error="X_CAPTION_OVER_280"), 400
    media_path = None
    try:
        media_path = _download_media(media_url)
        with runtime._LOCK:
            context, page = runtime._ensure_browser()
            handle = _identity(page)
            before = _statuses(page, handle)
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1000)
            editor = page.locator('[data-testid="tweetTextarea_0"]').first
            editor.wait_for(state="visible", timeout=15000)
            editor.fill(text)
            page.locator('input[type="file"]').first.set_input_files(media_path)
            # Wait for an uploaded preview rather than relying on locale-specific labels.
            deadline = time.time() + 75
            while time.time() < deadline:
                if page.locator('video, [data-testid="attachments"] video, [data-testid="media-preview"] video').count() > 0:
                    break
                page.wait_for_timeout(800)
            button = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
            deadline = time.time() + 40
            attempt = None
            while time.time() < deadline:
                if button.count() and button.is_enabled():
                    try:
                        attempt = durable_begin(key)
                    except Exception as exc:
                        from x_durable_ledger import AlreadyStarted
                        if not isinstance(exc, AlreadyStarted):
                            raise
                        return jsonify(ok=False, error="X_SUBMISSION_ALREADY_STARTED_RECONCILE_FIRST"), 409
                    button.click()
                    break
                page.wait_for_timeout(500)
            else:
                raise RuntimeError("post button disabled")

            deadline = time.time() + 90
            after = ""
            while time.time() < deadline:
                page.wait_for_timeout(1800)
                found = _statuses(page, handle) - before
                if found:
                    after = sorted(found, reverse=True)[0]
                    break
            if not after:
                raise RuntimeError("X_SUBMISSION_UNCERTAIN_RECONCILE_NO_AUTOMATIC_RETRY")
            check = context.new_page()
            try:
                check.goto(after, wait_until="domcontentloaded", timeout=45000)
                check.wait_for_timeout(1800)
                if check.locator("video").count() < 1:
                    raise RuntimeError("X_POST_UNCERTAIN_VIDEO_NOT_VISIBLE")
                posted_text = " ".join(check.locator('[data-testid="tweetText"]').all_text_contents())
                if " ".join(text.split()) not in " ".join(posted_text.split()):
                    raise RuntimeError("X_POST_UNCERTAIN_CAPTION_MISMATCH")
                if verified_post_url(after) != after:
                    raise RuntimeError("X_POST_UNCERTAIN_WRONG_ACCOUNT")
            finally:
                check.close()
            persisted = runtime._persist()
            durable_confirm(attempt, after)
        return jsonify(ok=True, handle=handle, post_url=after, video_verified=True, durable=bool(persisted), render_dependency=False)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)[:700]), 503
    finally:
        if media_path:
            try:
                os.unlink(media_path)
            except OSError:
                pass
