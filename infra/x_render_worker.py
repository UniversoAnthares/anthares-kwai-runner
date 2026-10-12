import json
import os
import re
import tempfile
import time

import requests
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)
EXPECTED = os.getenv("EXPECTED_X_HANDLE", "lucasyahn").strip().lstrip("@").lower()
TOKEN = os.getenv("X_WORKER_TOKEN", "")
STATE_PATH = os.getenv("X_STATE_PATH", "/tmp/anthares-x-storage-state.json")


def _state():
    raw = os.getenv("X_STORAGE_STATE", "")
    if not raw and os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as fh:
            raw = fh.read()
    if not raw:
        raise RuntimeError("X storage state not configured")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("cookies"), list):
        raise RuntimeError("invalid X storage state")
    names = {str(c.get("name") or "") for c in data["cookies"] if isinstance(c, dict)}
    if "auth_token" not in names or "ct0" not in names:
        raise RuntimeError("X auth cookies missing")
    return data


def _auth_ok(req):
    return bool(TOKEN) and req.headers.get("Authorization", "") == "Bearer " + TOKEN


def _identity(page):
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


def _latest(page, handle):
    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    links = page.locator('a[href*="/status/"]')
    for i in range(min(links.count(), 80)):
        href = links.nth(i).get_attribute("href") or ""
        m = re.search(r"/status/(\d+)", href)
        if m:
            return f"https://x.com/{handle}/status/{m.group(1)}"
    return ""


def _download_media(url):
    if not url.startswith("https://"):
        raise RuntimeError("https media_url required")
    r = requests.get(url, timeout=60, allow_redirects=True)
    r.raise_for_status()
    if len(r.content) > 50 * 1024 * 1024:
        raise RuntimeError("media too large")
    suffix = ".mp4"
    fd, path = tempfile.mkstemp(prefix="anthares-x-", suffix=suffix)
    os.close(fd)
    with open(path, "wb") as fh:
        fh.write(r.content)
    return path


def _publish(text, media_url):
    media_path = _download_media(media_url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state=_state(), viewport={"width": 1280, "height": 900})
            page = context.new_page()
            try:
                handle = _identity(page)
                before = _latest(page, handle)
                page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1200)
                editor = page.locator('[data-testid="tweetTextarea_0"]').first
                editor.wait_for(state="visible", timeout=15000)
                editor.fill(text)
                file_input = page.locator('input[data-testid="fileInput"]').first
                file_input.set_input_files(media_path)
                remove_media = page.get_by_label("Remove media").or_(page.get_by_label("Remover mídia"))
                deadline = time.time() + 90
                while time.time() < deadline:
                    if remove_media.count() and remove_media.first.is_visible():
                        break
                    page.wait_for_timeout(1000)
                else:
                    raise RuntimeError("media attachment not confirmed")
                button = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                deadline = time.time() + 90
                while time.time() < deadline:
                    if button.count() and button.is_enabled():
                        button.click()
                        break
                    page.wait_for_timeout(1000)
                else:
                    raise RuntimeError("post button disabled")
                deadline = time.time() + 90
                while time.time() < deadline:
                    page.wait_for_timeout(2000)
                    after = _latest(page, handle)
                    if after and after != before:
                        page.goto(after, wait_until="domcontentloaded", timeout=45000)
                        page.wait_for_timeout(1800)
                        has_video = page.locator("video").count() > 0 or page.locator('[data-testid="videoPlayer"]').count() > 0
                        if not has_video:
                            raise RuntimeError("published post has no visible video")
                        return {"handle": handle, "post_url": after, "video_verified": True}
                raise RuntimeError("publication not confirmed")
            finally:
                context.close()
                browser.close()
    finally:
        try:
            os.unlink(media_path)
        except OSError:
            pass


@app.get("/health")
def health():
    return jsonify(ok=True, state_configured=bool(os.getenv("X_STORAGE_STATE", "")) or os.path.exists(STATE_PATH))


@app.post("/ingest-state")
def ingest_state():
    if not _auth_ok(request):
        return jsonify(ok=False, error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    data = body.get("storage_state")
    if not isinstance(data, dict) or not isinstance(data.get("cookies"), list):
        return jsonify(ok=False, error="invalid storage_state"), 400
    names = {str(c.get("name") or "") for c in data["cookies"] if isinstance(c, dict)}
    if "auth_token" not in names or "ct0" not in names:
        return jsonify(ok=False, error="required X cookies missing"), 400
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    os.replace(tmp, STATE_PATH)
    return jsonify(ok=True, cookie_count=len(data["cookies"]))


@app.get("/verify")
def verify():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state=_state())
            page = context.new_page()
            handle = _identity(page)
            context.close()
            browser.close()
        return jsonify(ok=True, handle=handle)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 503


@app.post("/post")
def post():
    if not _auth_ok(request):
        return jsonify(ok=False, error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or "")[:280]
    media_url = str(body.get("media_url") or "")
    if not text:
        return jsonify(ok=False, error="text required"), 400
    if not media_url:
        return jsonify(ok=False, error="media_url required"), 400
    try:
        return jsonify(ok=True, **_publish(text, media_url))
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500
