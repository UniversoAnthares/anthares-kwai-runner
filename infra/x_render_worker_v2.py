import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time

import requests
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)
EXPECTED = os.getenv("EXPECTED_X_HANDLE", "lucasyahn").strip().lstrip("@").lower()
TOKEN = os.getenv("X_WORKER_TOKEN", "")
VAULT_URL = os.getenv("X_VAULT_URL", "https://anthares-x-vault.anthares1.workers.dev/state")
VAULT_PRIVATE_KEY = os.getenv("X_VAULT_PRIVATE_KEY", "")
STATE_PASSPHRASE = os.getenv("X_STATE_PASSPHRASE", "")
STATE_PATH = os.getenv("X_STATE_PATH", "/tmp/anthares-x-storage-state.json")


def _auth_ok(req):
    return bool(TOKEN) and req.headers.get("Authorization", "") == "Bearer " + TOKEN


def _validate_state(data):
    if not isinstance(data, dict) or not isinstance(data.get("cookies"), list):
        raise RuntimeError("invalid X storage state")
    if not data["cookies"]:
        raise RuntimeError("empty X storage state")
    if "origins" in data and not isinstance(data.get("origins"), list):
        raise RuntimeError("invalid X origins")
    return {"cookies": data["cookies"], "origins": data.get("origins", [])}


def _openssl(args, payload=None):
    p = subprocess.run(args, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return p.stdout


def _encrypt_state(data):
    if not STATE_PASSPHRASE:
        raise RuntimeError("state encryption unavailable")
    raw = json.dumps(_validate_state(data), separators=(",", ":")).encode()
    out = _openssl([
        "openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-iter", "200000",
        "-pass", "env:X_STATE_PASSPHRASE"
    ], raw)
    return base64.b64encode(out).decode("ascii")


def _decrypt_state(ciphertext):
    if not STATE_PASSPHRASE:
        raise RuntimeError("state encryption unavailable")
    raw = base64.b64decode(ciphertext, validate=True)
    out = _openssl([
        "openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
        "-pass", "env:X_STATE_PASSPHRASE"
    ], raw)
    return _validate_state(json.loads(out.decode("utf-8")))


def _signature(body):
    if not VAULT_PRIVATE_KEY:
        raise RuntimeError("vault signer unavailable")
    ts = str(int(time.time() * 1000))
    digest = hashlib.sha256(body.encode()).hexdigest()
    message = (ts + "." + digest).encode()
    with tempfile.NamedTemporaryFile("w", delete=False) as keyf:
        keyf.write(VAULT_PRIVATE_KEY)
        key_path = keyf.name
    try:
        sig = _openssl(["openssl", "dgst", "-sha256", "-sign", key_path], message)
    finally:
        try:
            os.unlink(key_path)
        except OSError:
            pass
    return ts, base64.b64encode(sig).decode("ascii")


def _vault_request(method, body=""):
    ts, sig = _signature(body)
    headers = {"X-Anthares-Timestamp": ts, "X-Anthares-Signature": sig}
    if body:
        headers["Content-Type"] = "application/json"
    r = requests.request(method, VAULT_URL, headers=headers, data=body or None, timeout=20)
    return r


def _vault_pull():
    r = _vault_request("GET")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    if not data.get("ok") or not data.get("available"):
        return None
    return _decrypt_state(data["ciphertext"])


def _vault_push(state):
    ciphertext = _encrypt_state(state)
    body = json.dumps({
        "schema": "anthares.encrypted-browser-state.v1",
        "ciphertext": ciphertext,
        "sha256": hashlib.sha256(ciphertext.encode("ascii")).hexdigest(),
    }, separators=(",", ":"))
    r = _vault_request("POST", body)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok") or not data.get("stored"):
        raise RuntimeError("vault did not acknowledge state")
    return data


def _state():
    try:
        state = _vault_pull()
        if state:
            return state
    except Exception:
        pass
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return _validate_state(json.load(f))
    raw = os.getenv("X_STORAGE_STATE", "")
    if raw:
        return _validate_state(json.loads(raw))
    raise RuntimeError("X storage state unavailable")


def _save_state(state):
    state = _validate_state(state)
    fd, tmp = tempfile.mkstemp(prefix="x-state-", suffix=".json", dir="/tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"))
        os.replace(tmp, STATE_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    _vault_push(state)


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
    for i in range(min(links.count(), 60)):
        href = links.nth(i).get_attribute("href") or ""
        m = re.search(r"/status/(\d+)", href)
        if m:
            return f"https://x.com/{handle}/status/{m.group(1)}"
    return ""


def _download_media(url):
    r = requests.get(url, timeout=90, allow_redirects=True)
    r.raise_for_status()
    ctype = (r.headers.get("content-type") or "").lower()
    if len(r.content) < 1024 or len(r.content) > 50_000_000:
        raise RuntimeError("invalid media size")
    if "text/html" in ctype:
        raise RuntimeError("media URL returned HTML")
    fd, path = tempfile.mkstemp(prefix="anthares-x-", suffix=".mp4")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
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
                page.wait_for_timeout(1000)
                editor = page.locator('[data-testid="tweetTextarea_0"]').first
                editor.wait_for(state="visible", timeout=10000)
                editor.fill(text)
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(media_path)
                page.get_by_label("Remove media").wait_for(state="visible", timeout=60000)
                button = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                deadline = time.time() + 30
                while time.time() < deadline:
                    if button.is_enabled():
                        button.click()
                        break
                    page.wait_for_timeout(500)
                else:
                    raise RuntimeError("post button disabled")
                deadline = time.time() + 75
                while time.time() < deadline:
                    page.wait_for_timeout(1800)
                    after = _latest(page, handle)
                    if after and after != before:
                        check = context.new_page()
                        check.goto(after, wait_until="domcontentloaded", timeout=45000)
                        check.wait_for_timeout(1800)
                        if check.locator("video").count() < 1:
                            raise RuntimeError("published post has no visible video")
                        _save_state(context.storage_state())
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
    vault = False
    try:
        r = requests.get(VAULT_URL.rsplit("/", 1)[0] + "/health", timeout=10)
        vault = r.ok and bool(r.json().get("persistent_state"))
    except Exception:
        pass
    return jsonify(ok=True, vault_ready=vault, state_configured=bool(os.getenv("X_STORAGE_STATE", "") or os.path.exists(STATE_PATH)))


@app.get("/verify")
def verify():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state=_state())
            page = context.new_page()
            handle = _identity(page)
            _save_state(context.storage_state())
            context.close(); browser.close()
        return jsonify(ok=True, handle=handle, durable=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 503


@app.post("/ingest-state")
def ingest_state():
    if not _auth_ok(request):
        return jsonify(ok=False, error="unauthorized"), 401
    try:
        body = request.get_json(force=True) or {}
        state = body.get("storage_state", body)
        _save_state(state)
        return jsonify(ok=True, stored=True, durable=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/post")
def post():
    if not _auth_ok(request):
        return jsonify(ok=False, error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or "")[:280]
    media_url = str(body.get("media_url") or "")
    if not text or not media_url:
        return jsonify(ok=False, error="text and media_url required"), 400
    try:
        return jsonify(ok=True, **_publish(text, media_url))
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500
