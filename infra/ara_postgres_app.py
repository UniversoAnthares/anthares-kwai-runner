import hashlib
import json
import os
import secrets
import time

import requests
from flask import Flask, jsonify, request

import ara_postgres_store as store
from ara_postgres_mcp_bridge import register as register_mcp

app = Flask(__name__)
register_mcp(app)
CONTROL_TOKEN = os.getenv("ANTHARES_REMOTE_CONTROL_TOKEN", "")
DEVICE_HASH_BASE = os.getenv(
    "ARA_DEVICE_HASH_BASE",
    "https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices",
)
_HASH_CACHE = {}
_HASH_TTL = 60
_STARTUP_SELFTEST = {"ok": False, "error": "not_run"}


def bearer():
    value = request.headers.get("Authorization", "")
    return value[7:] if value.startswith("Bearer ") else ""


def control_ok():
    got = bearer()
    return bool(CONTROL_TOKEN and got) and secrets.compare_digest(got, CONTROL_TOKEN)


def device_id():
    return request.headers.get("X-Anthares-Device", "").strip()


def _valid_hash(value):
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _remember_device_hash(device, token_hash):
    if not device or not _valid_hash(token_hash):
        return
    try:
        with store.connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS ara_device_auth(
                     device_id TEXT PRIMARY KEY,
                     token_hash TEXT NOT NULL,
                     updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                   )"""
            )
            conn.execute(
                """INSERT INTO ara_device_auth(device_id,token_hash,updated_at)
                   VALUES(%s,%s,now())
                   ON CONFLICT(device_id) DO UPDATE
                   SET token_hash=excluded.token_hash, updated_at=now()""",
                (device, token_hash),
            )
    except Exception:
        app.logger.exception("failed to persist ARA device auth hash")


def _finalize_expired_uncertain(device=None):
    """Move expired unknown outcomes out of the active-pending count.

    The audit record is preserved permanently in PostgreSQL. We do not retry the
    operation and do not pretend it succeeded; after its deadline it becomes an
    expired terminal record with an explicit unknown-outcome result.
    """
    marker = {
        "ok": False,
        "error": "execution_outcome_unknown",
        "reconciled": "expired_after_deadline",
    }
    with store.connection() as conn:
        if device:
            conn.execute(
                """UPDATE ara_jobs
                   SET status='expired', lease_until=NULL,
                       result=COALESCE(result,%s::jsonb)
                   WHERE device_id=%s AND status='uncertain' AND expires_at<=now()""",
                (json.dumps(marker), device),
            )
        else:
            conn.execute(
                """UPDATE ara_jobs
                   SET status='expired', lease_until=NULL,
                       result=COALESCE(result,%s::jsonb)
                   WHERE status='uncertain' AND expires_at<=now()""",
                (json.dumps(marker),),
            )


def device_ok(device):
    if not device or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        for c in device
    ):
        return False
    env_key = "ARA_DEVICE_HASH_" + "".join(
        c if c.isalnum() else "_" for c in device.upper()
    )
    expected = os.getenv(env_key, "").strip().lower()
    if not _valid_hash(expected):
        cached = _HASH_CACHE.get(device)
        if cached and time.time() - cached[1] < _HASH_TTL:
            expected = cached[0]
        else:
            try:
                response = requests.get(f"{DEVICE_HASH_BASE}/{device}.sha256", timeout=6)
                expected = response.text.strip().lower() if response.ok else ""
                if _valid_hash(expected):
                    _HASH_CACHE[device] = (expected, time.time())
                else:
                    expected = ""
            except requests.RequestException:
                expected = ""
    got = bearer()
    actual = hashlib.sha256(got.encode()).hexdigest() if got else ""
    valid = bool(expected and actual) and secrets.compare_digest(actual, expected)
    if valid:
        _remember_device_hash(device, actual)
    return valid


@app.get("/healthz")
def health():
    try:
        _finalize_expired_uncertain()
        with store.connection() as conn:
            conn.execute("SELECT 1")
        return jsonify(
            ok=bool(_STARTUP_SELFTEST.get("ok")),
            database="connected",
            selftest=_STARTUP_SELFTEST,
        ), (200 if _STARTUP_SELFTEST.get("ok") else 503)
    except Exception:
        app.logger.exception("ARA health check failed")
        return jsonify(ok=False, database="unavailable", selftest=_STARTUP_SELFTEST), 503


@app.get("/")
def root():
    return health()


@app.get("/v1/device/auth-check")
def auth_check():
    device = device_id()
    if not device_ok(device):
        return jsonify(ok=False, error="unauthorized"), 401
    return jsonify(ok=True)


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
    _finalize_expired_uncertain(device)
    job = store.lease_next(device)
    return (jsonify(job=job), 200) if job else ("", 204)


@app.post("/v1/device/jobs/<job_id>/result")
def result(job_id):
    device = device_id()
    if not device_ok(device):
        return jsonify(error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    outcome = store.submit_result(device, job_id, body)
    if outcome == "missing":
        return jsonify(error="unknown_job_or_wrong_device"), 404
    if outcome == "not_leased":
        return jsonify(error="job_not_leased"), 409
    if outcome == "conflict":
        return jsonify(error="result_conflict"), 409
    return jsonify(ok=True, duplicate=(outcome == "duplicate"))


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
    idempotency_key = request.headers.get("Idempotency-Key", "").strip()
    if len(idempotency_key) > 200:
        return jsonify(error="idempotency_key_too_long"), 400
    job, created = store.create_job(
        device,
        job_type,
        body.get("args") or {},
        timeout,
        idempotency_key=idempotency_key or None,
    )
    return jsonify(ok=True, job=job, created=created), (201 if created else 200)


@app.get("/v1/control/jobs/<job_id>")
def get_job(job_id):
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    device = request.args.get("device_id", "").strip()
    if not device:
        return jsonify(error="missing_device_id"), 400
    _finalize_expired_uncertain(device)
    job = store.get_job(device, job_id)
    if not job:
        return jsonify(error="not_found"), 404
    return jsonify(job=job)


@app.get("/v1/control/status")
def status():
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    device = request.args.get("device_id", "").strip()
    if not device:
        return jsonify(error="missing_device_id"), 400
    _finalize_expired_uncertain(device)
    return jsonify(store.device_status(device))


@app.get("/v1/control/selftest")
def selftest():
    if not control_ok():
        return jsonify(error="unauthorized"), 401
    try:
        result = store.transactional_selftest()
        return jsonify(result)
    except Exception as exc:
        app.logger.exception("ARA PostgreSQL self-test failed")
        return jsonify(ok=False, error=type(exc).__name__), 503


try:
    store.initialize()
    _finalize_expired_uncertain()
    _STARTUP_SELFTEST = store.transactional_selftest()
    app.logger.info("ARA_POSTGRES_SELFTEST=PASS checks=%s", _STARTUP_SELFTEST["checks"])
except Exception as exc:
    _STARTUP_SELFTEST = {"ok": False, "error": type(exc).__name__}
    app.logger.exception("ARA PostgreSQL initialization/self-test failed")
