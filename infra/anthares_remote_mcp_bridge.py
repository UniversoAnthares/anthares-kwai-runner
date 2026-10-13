"""Authenticated Ed25519 bridge used only by the Anthares remote MCP service."""
import base64
import json
import secrets
import threading
import time

import requests
from flask import jsonify, request
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

import anthares_remote_control_routes as _relay

_SIGNER = "anthares-remote-mcp"
_KEY_URL = "https://anthares-remote-mcp.onrender.com/.well-known/ara-control-key"
_KEY_TTL = 60
_MAX_SKEW_MS = 30000
_LOCK = threading.Lock()
_KEY_CACHE = {"key": None, "at": 0.0}
_REPLAY = {}


def _public_key():
    now = time.time()
    with _LOCK:
        if _KEY_CACHE["key"] is not None and now - _KEY_CACHE["at"] < _KEY_TTL:
            return _KEY_CACHE["key"]
    r = requests.get(_KEY_URL, timeout=6, headers={"User-Agent": "AntharesRemoteControl/0.4"})
    r.raise_for_status()
    raw = r.content
    if len(raw) > 4096:
        raise ValueError("service key too large")
    key = serialization.load_pem_public_key(raw)
    with _LOCK:
        _KEY_CACHE["key"] = key
        _KEY_CACHE["at"] = now
    return key


def _b64decode(value):
    value = str(value or "")
    value += "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))


def _canonical_path():
    qs = request.query_string.decode("ascii", errors="strict")
    return request.path + (("?" + qs) if qs else "")


def _verify():
    if request.headers.get("X-ARA-Signer", "") != _SIGNER:
        return False, b""
    ts = request.headers.get("X-ARA-Timestamp", "")
    sig = request.headers.get("X-ARA-Signature", "")
    try:
        ts_num = int(ts)
    except Exception:
        return False, b""
    now_ms = int(time.time() * 1000)
    if abs(now_ms - ts_num) > _MAX_SKEW_MS:
        return False, b""
    raw = request.get_data(cache=True) or b""
    if len(raw) > 3 * 1024 * 1024:
        return False, b""
    try:
        signature = _b64decode(sig)
    except Exception:
        return False, b""
    replay_key = secrets.token_hex(0) + sig
    with _LOCK:
        cutoff = time.time() - 60
        for key, seen in list(_REPLAY.items()):
            if seen < cutoff:
                _REPLAY.pop(key, None)
        if replay_key in _REPLAY:
            return False, b""
    payload = (ts + "\n" + request.method.upper() + "\n" + _canonical_path() + "\n").encode("utf-8") + raw
    try:
        _public_key().verify(signature, payload)
    except (InvalidSignature, ValueError, TypeError, requests.RequestException):
        return False, b""
    with _LOCK:
        _REPLAY[replay_key] = time.time()
    return True, raw


def register(app):
    @app.get("/v1/mcp/status")
    def ara_mcp_status():
        ok, _ = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        device = request.args.get("device_id", "").strip()
        if not device:
            return jsonify(error="missing_device_id"), 400
        return jsonify(**_relay.device_status(device))

    @app.get("/v1/mcp/capabilities")
    def ara_mcp_capabilities():
        ok, _ = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        return jsonify(
            ok=True,
            protocol="anthares-remote-agent/0.4",
            auth="ed25519-service-signature",
            replay_protection=True,
            capabilities=[
                "status", "system_info", "shell", "process_list", "process_start", "process_kill",
                "service_status", "service_start", "service_stop", "clipboard_get", "clipboard_set",
                "screenshot", "file_stat", "file_list", "file_read", "file_write", "file_read_chunk",
                "file_write_chunk", "file_mkdir", "file_remove", "file_rename", "file_copy", "file_sha256",
                "file_write_atomic", "job_start", "job_list", "job_status", "job_logs", "job_cancel"
            ],
        )

    @app.post("/v1/mcp/execute")
    def ara_mcp_execute():
        ok, raw = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return jsonify(error="invalid_json"), 400
        device = str(body.get("device_id") or "").strip()
        job_type = str(body.get("type") or "").strip()
        if not device or not job_type:
            return jsonify(error="missing_device_id_or_type"), 400
        try:
            timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        except Exception:
            return jsonify(error="invalid_timeout"), 400
        job = _relay.execute_job(device, job_type, body.get("args") or {}, timeout, body.get("idempotency_key"))
        if not job:
            return jsonify(error="job_lost"), 503
        if job.get("status") not in ("done", "failed"):
            return jsonify(ok=False, status=job.get("status"), job_id=job.get("id"), error="timeout_waiting_for_device"), 504
        result = job.get("result") or {}
        return jsonify(
            ok=bool(result.get("ok")), status=job.get("status"), job_id=job.get("id"),
            output=result.get("output"), error=result.get("error"),
            started_at=result.get("started_at"), ended_at=result.get("ended_at")
        ), (200 if result.get("ok") else 500)
