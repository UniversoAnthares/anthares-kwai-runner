import base64
import hashlib
import os
import secrets
import threading
import time

import requests
from flask import Response, jsonify, request

_LOCK = threading.Lock()
_DEVICES = {}
_DEVICE_HASH_CACHE = {}
_DEVICE_HASH_TTL = 60
_DEVICE_HASH_BASE = "https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices"
_PROBE_DEVICE = "DESKTOP-FTDK0HP"
_BLOBS = {}
_MAX_TRANSFER = 100 * 1024 * 1024


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

    def enqueue(device, job_type, args=None, timeout=30):
        job_id = secrets.token_hex(16)
        job = {
            "id": job_id,
            "type": job_type,
            "args": args or {},
            "timeout_seconds": max(1, min(int(timeout or 30), 120)),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "queued",
        }
        s = state(device)
        s["jobs"][job_id] = job
        s["queue"].append(job_id)
        return job

    def wait_for_job(device, job_id, wait_seconds):
        deadline = time.time() + max(1, min(float(wait_seconds), 130.0))
        while time.time() < deadline:
            with _LOCK:
                job = state(device)["jobs"].get(job_id)
                if not job:
                    return None
                if job.get("status") in ("done", "failed"):
                    return dict(job)
            time.sleep(0.20)
        with _LOCK:
            job = state(device)["jobs"].get(job_id)
            return dict(job) if job else None

    def execute(device, job_type, args=None, timeout=30):
        with _LOCK:
            job = enqueue(device, job_type, args or {}, timeout)
        return wait_for_job(device, job["id"], min(int(timeout or 30) + 8, 130))

    def stash_blob(data, mime="application/octet-stream", filename="download.bin", ttl=300):
        token = secrets.token_urlsafe(32)
        now = time.time()
        with _LOCK:
            # Opportunistic cleanup keeps this in-memory courier bounded.
            for key, item in list(_BLOBS.items()):
                if item["expires"] <= now:
                    _BLOBS.pop(key, None)
            _BLOBS[token] = {
                "data": data,
                "mime": mime,
                "filename": filename,
                "expires": now + max(30, min(int(ttl), 900)),
            }
        return token

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
        with _LOCK:
            job = enqueue(device, job_type, body.get("args") or {}, body.get("timeout_seconds") or 30)
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

    @app.post("/v1/control/execute")
    def ara_execute():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "").strip()
        job_type = str(body.get("type") or "").strip()
        timeout = max(1, min(int(body.get("timeout_seconds") or 30), 120))
        if not device or not job_type:
            return jsonify(error="missing_device_id_or_type"), 400
        job = execute(device, job_type, body.get("args") or {}, timeout)
        if not job:
            return jsonify(error="job_lost"), 503
        if job.get("status") not in ("done", "failed"):
            return jsonify(ok=False, status=job.get("status"), job_id=job.get("id"), error="timeout_waiting_for_device"), 504
        result = job.get("result") or {}
        return jsonify(
            ok=bool(result.get("ok")), status=job.get("status"), job_id=job.get("id"),
            output=result.get("output"), error=result.get("error"),
            started_at=result.get("started_at"), ended_at=result.get("ended_at"),
        ), (200 if result.get("ok") else 500)

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

    @app.get("/v1/control/capabilities")
    def ara_capabilities():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        return jsonify(
            ok=True,
            protocol="anthares-remote-agent/0.2",
            capabilities=[
                "status", "system_info", "shell", "process_list", "clipboard_get", "clipboard_set",
                "screenshot", "file_stat", "file_list", "file_read", "file_write",
                "file_read_chunk", "file_write_chunk", "job_start", "job_list", "job_status", "job_logs", "job_cancel",
                "pull_100mb", "push_chunked", "elevated_via_system_agent",
            ],
        )

    @app.post("/v1/control/screenshot")
    def ara_screenshot_bridge():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or _PROBE_DEVICE).strip()
        display = str(body.get("display") if body.get("display") is not None else "0")
        job = execute(device, "screenshot", {"display": display}, 45)
        result = (job or {}).get("result") or {}
        if not result.get("ok"):
            return jsonify(ok=False, error=result.get("error") or "screenshot_failed"), 500
        try:
            data = base64.b64decode(result.get("output") or "", validate=True)
        except Exception:
            return jsonify(ok=False, error="invalid_screenshot_payload"), 500
        if not data:
            return jsonify(ok=False, error="empty_screenshot"), 500
        token = stash_blob(data, "image/jpeg", f"{device}-display-{display}.jpg", 180)
        return jsonify(ok=True, size=len(data), download_url=f"/v1/blob/{token}")

    @app.post("/v1/control/pull")
    def ara_pull_bridge():
        if not control_auth_ok():
            return jsonify(error="unauthorized"), 401
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or _PROBE_DEVICE).strip()
        path = str(body.get("path") or "")
        if not path:
            return jsonify(error="missing_path"), 400
        stat_job = execute(device, "file_stat", {"path": path}, 30)
        stat_result = (stat_job or {}).get("result") or {}
        if not stat_result.get("ok"):
            return jsonify(ok=False, error=stat_result.get("error") or "stat_failed"), 500
        try:
            meta = __import__("json").loads(stat_result.get("output") or "{}")
            size = int(meta.get("size") or 0)
        except Exception:
            return jsonify(ok=False, error="invalid_stat_payload"), 500
        if meta.get("is_dir"):
            return jsonify(ok=False, error="path_is_directory"), 400
        if size > _MAX_TRANSFER:
            return jsonify(ok=False, error="file_exceeds_100mb", size=size), 413
        offset = 0
        chunks = []
        while offset < size:
            job = execute(device, "file_read_chunk", {"path": path, "offset": str(offset), "length": str(4 * 1024 * 1024)}, 45)
            result = (job or {}).get("result") or {}
            if not result.get("ok"):
                return jsonify(ok=False, error=result.get("error") or "read_chunk_failed", offset=offset), 500
            try:
                payload = __import__("json").loads(result.get("output") or "{}")
                chunk = base64.b64decode(payload.get("base64") or "", validate=True)
                next_offset = int(payload.get("next_offset"))
            except Exception:
                return jsonify(ok=False, error="invalid_chunk_payload", offset=offset), 500
            if next_offset <= offset and offset < size:
                return jsonify(ok=False, error="non_advancing_chunk", offset=offset), 500
            chunks.append(chunk)
            offset = next_offset
        data = b"".join(chunks)
        token = stash_blob(data, "application/octet-stream", os.path.basename(path) or "download.bin", 600)
        return jsonify(ok=True, size=len(data), download_url=f"/v1/blob/{token}")

    @app.get("/v1/blob/<token>")
    def ara_blob(token):
        with _LOCK:
            item = _BLOBS.pop(token, None)
        if not item or item["expires"] <= time.time():
            return jsonify(error="not_found_or_expired"), 404
        headers = {"Content-Disposition": f'attachment; filename="{item["filename"].replace(chr(34), "")}"', "Cache-Control": "no-store"}
        return Response(item["data"], mimetype=item["mime"], headers=headers)

    @app.get("/v1/public/status")
    def ara_public_status():
        device = request.args.get("device_id", "").strip()
        if device != _PROBE_DEVICE:
            return jsonify(error="not_found"), 404
        with _LOCK:
            hb = state(device)["heartbeat"]
        return jsonify(device_id=device, connected=bool(hb), heartbeat=hb)

    @app.post("/v1/public/ping")
    def ara_public_ping_create():
        body = request.get_json(silent=True) or {}
        device = str(body.get("device_id") or "").strip()
        if device != _PROBE_DEVICE:
            return jsonify(error="not_found"), 404
        with _LOCK:
            job = enqueue(device, "ping", {}, 15)
        return jsonify(job_id=job["id"], status=job["status"]), 202

    @app.get("/v1/public/ping/<job_id>")
    def ara_public_ping_get(job_id):
        with _LOCK:
            job = state(_PROBE_DEVICE)["jobs"].get(job_id)
            if not job or job.get("type") != "ping":
                return jsonify(error="not_found"), 404
            result = job.get("result") or {}
            return jsonify(status=job.get("status"), ok=result.get("ok"), output=result.get("output") if result.get("ok") else None)
