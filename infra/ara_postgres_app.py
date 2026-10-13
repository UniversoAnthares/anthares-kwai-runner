import hashlib
import os
import secrets
import time

import requests
from flask import Flask, jsonify, request
import ara_postgres_store as store

app = Flask(__name__)
CONTROL_TOKEN = os.getenv("ANTHARES_REMOTE_CONTROL_TOKEN", "")
DEVICE_HASH_BASE = os.getenv("ARA_DEVICE_HASH_BASE", "https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices")
_HASH_CACHE = {}
_HASH_TTL = 60


def bearer():
    value = request.headers.get("Authorization", "")
    return value[7:] if value.startswith("Bearer ") else ""


def control_ok():
    got = bearer()
    return bool(CONTROL_TOKEN and got) and secrets.compare_digest(got, CONTROL_TOKEN)


def device_id():
    return request.headers.get("X-Anthares-Device", "").strip()


def device_ok(device):
    if not device or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in device):
        return False
    env_key = "ARA_DEVICE_HASH_" + "".join(c if c.isalnum() else "_" for c in device.upper())
    expected = os.getenv(env_key, "").strip().lower()
    if not (len(expected) == 64 and all(c in "0123456789abcdef" for c in expected)):
        cached = _HASH_CACHE.get(device)
        if cached and time.time() - cached[1] < _HASH_TTL:
            expected = cached[0]
        else:
            try:
                response = requests.get(f"{DEVICE_HASH_BASE}/{device}.sha256", timeout=6)
                expected = response.text.strip().lower() if response.ok else ""
                if len(expected) == 64 and all(c in "0123456789abcdef" for c in expected):
                    _HASH_CACHE[device] = (expected, time.time())
                else:
                    expected = ""
            except requests.RequestException:
                expected = ""
    got = bearer()
    actual = hashlib.sha256(got.encode()).hexdigest() if got else ""
    return bool(expected and actual) and secrets.compare_digest(actual, expected)


@app.get("/healthz")
def health():
    try:
        with store.connection() as conn:
            conn.execute("SELECT 1")
        return jsonify(ok=True, database="connected")
    except Exception:
        app.logger.exception("ARA health check failed")
        return jsonify(ok=False, database="unavailable"), 503


@app.post("/v1/device/heartbeat")
def heartbeat():
    device = device_id()
    if not device_ok(device):
        return jsonify(error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    body["seen_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store.heartbeat(device, body)
    return jsonify(ok=True)


@app.get("/v1/device/jobs/next")
def next_job():
    device = device_id()
    if not device_ok(device):
        return jsonify(error="unauthorized"), 401
    job = store.lease_next(device)
    return (jsonify(job=job), 200) if job else ("", 204)


@app.post("/v1/device/jobs/<job_id>/result")
def result(job_id):
    device = device_id()
    if not device_ok(device):
        return jsonify(error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    if not store.submit_result(device, job_id, body):
        return jsonify(error="unknown_job_or_wrong_device"), 404
    return jsonify(ok=True)


@app.post("/v1/control/jobs")
def create_job():
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    device = str(body.get("device_id") or "").strip()
    job_type = str(body.get("type") or "").strip()
    if not device or not job_type:
        return jsonify(error="missing_device_id_or_type"), 400
    timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
    return jsonify(ok=True, job=store.create_job(device, job_type, body.get("args") or {}, timeout)), 201


@app.get("/v1/control/jobs/<job_id>")
def get_job(job_id):
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    device = request.args.get("device_id", "").strip()
    if not device:
        return jsonify(error="missing_device_id"), 400
    job = store.get_job(device, job_id)
    return jsonify(job=job), 200 if job else 404


@app.get("/v1/control/status")
def status():
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    device = request.args.get("device_id", "").strip()
    if not device:
        return jsonify(error="missing_device_id"), 400
    return jsonify(store.device_status(device))


try:
    store.initialize()
except Exception:
    # Keep the process importable; healthz reports database errors and no job route can
    # falsely claim success without a working persistent database.
    app.logger.exception("ARA PostgreSQL initialization failed")
