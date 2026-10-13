"""Cookie-authenticated Browserless bridge for Anthares Remote Agent."""
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
_PENDING_COOKIE = "ara_pending"
_CONTROL_SECRET = os.getenv("ARA_SHARED", "")
_CLAIM_LOCK = threading.Lock()
_CLAIMED = set()


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


def register(app):
    @app.get("/v1/browser/challenge")
    def ara_browser_challenge():
        challenge_id = secrets.token_hex(16)
        resp = make_response(jsonify(ok=True, challenge_id=challenge_id, expires_in=600))
        resp.set_cookie(_PENDING_COOKIE, challenge_id, max_age=600, httponly=True, secure=True, samesite="Strict", path="/v1/browser")
        return resp

    @app.get("/v1/browser/claim")
    def ara_browser_claim():
        challenge_id = request.cookies.get(_PENDING_COOKIE, "")
        approved = os.getenv("ARA_BROWSER_APPROVED_CHALLENGE", "")
        with _CLAIM_LOCK:
            valid = bool(challenge_id and approved and challenge_id not in _CLAIMED and secrets.compare_digest(challenge_id, approved))
            if valid:
                _CLAIMED.add(challenge_id)
        if not valid:
            return jsonify(ok=False, error="not_approved"), 403
        resp = make_response(jsonify(ok=True, session="created"))
        resp.set_cookie(_COOKIE, _mint_cookie(), max_age=30 * 24 * 3600, httponly=True, secure=True, samesite="Strict", path="/v1/browser")
        resp.delete_cookie(_PENDING_COOKIE, path="/v1/browser")
        return resp

    @app.get("/v1/browser/status")
    def ara_browser_status():
        if not _cookie_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        device = request.args.get("device_id", "DESKTOP-FTDK0HP").strip()
        status = _relay.device_status(device)
        return jsonify(ok=True, device_id=device, **status)

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
        finished = _relay.execute_job(device, job_type, body.get("args") or {}, timeout, body.get("idempotency_key"))
        if not finished:
            return jsonify(ok=False, error="job_lost"), 503
        if finished.get("status") not in ("done", "failed"):
            return jsonify(ok=False, status=finished.get("status"), job_id=finished.get("id"), error="timeout_waiting_for_device"), 504
        result = finished.get("result") or {}
        return jsonify(ok=bool(result.get("ok")), status=finished.get("status"), job_id=finished.get("id"), output=result.get("output"), error=result.get("error"), started_at=result.get("started_at"), ended_at=result.get("ended_at")), (200 if result.get("ok") else 500)

    @app.post("/v1/browser/screenshot")
    def ara_browser_screenshot():
        if not _cookie_ok():
            return jsonify(ok=False, error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "DESKTOP-FTDK0HP").strip()
        display = str(body.get("display") if body.get("display") is not None else "0")
        finished = _relay.execute_job(device, "screenshot", {"display": display}, 45)
        result = (finished or {}).get("result") or {}
        if not result.get("ok"):
            return jsonify(ok=False, error=result.get("error") or "screenshot_failed"), 500
        try:
            data = base64.b64decode(result.get("output") or "", validate=True)
        except Exception:
            return jsonify(ok=False, error="invalid_screenshot"), 500
        return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
