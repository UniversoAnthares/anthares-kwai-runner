"""Browser-session control bridge for Anthares Remote Agent.

A one-time bootstrap code mints a signed HttpOnly cookie. After that, Browserless can
operate the user's authorized PC without placing the long-lived control secret in tool calls.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time

from flask import Response, jsonify, make_response, request

import anthares_remote_control_routes as _relay

_COOKIE = "ara_control"
_BOOTSTRAP_CODE = os.getenv("ARA_BROWSER_BOOTSTRAP_CODE", "")
_CONTROL_SECRET = os.getenv("ARA_SHARED", "")
_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAP_USED = False


def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload):
    return _b64(hmac.new(_CONTROL_SECRET.encode(), payload, hashlib.sha256).digest())


def _mint_cookie(ttl=30 * 24 * 3600):
    payload = json.dumps({"exp": int(time.time()) + ttl, "nonce": secrets.token_hex(12)}, separators=(",", ":")).encode()
    return _b64(payload) + "." + _sign(payload)


def _cookie_ok():
    if not _CONTROL_SECRET:
        return False
    raw = request.cookies.get(_COOKIE, "")
    try:
        p64, sig = raw.split(".", 1)
        payload = _b64d(p64)
        if not hmac.compare_digest(sig, _sign(payload)):
            return False
        data = json.loads(payload.decode("utf-8"))
        return int(data.get("exp", 0)) > int(time.time())
    except Exception:
        return False


def _state(device):
    return _relay._DEVICES.setdefault(device, {"heartbeat": None, "queue": [], "jobs": {}})


def _enqueue(device, job_type, args, timeout):
    job_id = secrets.token_hex(16)
    job = {
        "id": job_id,
        "type": job_type,
        "args": args or {},
        "timeout_seconds": max(1, min(int(timeout or 30), 120)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "queued",
    }
    with _relay._LOCK:
        s = _state(device)
        s["jobs"][job_id] = job
        s["queue"].append(job_id)
    return job


def _wait(device, job_id, seconds):
    deadline = time.time() + max(1, min(float(seconds), 130.0))
    while time.time() < deadline:
        with _relay._LOCK:
            job = _state(device)["jobs"].get(job_id)
            if not job:
                return None
            if job.get("status") in ("done", "failed"):
                return dict(job)
        time.sleep(0.20)
    with _relay._LOCK:
        job = _state(device)["jobs"].get(job_id)
        return dict(job) if job else None


def register(app):
    @app.get("/v1/browser/bootstrap")
    def ara_browser_bootstrap():
        global _BOOTSTRAP_USED
        supplied = request.args.get("code", "")
        with _BOOTSTRAP_LOCK:
            if _BOOTSTRAP_USED or not _BOOTSTRAP_CODE or not secrets.compare_digest(supplied, _BOOTSTRAP_CODE):
                return jsonify(ok=False, error="not_available"), 404
            _BOOTSTRAP_USED = True
        resp = make_response(jsonify(ok=True, session="created"))
        resp.set_cookie(_COOKIE, _mint_cookie(), max_age=30 * 24 * 3600, httponly=True, secure=True, samesite="Strict", path="/v1/browser")
        return resp

    @app.get("/v1/browser/status")
    def ara_browser_status():
        if not _cookie_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        device = request.args.get("device_id", "DESKTOP-FTDK0HP").strip()
        with _relay._LOCK:
            hb = _state(device).get("heartbeat")
        return jsonify(ok=True, device_id=device, connected=bool(hb), heartbeat=hb)

    @app.post("/v1/browser/execute")
    def ara_browser_execute():
        if not _cookie_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "DESKTOP-FTDK0HP").strip()
        job_type = str(body.get("type") or "").strip()
        timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        if not job_type:
            return jsonify(ok=False, error="missing_type"), 400
        job = _enqueue(device, job_type, body.get("args") or {}, timeout)
        finished = _wait(device, job["id"], timeout + 8)
        if not finished:
            return jsonify(ok=False, error="job_lost"), 503
        if finished.get("status") not in ("done", "failed"):
            return jsonify(ok=False, status=finished.get("status"), job_id=job["id"], error="timeout_waiting_for_device"), 504
        result = finished.get("result") or {}
        return jsonify(ok=bool(result.get("ok")), status=finished.get("status"), job_id=job["id"], output=result.get("output"), error=result.get("error"), started_at=result.get("started_at"), ended_at=result.get("ended_at")), (200 if result.get("ok") else 500)

    @app.post("/v1/browser/screenshot")
    def ara_browser_screenshot():
        if not _cookie_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "DESKTOP-FTDK0HP").strip()
        display = str(body.get("display") if body.get("display") is not None else "0")
        job = _enqueue(device, "screenshot", {"display": display}, 45)
        finished = _wait(device, job["id"], 53)
        result = (finished or {}).get("result") or {}
        if not result.get("ok"):
            return jsonify(ok=False, error=result.get("error") or "screenshot_failed"), 500
        try:
            data = base64.b64decode(result.get("output") or "", validate=True)
        except Exception:
            return jsonify(ok=False, error="invalid_screenshot"), 500
        return Response(data, mimetype="image/jpeg", headers={"Cache-Control":"no-store"})
