import secrets
import threading
import time

from flask import jsonify, request

_LOCK = threading.Lock()
_DEVICES = {}


def register(app, shared_token):
    token = str(shared_token or "")

    def auth_ok():
        header = request.headers.get("Authorization", "")
        if not token or not header.startswith("Bearer "):
            return False
        return secrets.compare_digest(header[7:], token)

    def device_id():
        return request.headers.get("X-Anthares-Device", "").strip()

    def state(device):
        return _DEVICES.setdefault(device, {"heartbeat": None, "queue": [], "jobs": {}})

    @app.post("/v1/device/heartbeat")
    def ara_heartbeat():
        if not auth_ok():
            return jsonify(error="unauthorized"), 401
        device = device_id()
        if not device:
            return jsonify(error="missing_device_id"), 400
        body = request.get_json(silent=True) or {}
        body["seen_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with _LOCK:
            state(device)["heartbeat"] = body
        return jsonify(ok=True)

    @app.get("/v1/device/jobs/next")
    def ara_next_job():
        if not auth_ok():
            return jsonify(error="unauthorized"), 401
        device = device_id()
        if not device:
            return jsonify(error="missing_device_id"), 400
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
        if not auth_ok():
            return jsonify(error="unauthorized"), 401
        device = device_id()
        if not device:
            return jsonify(error="missing_device_id"), 400
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
        if not auth_ok():
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
        if not auth_ok():
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
        if not auth_ok():
            return jsonify(error="unauthorized"), 401
        device = request.args.get("device_id", "").strip()
        if not device:
            return jsonify(error="missing_device_id"), 400
        with _LOCK:
            s = state(device)
            return jsonify(heartbeat=s["heartbeat"], queued=len(s["queue"]))
