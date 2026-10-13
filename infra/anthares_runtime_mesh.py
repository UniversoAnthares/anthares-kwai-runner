"""Unified Anthares runtime surface.

Anthares-control remains the authority for global routing and operation leases.
This module joins Anthares Remote and the isolated Anthares-browser behind one
fail-closed API. The browser lease here is only a local execution fence for one
Chromium profile; it is subordinate to the global anthares-control lease and
never becomes a second control plane.
"""
from __future__ import annotations

import os
import secrets
import threading
import time
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


def _browser_ready() -> dict[str, Any]:
    url, _ = _browser_cfg()
    if not url:
        return {"configured": False, "healthy": False, "error": "browser_not_configured"}
    try:
        r = requests.get(url + "/health", timeout=8)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return {
            "configured": True,
            "healthy": bool(r.ok and body.get("ok") and body.get("cdp_ready")),
            "status": r.status_code,
            "cdp_ready": bool(body.get("cdp_ready")),
            "chromium_running": bool(body.get("chromium_running")),
        }
    except Exception as exc:
        return {"configured": True, "healthy": False, "error": type(exc).__name__}


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


def _browser_request(method: str, path: str, payload: dict[str, Any] | None = None):
    url, token = _browser_cfg()
    if not url or not token:
        return None, {"ok": False, "error": "browser_not_configured"}, 503
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
