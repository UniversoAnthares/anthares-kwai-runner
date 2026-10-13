"""Explicit Anthares Remote Agent canary entrypoint.

The dedicated canary uses its own Flask app, independent of the existing X worker.
"""
import hashlib
import hmac
import os
import uuid

from ara_state_store import build_store

if not os.getenv("ARA_SHARED"):
    raise RuntimeError("ARA_SHARED must be configured before serving control routes")
if not (os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")):
    raise RuntimeError("ARA canary requires a durable PostgreSQL connection")
_durable_store = build_store()

from flask import Flask, jsonify, request
import anthares_remote_control_routes as _relay
from ara_public_probe_guard import register as _register_probe_guard
from ara_runtime_truth import register as _register_runtime_truth

app = Flask("anthares_remote_agent_canary")
_register_probe_guard(app)
_register_runtime_truth(app)
_relay.register(app, os.getenv("ARA_SHARED", ""))

from anthares_remote_browser_bridge import register as _register_browser
from anthares_remote_secure_bootstrap import register as _register_secure_bootstrap

# Deliberately do not register anthares_remote_bootstrap or anthares_remote_switch:
# both legacy modules expose shell-producing actions without controller authentication.
_register_browser(app)
_register_secure_bootstrap(app)


@app.post("/_canary/persistence-cycle")
def ara_persistence_cycle_probe():
    """Token-gated synthetic end-to-end persistence proof; canary only."""
    expected = os.getenv("ARA_PERSISTENCE_PROBE_TOKEN", "")
    supplied = request.headers.get("Authorization", "")
    supplied = supplied[7:] if supplied.startswith("Bearer ") else ""
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify(ok=False, error="unauthorized"), 401

    controller_token = os.getenv("ARA_SHARED", "")
    if not controller_token:
        return jsonify(ok=False, error="controller_not_configured"), 503

    device = "persistence-probe-" + uuid.uuid4().hex
    idem = "persistence-probe-" + uuid.uuid4().hex
    device_token = "device-probe-" + uuid.uuid4().hex
    env_key = "ARA_DEVICE_HASH_" + "".join(c if c.isalnum() else "_" for c in device.upper())
    old_hash = os.environ.get(env_key)
    os.environ[env_key] = hashlib.sha256(device_token.encode("utf-8")).hexdigest()
    headers = {"Authorization": "Bearer " + controller_token}
    device_headers = {
        "Authorization": "Bearer " + device_token,
        "X-Anthares-Device": device,
    }

    try:
        # Exercise the actual HTTP control route for creation.
        with app.test_client() as client:
            created_response = client.post(
                "/v1/control/jobs",
                headers=headers,
                json={"device_id": device, "type": "ping", "args": {"probe": True},
                      "timeout_seconds": 30, "idempotency_key": idem},
            )
            created_body = created_response.get_json() or {}
            created = created_body.get("job") or {}
            duplicate_response = client.post(
                "/v1/control/jobs",
                headers=headers,
                json={"device_id": device, "type": "ping", "args": {"probe": True},
                      "timeout_seconds": 30, "idempotency_key": idem},
            )
            duplicate = (duplicate_response.get_json() or {}).get("job") or {}

            # Exercise the actual authenticated device lease route.
            lease_response = client.get("/v1/device/jobs/next", headers=device_headers)
            leased = (lease_response.get_json() or {}).get("job") or {}

            # Exercise the actual authenticated device completion route.
            result_response = client.post(
                "/v1/device/jobs/" + str(created.get("id", "")) + "/result",
                headers=device_headers,
                json={"ok": True, "output": "persistence-probe"},
            )

            # Exercise the actual HTTP control retrieval route.
            get_response = client.get(
                "/v1/control/jobs/" + str(created.get("id", "")) + "?device_id=" + device,
                headers=headers,
            )
            recovered_via_route = (get_response.get_json() or {}).get("job") or {}

        # A newly constructed store opens a fresh PostgreSQL connection and reads the durable row.
        recovered_after_new_store = build_store().get_job(device, str(created.get("id", "")))
        checks = {
            "created_via_control_route": created_response.status_code == 201 and created.get("status") == "queued",
            "idempotency_via_control_route": duplicate_response.status_code == 201 and duplicate.get("id") == created.get("id"),
            "lease_via_device_route": lease_response.status_code == 200 and leased.get("status") == "leased" and leased.get("id") == created.get("id"),
            "completion_via_device_route": result_response.status_code == 200,
            "retrieval_via_control_route": get_response.status_code == 200 and recovered_via_route.get("status") == "done",
            "recovery_with_fresh_store": (recovered_after_new_store or {}).get("status") == "done",
            "result_recovered": ((recovered_after_new_store or {}).get("result") or {}).get("output") == "persistence-probe",
        }
        return jsonify(ok=all(checks.values()), backend="postgres", checks=checks,
                       test_job_id=created.get("id")), (200 if all(checks.values()) else 500)
    finally:
        if old_hash is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = old_hash


@app.get("/healthz")
def ara_canary_health():
    try:
        with _durable_store._conn() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            ready = cursor.fetchone()[0] == 1
        return {"ok": ready, "backend": "postgres"}, (200 if ready else 503)
    except Exception:
        app.logger.exception("ARA PostgreSQL readiness check failed")
        return {"ok": False, "backend": "postgres"}, 503
