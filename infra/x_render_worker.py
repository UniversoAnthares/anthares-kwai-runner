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


def _state():
    raw = os.getenv("X_STORAGE_STATE", "")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("cookies"), list):
        raise RuntimeError("invalid X storage state")
    return data


def _auth_ok(req):
    return bool(TOKEN) and req.headers.get("Authorization", "") == "Bearer " + TOKEN


def _identity(page):
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
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
    page.wait_for_timeout(1200)
    links = page.locator('a[href*="/status/"]')
    for i in range(min(links.count(), 50)):
        href = links.nth(i).get_attribute("href") or ""
        m = re.search(r"/status/(\d+)", href)
        if m:
            return f"https://x.com/{handle}/status/{m.group(1)}"
    return ""


def _publish(text):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(storage_state=_state(), viewport={"width": 1280, "height": 900})
        page = context.new_page()
        try:
            handle = _identity(page)
            before = _latest(page, handle)
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1000)
            editor = page.locator('[data-testid="tweetTextarea_0"]').first
            editor.wait_for(state="visible", timeout=10000)
            editor.fill(text)
            button = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
            deadline = time.time() + 30
            while time.time() < deadline:
                if button.is_enabled():
                    button.click()
                    break
                page.wait_for_timeout(500)
            else:
                raise RuntimeError("post button disabled")
            deadline = time.time() + 60
            while time.time() < deadline:
                page.wait_for_timeout(1500)
                after = _latest(page, handle)
                if after and after != before:
                    return {"handle": handle, "post_url": after}
            raise RuntimeError("publication not confirmed")
        finally:
            context.close()
            browser.close()


@app.get("/health")
def health():
    return jsonify(ok=True, state_configured=bool(os.getenv("X_STORAGE_STATE", "")))


@app.get("/verify")
def verify():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state=_state())
            page = context.new_page()
            handle = _identity(page)
            context.close(); browser.close()
        return jsonify(ok=True, handle=handle)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 503


@app.post("/post")
def post():
    if not _auth_ok(request):
        return jsonify(ok=False, error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or "")[:280]
    if not text:
        return jsonify(ok=False, error="text required"), 400
    try:
        return jsonify(ok=True, **_publish(text))
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500
