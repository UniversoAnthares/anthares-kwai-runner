"""Unified Anthares runtime surface.

Anthares-control remains the authority for global routing and operation leases.
This module joins Anthares Remote and the isolated Anthares-browser behind one
fail-closed API. The browser lease here is only a local execution fence for one
Chromium profile; it is subordinate to the global anthares-control lease and
never becomes a second control plane.

If ANTHARES_BROWSER_URL is unset, the Render service runs a dedicated headless
Playwright/Chromium profile inside its own Linux instance. It never attaches to
or controls the user's desktop browser, mouse, keyboard, tabs, or windows.
"""
from __future__ import annotations

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

import requests
from flask import jsonify, request

import anthares_remote_control_routes as _remote

_LOCK = threading.RLock()
_BROWSER_LEASE: dict[str, Any] = {
    "owner": None,
    "token": None,
    "generation": 0,
    "expires_at": 0.0,
}
_LOCAL_PLAYWRIGHT = None
_LOCAL_CONTEXT = None
_LOCAL_PAGE = None


def _now() -> float:
    return time.time()


def _auth_ok() -> bool:
    secret = os.getenv("ARA_SHARED", "")
    supplied = request.headers.get("Authorization", "")
    return bool(secret) and secrets.compare_digest(supplied, "Bearer " + secret)


def _browser_cfg() -> tuple[str, str]:
    return (
        os.getenv("ANTHARES_BROWSER_URL", "").rstrip("/"),
        os.getenv("ANTHARES_BROWSER_TOKEN", ""),
    )


def _local_profile_dir() -> str:
    path = Path(os.getenv("ANTHARES_BROWSER_PROFILE_DIR", "/tmp/anthares-browser-profile"))
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _local_browser():
    global _LOCAL_PLAYWRIGHT, _LOCAL_CONTEXT, _LOCAL_PAGE
    with _LOCK:
        if _LOCAL_CONTEXT is not None:
            try:
                pages = _LOCAL_CONTEXT.pages
                if pages:
                    _LOCAL_PAGE = pages[0]
                elif _LOCAL_PAGE is None:
                    _LOCAL_PAGE = _LOCAL_CONTEXT.new_page()
                return _LOCAL_CONTEXT, _LOCAL_PAGE
            except Exception:
                _LOCAL_CONTEXT = None
                _LOCAL_PAGE = None
        from playwright.sync_api import sync_playwright
        if _LOCAL_PLAYWRIGHT is None:
            _LOCAL_PLAYWRIGHT = sync_playwright().start()
        _LOCAL_CONTEXT = _LOCAL_PLAYWRIGHT.chromium.launch_persistent_context(
            _local_profile_dir(),
            headless=True,
            viewport={"width": 1365, "height": 768},
            locale="pt-BR",
            timezone_id="America/Campo_Grande",
            args=[
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-networking",
            ],
        )
        _LOCAL_PAGE = _LOCAL_CONTEXT.pages[0] if _LOCAL_CONTEXT.pages else _LOCAL_CONTEXT.new_page()
        return _LOCAL_CONTEXT, _LOCAL_PAGE


def _local_browser_status() -> dict[str, Any]:
    try:
        _, page = _local_browser()
        return {
            "configured": True,
            "healthy": True,
            "backend": "local_playwright",
            "isolated": True,
            "headless": True,
            "chromium_running": True,
            "host_desktop_fallback": False,
            "url": page.url,
        }
    except Exception as exc:
        return {
            "configured": True,
            "healthy": False,
            "backend": "local_playwright",
            "isolated": True,
            "headless": True,
            "chromium_running": False,
            "host_desktop_fallback": False,
            "error": type(exc).__name__,
        }


def _browser_ready() -> dict[str, Any]:
    url, _ = _browser_cfg()
    if not url:
        return _local_browser_status()
    try:
        r = requests.get(url + "/health", timeout=8)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return {
            "configured": True,
            "healthy": bool(r.ok and body.get("ok") and body.get("cdp_ready")),
            "backend": "external_anthares_browser",
            "status": r.status_code,
            "cdp_ready": bool(body.get("cdp_ready")),
            "chromium_running": bool(body.get("chromium_running")),
            "isolated": True,
            "host_desktop_fallback": False,
        }
    except Exception as exc:
        return {
            "configured": True,
            "healthy": False,
            "backend": "external_anthares_browser",
            "error": type(exc).__name__,
            "isolated": True,
            "host_desktop_fallback": False,
        }


def _lease_snapshot() -> dict[str, Any]:
    with _LOCK:
        active = bool(_BROWSER_LEASE["token"] and _BROWSER_LEASE["expires_at"] > _now())
        if not active:
            _BROWSER_LEASE["owner"] = None
            _BROWSER_LEASE["token"] = None
            _BROWSER_LEASE["expires_at"] = 0.0
        return {
            "active": active,
            "owner": _BROWSER_LEASE["owner"] if active else None,
            "generation": int(_BROWSER_LEASE["generation"]),
            "expires_at": _BROWSER_LEASE["expires_at"] if active else None,
            "scope": "local_browser_profile_fence",
        }


def _lease_required() -> tuple[bool, str]:
    token = request.headers.get("X-Anthares-Lease-Token", "")
    try:
        generation = int(request.headers.get("X-Anthares-Lease-Generation", "0"))
    except ValueError:
        return False, "invalid_generation"
    with _LOCK:
        if not _BROWSER_LEASE["token"] or _BROWSER_LEASE["expires_at"] <= _now():
            return False, "lease_expired"
        if generation != int(_BROWSER_LEASE["generation"]):
            return False, "stale_generation"
        if not secrets.compare_digest(token, str(_BROWSER_LEASE["token"])):
            return False, "invalid_lease_token"
    return True, ""


def _local_browser_request(method: str, path: str, payload: dict[str, Any] | None = None):
    data = payload or {}
    try:
        _, page = _local_browser()
        if method == "GET" and path == "/status":
            return None, {
                "ok": True,
                "version": "runtime-local-playwright-v1",
                "backend": "local_playwright",
                "isolated": True,
                "headless": True,
                "host_desktop_fallback": False,
                "url": page.url,
                "title": page.title(),
                "profile_dir": "isolated-runtime-profile",
            }, 200
        if method == "GET" and path == "/page":
            text = page.locator("body").inner_text(timeout=10000) if page.locator("body").count() else ""
            return None, {"ok": True, "url": page.url, "title": page.title(), "text": text[:50000]}, 200
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
            return None, {"ok": True, "url": page.url, "title": page.title()}, 200
        if path == "/click":
            selector = str(data.get("selector") or "").strip()
            if not selector:
                return None, {"ok": False, "error": "missing_selector"}, 400
            page.locator(selector).first.click(timeout=30000)
            wait_ms = max(0, min(int(data.get("wait_ms") or 0), 30000))
            if wait_ms:
                page.wait_for_timeout(wait_ms)
            return None, {"ok": True, "url": page.url, "title": page.title()}, 200
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
            return None, {"ok": True}, 200
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
            return None, {"ok": True, "result": page.evaluate(expression)}, 200
        return None, {"ok": False, "error": "not_found"}, 404
    except Exception as exc:
        return None, {"ok": False, "error": "browser_operation_failed", "detail": type(exc).__name__}, 500


def _browser_request(method: str, path: str, payload: dict[str, Any] | None = None):
    url, token = _browser_cfg()
    if not url:
        return _local_browser_request(method, path, payload)
    if not token:
        return None, {"ok": False, "error": "browser_token_not_configured"}, 503
    try:
        r = requests.request(
            method,
            url + path,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            json=payload if payload is not None else None,
            timeout=45,
        )
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:20000]}
        return r, body, r.status_code
    except Exception as exc:
        return None, {"ok": False, "error": "browser_unreachable", "detail": type(exc).__name__}, 503


def _legacy_state(device: str):
    return _remote._DEVICES.setdefault(device, {"heartbeat": None, "queue": [], "jobs": {}})


def _legacy_enqueue(device: str, job_type: str, args: dict[str, Any], timeout: int):
    job_id = secrets.token_hex(16)
    job = {
        "id": job_id,
        "type": job_type,
        "args": args,
        "timeout_seconds": max(1, min(timeout, 120)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "queued",
    }
    with _remote._LOCK:
        state = _legacy_state(device)
        state["jobs"][job_id] = job
        state["queue"].append(job_id)
    return job


def _legacy_wait(device: str, job_id: str, seconds: int):
    deadline = _now() + min(max(seconds, 1), 130)
    while _now() < deadline:
        with _remote._LOCK:
            job = _legacy_state(device)["jobs"].get(job_id)
            if job and job.get("status") in ("done", "failed"):
                return dict(job)
        time.sleep(0.2)
    with _remote._LOCK:
        job = _legacy_state(device)["jobs"].get(job_id)
        return dict(job) if job else None


def _remote_connected(device: str) -> bool:
    status_fn = getattr(_remote, "device_status", None)
    if callable(status_fn):
        try:
            return bool((status_fn(device) or {}).get("connected"))
        except Exception:
            return False
    with _remote._LOCK:
        return bool(_legacy_state(device).get("heartbeat"))


def _remote_execute(device: str, job_type: str, args: dict[str, Any], timeout: int):
    durable_execute = getattr(_remote, "execute_job", None)
    if callable(durable_execute):
        return durable_execute(device, job_type, args, timeout)
    job = _legacy_enqueue(device, job_type, args, timeout)
    return _legacy_wait(device, job["id"], timeout + 8)


def register(app):
    @app.get("/v1/runtime/health")
    def runtime_health():
        device = request.args.get("device_id", "DESKTOP-FTDK0HP").strip()
        return jsonify(
            ok=True,
            service="anthares-runtime-mesh",
            control_authority="anthares-control/cloudflare",
            global_lease_authority="anthares-control/cloudflare",
            remote={"device_id": device, "connected": _remote_connected(device)},
            browser=_browser_ready(),
            browser_lease=_lease_snapshot(),
            host_desktop_fallback=False,
        )

    @app.post("/v1/runtime/remote/execute")
    def runtime_remote_execute():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "DESKTOP-FTDK0HP").strip()
        job_type = str(body.get("type") or "").strip()
        timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        if not job_type:
            return jsonify(ok=False, error="missing_type"), 400
        finished = _remote_execute(device, job_type, body.get("args") or {}, timeout)
        if not finished:
            return jsonify(ok=False, error="job_lost"), 503
        if finished.get("status") not in ("done", "failed"):
            return jsonify(ok=False, error="timeout_waiting_for_device", job_id=finished.get("id"), status=finished.get("status")), 504
        result = finished.get("result") or {}
        return jsonify(
            ok=bool(result.get("ok")),
            status=finished.get("status"),
            job_id=finished.get("id"),
            output=result.get("output"),
            error=result.get("error"),
        ), (200 if result.get("ok") else 500)

    @app.post("/v1/runtime/browser/lease/acquire")
    def browser_lease_acquire():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        owner = str(body.get("owner") or "").strip()
        ttl = max(15, min(int(body.get("ttl_seconds") or 300), 1800))
        if not owner:
            return jsonify(ok=False, error="missing_owner"), 400
        with _LOCK:
            active = bool(_BROWSER_LEASE["token"] and _BROWSER_LEASE["expires_at"] > _now())
            if active and _BROWSER_LEASE["owner"] != owner:
                return jsonify(ok=False, error="lease_conflict", lease=_lease_snapshot()), 409
            if not active:
                _BROWSER_LEASE["generation"] += 1
                _BROWSER_LEASE["token"] = secrets.token_urlsafe(32)
                _BROWSER_LEASE["owner"] = owner
            _BROWSER_LEASE["expires_at"] = _now() + ttl
            return jsonify(ok=True, token=_BROWSER_LEASE["token"], generation=_BROWSER_LEASE["generation"], expires_at=_BROWSER_LEASE["expires_at"], scope="local_browser_profile_fence")

    @app.post("/v1/runtime/browser/lease/renew")
    def browser_lease_renew():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        ok, error = _lease_required()
        if not ok:
            return jsonify(ok=False, error=error), 409
        body = request.get_json(silent=True) or {}
        ttl = max(15, min(int(body.get("ttl_seconds") or 300), 1800))
        with _LOCK:
            _BROWSER_LEASE["expires_at"] = _now() + ttl
        return jsonify(ok=True, lease=_lease_snapshot())

    @app.post("/v1/runtime/browser/lease/release")
    def browser_lease_release():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        ok, error = _lease_required()
        if not ok:
            return jsonify(ok=False, error=error), 409
        with _LOCK:
            _BROWSER_LEASE["owner"] = None
            _BROWSER_LEASE["token"] = None
            _BROWSER_LEASE["expires_at"] = 0.0
        return jsonify(ok=True, generation=_BROWSER_LEASE["generation"])

    @app.get("/v1/runtime/browser/status")
    def browser_status():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        _, body, code = _browser_request("GET", "/status")
        return jsonify(body), code

    @app.get("/v1/runtime/browser/page")
    def browser_page():
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        _, body, code = _browser_request("GET", "/page")
        return jsonify(body), code

    @app.route("/v1/runtime/browser/<op>", methods=["POST"])
    def browser_mutation(op: str):
        if not _auth_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        allowed = {"navigate", "click", "type", "wait", "evaluate"}
        if op not in allowed:
            return jsonify(ok=False, error="unsupported_browser_operation"), 404
        ok, error = _lease_required()
        if not ok:
            return jsonify(ok=False, error=error), 409
        _, body, code = _browser_request("POST", "/" + op, request.get_json(silent=True) or {})
        return jsonify(body), code
