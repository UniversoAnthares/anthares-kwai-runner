import hashlib
import os
import secrets
import threading
import time

import requests
from flask import jsonify, request

_LOCK = threading.Lock()
_DEVICES = {}
_DEVICE_HASH_CACHE = {}
_DEVICE_HASH_TTL = 60
_DEVICE_HASH_BASE = "https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices"


def register(app, control_token):
    control_token = str(control_token or "")

    def bearer():
        header = request.headers.get("Authorization", "")
        return header[7:] if header.startswith("Bearer ") else ""

    def control_auth_ok():
        got = bearer()
        return bool(control_token and got) and secrets.compare_digest(got, control_token)

    def device_id():
        return request.headers.get("X-Anthares-Device", "").strip()

    def valid_hash(value):
        return len(value) == 64 and all(c in "0123456789abcdef" for c in value)

    def expected_device_hash(device):
        if not device or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in device):
            return ""
        env_name = "ARA_DEVICE_HASH_" + "".join(c if c.isalnum() else "_" for c in device.upper())
        env_value = os.getenv(env_name, "").strip().lower()
        if valid_hash(env_value):
            return env_value
        now = time.time()
        cached = _DEVICE_HASH_CACHE.get(device)
        if cached and now - cached[1] < _DEVICE_HASH_TTL:
            return cached[0]
        try:
            r = requests.get(f"{_DEVICE_HASH_BASE}/{device}.sha256", timeout=8)
            if not r.ok:
                return ""
            value = r.text.strip().lower()
            if not valid_hash(value):
                return ""
            _DEVICE_HASH_CACHE[device] = (value, now)
            return value
        except Exception:
            return ""

    def device_auth_ok(device):
        got = bearer()
        expected = expected_device_hash(device)
        if not got or not expected:
            return False
        actual = hashlib.sha256(got.encode("utf-8")).hexdigest()
        return secrets.compare_digest(actual, expected)

    def state(device):
        return _DEVICES.setdefault(device, {"heartbeat": None, "queue": [], "jobs": {}})

    @app.post("/v1/device/heartbeat")
    def ara_heartbeat():
        device = device_id()
        if not device_auth_ok(device):
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        body["seen_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with _LOCK:
            state(device)["heartbeat"] = body
        return jsonify(ok=True)

    @app.get("/v1/device/jobs/next")
    def ara_next_job():
        device = device_id()
        if not device_auth_ok(device):
            return jsonify(error="unauthorized"), 401
        with _LOCK:
            s = state(device)
            while s["queue"]:
                job_id = s["queue"].pop(0)
                job = s["jobs"].get(job_id)
                if not job or job.get("status") != "queued":
                    continue
                job["status"] = "leased"
                return jsonify(job=job)
        return ("", 204)

    @app.post("/v1/device/jobs/<job_id>/result")
    def ara_result(job_id):
        device = device_id()
        if not device_auth_ok(device):
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        with _LOCK:
            job = state(device)["jobs"].get(job_id)
            if not job:
                return jsonify(error="unknown_job"), 404
            job["result"] = body
            job["status"] = "done" if bool(body.get("ok")) else "failed"
        return jsonify(ok=True)

    @app.post("/v1/control/jobs")
    def ara_create_job():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "").strip()
        job_type = str(body.get("type") or "").strip()
        if not device or not job_type:
            return jsonify(error="missing_device_id_or_type"), 400
        timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        job_id = secrets.token_hex(16)
        job = {
            "id": job_id,
            "type": job_type,
            "args": body.get("args") or {},
            "timeout_seconds": timeout,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "queued",
        }
        with _LOCK:
            s = state(device)
            s["jobs"][job_id] = job
            s["queue"].append(job_id)
        return jsonify(ok=True, job=job), 201

    @app.get("/v1/control/jobs/<job_id>")
    def ara_get_job(job_id):
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        device = request.args.get("device_id", "").strip()
        if not device:
            return jsonify(error="missing_device_id"), 400
        with _LOCK:
            job = state(device)["jobs"].get(job_id)
            if not job:
                return jsonify(error="not_found"), 404
            return jsonify(job=job)

    @app.get("/v1/control/status")
    def ara_status():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        device = request.args.get("device_id", "").strip()
        if not device:
            return jsonify(error="missing_device_id"), 400
        with _LOCK:
            s = state(device)
            return jsonify(heartbeat=s["heartbeat"], queued=len(s["queue"]))
