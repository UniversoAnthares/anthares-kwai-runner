"""Signed MCP surface for the dedicated PostgreSQL ARA control service."""
import base64
import json
import threading
import time
from datetime import datetime, timezone

import requests
from flask import jsonify, request
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

import ara_postgres_store as store

_SIGNER = "anthares-remote-mcp"
_KEY_URLS = (
    "https://anthares-remote-mcp-v2.onrender.com/.well-known/ara-control-key",
    "https://anthares-remote-mcp.onrender.com/.well-known/ara-control-key",
)
_LOCK = threading.Lock()
_KEY_CACHE = {"keys": [], "at": 0.0, "sources": []}
_REPLAY = {}


def _keys(refresh=False):
    now = time.time()
    with _LOCK:
        if not refresh and _KEY_CACHE["keys"] and now - _KEY_CACHE["at"] < 60:
            return list(_KEY_CACHE["keys"])
    keys, sources, seen = [], [], set()
    for url in _KEY_URLS:
        try:
            r = requests.get(url, timeout=6, headers={"User-Agent": "AntharesARAControl/1.0"})
            r.raise_for_status()
            if len(r.content) > 4096:
                continue
            key = serialization.load_pem_public_key(r.content)
            fp = key.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            if fp not in seen:
                seen.add(fp)
                keys.append(key)
                sources.append(url)
        except Exception:
            continue
    if not keys:
        raise ValueError("no MCP signing key available")
    with _LOCK:
        _KEY_CACHE.update(keys=list(keys), at=now, sources=list(sources))
    return keys


def _decode_sig(value):
    value = str(value or "")
    value += "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))


def _verify():
    if request.headers.get("X-ARA-Signer", "") != _SIGNER:
        return False, b""
    ts = request.headers.get("X-ARA-Timestamp", "")
    sig = request.headers.get("X-ARA-Signature", "")
    try:
        ts_num, signature = int(ts), _decode_sig(sig)
    except Exception:
        return False, b""
    if abs(int(time.time() * 1000) - ts_num) > 30000:
        return False, b""
    raw = request.get_data(cache=True) or b""
    if len(raw) > 3 * 1024 * 1024:
        return False, b""
    with _LOCK:
        cutoff = time.time() - 60
        for key, seen_at in list(_REPLAY.items()):
            if seen_at < cutoff:
                _REPLAY.pop(key, None)
        if sig in _REPLAY:
            return False, b""
    qs = request.query_string.decode("ascii", errors="strict")
    path = request.path + (("?" + qs) if qs else "")
    payload = (ts + "\n" + request.method.upper() + "\n" + path + "\n").encode() + raw
    for refresh in (False, True):
        try:
            for key in _keys(refresh):
                try:
                    key.verify(signature, payload)
                    with _LOCK:
                        _REPLAY[sig] = time.time()
                    return True, raw
                except InvalidSignature:
                    pass
        except Exception:
            pass
    return False, b""


def _heartbeat_fresh(status, max_age_seconds=90):
    if not status.get("heartbeat") or not status.get("seen_at"):
        return False
    try:
        seen = datetime.fromisoformat(str(status["seen_at"]).replace("Z", "+00:00"))
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - seen.astimezone(timezone.utc)).total_seconds()
        return 0 <= age <= max_age_seconds
    except (TypeError, ValueError, OverflowError):
        return False


def _consume_oauth_token(kind, issuer, jti, exp):
    if kind not in {"authorization_code", "refresh_token"}:
        return False
    if not issuer or len(issuer) > 300 or not jti or len(jti) > 128:
        return False
    try:
        exp = int(exp)
    except (TypeError, ValueError):
        return False
    now = int(time.time())
    if exp <= now or exp > now + 32 * 24 * 3600:
        return False
    with store.connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ara_oauth_consumed(
              kind TEXT NOT NULL,
              issuer TEXT NOT NULL,
              jti TEXT NOT NULL,
              expires_at TIMESTAMPTZ NOT NULL,
              consumed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              PRIMARY KEY(kind,issuer,jti)
            )
            """
        )
        conn.execute("DELETE FROM ara_oauth_consumed WHERE expires_at <= now()")
        row = conn.execute(
            """
            INSERT INTO ara_oauth_consumed(kind,issuer,jti,expires_at)
            VALUES(%s,%s,%s,to_timestamp(%s))
            ON CONFLICT DO NOTHING
            RETURNING jti
            """,
            (kind, issuer, jti, exp),
        ).fetchone()
        return row is not None


def _execute(device, job_type, args, timeout):
    job, _ = store.create_job(device, job_type, args or {}, timeout)
    deadline = time.time() + min(timeout + 8, 130)
    while time.time() < deadline:
        current = store.get_job(device, job["id"])
        if not current:
            return None
        if current.get("status") in ("done", "failed", "expired", "uncertain"):
            return current
        time.sleep(0.2)
    return store.get_job(device, job["id"])


def register(app):
    @app.get("/v1/mcp/status")
    def mcp_status():
        ok, _ = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        device = request.args.get("device_id", "").strip()
        if not device:
            return jsonify(error="missing_device_id"), 400
        status = store.device_status(device)
        return jsonify(**status, connected=_heartbeat_fresh(status))

    @app.get("/v1/mcp/capabilities")
    def mcp_capabilities():
        ok, _ = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        with _LOCK:
            trusted = len(_KEY_CACHE.get("sources") or [])
        return jsonify(
            ok=True,
            protocol="anthares-remote-agent/1.0",
            auth="ed25519-service-signature",
            durability="postgres",
            replay_protection=True,
            oauth_one_time_tokens="postgres",
            redundant_mcp_keys=True,
            rotating_service_key_refresh=True,
            trusted_mcp_services=trusted,
            capabilities=[
                "status", "system_info", "shell", "process_list", "process_start", "process_kill",
                "service_status", "service_start", "service_stop", "clipboard_get", "clipboard_set", "screenshot",
                "file_stat", "file_list", "file_read", "file_write", "file_read_chunk", "file_write_chunk",
                "file_mkdir", "file_remove", "file_rename", "file_copy", "file_sha256", "file_write_atomic",
                "job_start", "job_list", "job_status", "job_logs", "job_cancel",
            ],
        )

    @app.post("/v1/mcp/oauth/consume")
    def mcp_oauth_consume():
        ok, raw = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
            kind = str(body.get("kind") or "")
            issuer = str(body.get("issuer") or "")
            jti = str(body.get("jti") or "")
            exp = body.get("exp")
        except Exception:
            return jsonify(error="invalid_request"), 400
        try:
            consumed = _consume_oauth_token(kind, issuer, jti, exp)
        except Exception:
            app.logger.exception("durable OAuth token consumption failed")
            return jsonify(error="oauth_store_unavailable"), 503
        if not consumed:
            return jsonify(ok=False, error="already_used_or_invalid"), 409
        return jsonify(ok=True, consumed=True)

    @app.post("/v1/mcp/execute")
    def mcp_execute():
        ok, raw = _verify()
        if not ok:
            return jsonify(error="unauthorized"), 401
        try:
            body = json.loads(raw.decode()) if raw else {}
            device = str(body.get("device_id") or "").strip()
            job_type = str(body.get("type") or "").strip()
            timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        except Exception:
            return jsonify(error="invalid_request"), 400
        if not device or not job_type:
            return jsonify(error="missing_device_id_or_type"), 400
        job = _execute(device, job_type, body.get("args") or {}, timeout)
        if not job:
            return jsonify(error="job_lost"), 503
        status = job.get("status")
        if status == "uncertain":
            return jsonify(
                ok=False,
                status=status,
                job_id=job.get("id"),
                error="execution_outcome_unknown",
            ), 409
        if status not in ("done", "failed"):
            return jsonify(
                ok=False,
                status=status,
                job_id=job.get("id"),
                error="timeout_waiting_for_device",
            ), 504
        result = job.get("result") or {}
        # A completed remote operation may legitimately report ok=false (for example,
        # a rejected path or non-zero command). That is an operation result, not a
        # control-plane failure. Keep transport HTTP 200 so clients receive the
        # structured outcome; reserve 5xx for infrastructure failures above.
        return jsonify(
            ok=bool(result.get("ok")),
            status=status,
            job_id=job.get("id"),
            output=result.get("output"),
            error=result.get("error"),
            started_at=result.get("started_at"),
            ended_at=result.get("ended_at"),
        ), 200
