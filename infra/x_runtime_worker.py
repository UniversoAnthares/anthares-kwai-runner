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

import requests
from flask import Flask, jsonify, request

import anthares_runtime_browser_local as runtime

app = Flask(__name__)
EXPECTED = os.getenv("EXPECTED_X_HANDLE", "lucasyahn").strip().lstrip("@").lower()
CLIENT_TOKEN = os.getenv("X_WORKER_TOKEN") or os.getenv("ARA_SHARED", "")


def _auth_ok() -> bool:
    return bool(CLIENT_TOKEN) and request.headers.get("Authorization", "") == "Bearer " + CLIENT_TOKEN


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


def _latest(page, handle: str) -> str:
    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    links = page.locator('a[href*="/status/"]')
    for i in range(min(links.count(), 80)):
        href = links.nth(i).get_attribute("href") or ""
        m = re.search(r"/status/(\d+)", href)
        if m:
            return f"https://x.com/{handle}/status/{m.group(1)}"
    return ""


def _download_media(url: str) -> str:
    r = requests.get(url, timeout=90, allow_redirects=True)
    r.raise_for_status()
    ctype = (r.headers.get("content-type") or "").lower()
    if len(r.content) < 1024 or len(r.content) > 50_000_000 or "text/html" in ctype:
        raise RuntimeError("invalid media response")
    fd, path = tempfile.mkstemp(prefix="anthares-x-", suffix=".mp4")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
    return path


@app.get("/health")
def health_route():
    h = runtime.health()
    return jsonify(
        ok=bool(h.get("healthy")),
        backend=h.get("backend"),
        browser_vault=True,
        vault_ready=bool(h.get("vault_enabled")),
        restore_status=h.get("restore_status"),
        render_dependency=False,
    ), (200 if h.get("healthy") else 503)


@app.get("/v1/runtime/browser/signing-public-key")
def signing_public_key():
    try:
        return jsonify(ok=True, jwk=runtime.public_jwk(), authority=os.getenv("ANTHARES_BROWSER_STATE_AUTHORITY", "runtime"), render_dependency=False)
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
    if not text or not media_url:
        return jsonify(ok=False, error="missing text/media_url"), 400
    media_path = None
    try:
        media_path = _download_media(media_url)
        with runtime._LOCK:
            context, page = runtime._ensure_browser()
            handle = _identity(page)
            before = _latest(page, handle)
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
            while time.time() < deadline:
                if button.count() and button.is_enabled():
                    button.click()
                    break
                page.wait_for_timeout(500)
            else:
                raise RuntimeError("post button disabled")

            deadline = time.time() + 90
            after = ""
            while time.time() < deadline:
                page.wait_for_timeout(1800)
                after = _latest(page, handle)
                if after and after != before:
                    break
            if not after or after == before:
                raise RuntimeError("publication not confirmed")
            check = context.new_page()
            try:
                check.goto(after, wait_until="domcontentloaded", timeout=45000)
                check.wait_for_timeout(1800)
                if check.locator("video").count() < 1:
                    raise RuntimeError("published post has no visible video")
            finally:
                check.close()
            persisted = runtime._persist()
        return jsonify(ok=True, handle=handle, post_url=after, video_verified=True, durable=bool(persisted), render_dependency=False)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)[:700]), 503
    finally:
        if media_path:
            try:
                os.unlink(media_path)
            except OSError:
                pass
