"""Isolated local Anthares-browser backend for the Render control instance.

This browser is a dedicated headless Chromium process inside the Render Linux
instance. It never attaches to a host/user desktop. Playwright storage state is
encrypted locally and persisted in the dedicated /browser-state slot of the
Cloudflare durable vault using the already-established Render->vault signing
identity derived from X_WORKER_TOKEN.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
from typing import Any

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from playwright.sync_api import sync_playwright

_LOCK = threading.RLock()
_PLAYWRIGHT = None
_BROWSER = None
_CONTEXT = None
_PAGE = None
_RESTORE_STATUS = "not_started"
_LAST_PERSIST_OK = None

VAULT_URL = os.getenv(
    "ANTHARES_BROWSER_STATE_VAULT_URL",
    "https://anthares-x-vault.anthares1.workers.dev/browser-state",
)


def _token() -> str:
    return os.getenv("X_WORKER_TOKEN", "")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _enc_key() -> bytes:
    token = _token()
    if not token:
        raise RuntimeError("browser vault signing identity unavailable")
    return hashlib.sha256(("browser-state:" + token).encode()).digest()


def _encrypt_state(state: dict[str, Any]) -> str:
    raw = json.dumps(state, separators=(",", ":")).encode()
    nonce = os.urandom(12)
    cipher = AESGCM(_enc_key()).encrypt(nonce, raw, b"anthares-browser-runtime-state-v1")
    return _b64(nonce + cipher)


def _decrypt_state(ciphertext: str) -> dict[str, Any]:
    blob = _b64d(ciphertext)
    if len(blob) < 29:
        raise RuntimeError("invalid encrypted browser state")
    raw = AESGCM(_enc_key()).decrypt(
        blob[:12], blob[12:], b"anthares-browser-runtime-state-v1"
    )
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cookies", []), list):
        raise RuntimeError("invalid browser storage state")
    if not isinstance(data.get("origins", []), list):
        raise RuntimeError("invalid browser origins state")
    return {"cookies": data.get("cookies", []), "origins": data.get("origins", [])}


def _signed_headers(body: str) -> dict[str, str]:
    import x_render_worker_v3 as xworker

    ts, sig = xworker._signature(body)
    headers = {
        "X-Anthares-Timestamp": ts,
        "X-Anthares-Signature": sig,
    }
    if body:
        headers["Content-Type"] = "application/json"
    return headers


def _vault_pull() -> dict[str, Any] | None:
    if not _token():
        return None
    r = requests.get(VAULT_URL, headers=_signed_headers(""), timeout=20)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    if not data.get("ok") or not data.get("available"):
        return None
    return _decrypt_state(str(data.get("ciphertext") or ""))


def _context_state() -> dict[str, Any]:
    try:
        return _CONTEXT.storage_state(indexed_db=True)
    except TypeError:
        return _CONTEXT.storage_state()


def _persist() -> bool:
    global _LAST_PERSIST_OK
    if not _token() or _CONTEXT is None:
        _LAST_PERSIST_OK = False
        return False
    try:
        ciphertext = _encrypt_state(_context_state())
        body = json.dumps(
            {
                "schema": "anthares.encrypted-browser-state.v1",
                "ciphertext": ciphertext,
                "sha256": hashlib.sha256(ciphertext.encode("ascii")).hexdigest(),
            },
            separators=(",", ":"),
        )
        r = requests.post(VAULT_URL, headers=_signed_headers(body), data=body, timeout=20)
        r.raise_for_status()
        data = r.json()
        _LAST_PERSIST_OK = bool(data.get("ok") and data.get("stored"))
    except Exception:
        _LAST_PERSIST_OK = False
    return bool(_LAST_PERSIST_OK)


def _ensure_browser():
    global _PLAYWRIGHT, _BROWSER, _CONTEXT, _PAGE, _RESTORE_STATUS
    with _LOCK:
        if _CONTEXT is not None:
            try:
                pages = _CONTEXT.pages
                _PAGE = pages[0] if pages else (_PAGE or _CONTEXT.new_page())
                return _CONTEXT, _PAGE
            except Exception:
                _BROWSER = None
                _CONTEXT = None
                _PAGE = None
        if _PLAYWRIGHT is None:
            _PLAYWRIGHT = sync_playwright().start()
        restored = None
        try:
            restored = _vault_pull()
            _RESTORE_STATUS = "restored" if restored else "empty"
        except Exception:
            _RESTORE_STATUS = "vault_unavailable"
        _BROWSER = _PLAYWRIGHT.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-networking",
            ],
        )
        kwargs = {
            "viewport": {"width": 1365, "height": 768},
            "locale": "pt-BR",
            "timezone_id": "America/Campo_Grande",
        }
        if restored:
            kwargs["storage_state"] = restored
        _CONTEXT = _BROWSER.new_context(**kwargs)
        _PAGE = _CONTEXT.new_page()
        return _CONTEXT, _PAGE


def health() -> dict[str, Any]:
    try:
        _, page = _ensure_browser()
        return {
            "configured": True,
            "healthy": True,
            "backend": "local_playwright_vault",
            "isolated": True,
            "headless": True,
            "chromium_running": True,
            "host_desktop_fallback": False,
            "vault_enabled": bool(_token()),
            "restore_status": _RESTORE_STATUS,
            "last_persist_ok": _LAST_PERSIST_OK,
            "url": page.url,
        }
    except Exception as exc:
        return {
            "configured": True,
            "healthy": False,
            "backend": "local_playwright_vault",
            "isolated": True,
            "headless": True,
            "chromium_running": False,
            "host_desktop_fallback": False,
            "vault_enabled": bool(_token()),
            "restore_status": _RESTORE_STATUS,
            "error": type(exc).__name__,
        }


def browser_request(method: str, path: str, payload: dict[str, Any] | None = None):
    data = payload or {}
    try:
        _, page = _ensure_browser()
        if method == "GET" and path == "/status":
            h = health()
            return None, {
                "ok": True,
                "version": "anthares-runtime-browser-local-v2",
                **h,
                "title": page.title(),
            }, 200
        if method == "GET" and path == "/page":
            body = page.locator("body")
            text = body.inner_text(timeout=10000) if body.count() else ""
            return None, {
                "ok": True,
                "url": page.url,
                "title": page.title(),
                "text": text[:50000],
            }, 200
        if method != "POST":
            return None, {"ok": False, "error": "method_not_allowed"}, 405
        if path == "/navigate":
            url = str(data.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                return None, {"ok": False, "error": "invalid_url"}, 400
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            wait_ms = max(0, min(int(data.get("wait_ms") or 0), 30000))
            if wait_ms:
                page.wait_for_timeout(wait_ms)
            persisted = _persist()
            return None, {"ok": True, "url": page.url, "title": page.title(), "state_persisted": persisted}, 200
        if path == "/click":
            selector = str(data.get("selector") or "").strip()
            if not selector:
                return None, {"ok": False, "error": "missing_selector"}, 400
            page.locator(selector).first.click(timeout=30000)
            wait_ms = max(0, min(int(data.get("wait_ms") or 0), 30000))
            if wait_ms:
                page.wait_for_timeout(wait_ms)
            persisted = _persist()
            return None, {"ok": True, "url": page.url, "title": page.title(), "state_persisted": persisted}, 200
        if path == "/type":
            selector = str(data.get("selector") or "").strip()
            value = str(data.get("text") if data.get("text") is not None else data.get("value") or "")
            if not selector:
                return None, {"ok": False, "error": "missing_selector"}, 400
            locator = page.locator(selector).first
            if bool(data.get("clear", True)):
                locator.fill(value, timeout=30000)
            else:
                locator.press_sequentially(value, timeout=30000)
            wait_ms = max(0, min(int(data.get("wait_ms") or 0), 30000))
            if wait_ms:
                page.wait_for_timeout(wait_ms)
            persisted = _persist()
            return None, {"ok": True, "state_persisted": persisted}, 200
        if path == "/wait":
            selector = str(data.get("selector") or "").strip()
            if not selector:
                return None, {"ok": False, "error": "missing_selector"}, 400
            timeout_ms = max(100, min(int(data.get("timeout_ms") or 10000), 120000))
            state = "visible" if bool(data.get("visible", True)) else "attached"
            page.locator(selector).first.wait_for(state=state, timeout=timeout_ms)
            return None, {"ok": True}, 200
        if path == "/evaluate":
            expression = str(data.get("expression") or data.get("script") or "").strip()
            if not expression:
                return None, {"ok": False, "error": "missing_expression"}, 400
            result = page.evaluate(expression)
            persisted = _persist()
            return None, {"ok": True, "result": result, "state_persisted": persisted}, 200
        return None, {"ok": False, "error": "not_found"}, 404
    except Exception as exc:
        return None, {
            "ok": False,
            "error": "browser_operation_failed",
            "detail": type(exc).__name__,
        }, 500
