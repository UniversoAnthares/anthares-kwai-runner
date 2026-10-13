"""Explicit Anthares Remote Agent canary entrypoint.

The dedicated canary uses its own Flask app, independent of the existing X worker.
It also executes a synthetic persistence proof at boot so durability can be
validated without exposing controller credentials or requiring manual secrets.
"""
import hashlib
import os
import uuid

from ara_state_store import build_store

if not os.getenv("ARA_SHARED"):
    raise RuntimeError("ARA_SHARED must be configured before serving control routes")
if not (os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")):
    raise RuntimeError("ARA canary requires a durable PostgreSQL connection")
_durable_store = build_store()

from flask import Flask, jsonify
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

_RESTART_DEVICE = "persistence-restart-sentinel-v1"
_RESTART_IDEMPOTENCY_KEY = "persistence-restart-sentinel-v1"


def _route_cycle_proof():
    """Exercise create -> idempotency -> lease -> complete -> read through real routes."""
    controller_token = os.getenv("ARA_SHARED", "")
    device = "persistence-route-probe-" + uuid.uuid4().hex
    idem = "persistence-route-probe-" + uuid.uuid4().hex
    device_token = "device-probe-" + uuid.uuid4().hex
    env_key = "ARA_DEVICE_HASH_" + "".join(c if c.isalnum() else "_" for c in device.upper())
    old_hash = os.environ.get(env_key)
    os.environ[env_key] = hashlib.sha256(device_token.encode("utf-8")).hexdigest()
    control_headers = {"Authorization": "Bearer " + controller_token}
    device_headers = {"Authorization": "Bearer " + device_token, "X-Anthares-Device": device}

    try:
        with app.test_client() as client:
            created_response = client.post(
                "/v1/control/jobs",
                headers=control_headers,
                json={
                    "device_id": device,
                    "type": "ping",
                    "args": {"probe": True},
                    "timeout_seconds": 30,
                    "idempotency_key": idem,
                },
            )
            created = (created_response.get_json() or {}).get("job") or {}

            duplicate_response = client.post(
                "/v1/control/jobs",
                headers=control_headers,
                json={
                    "device_id": device,
                    "type": "ping",
                    "args": {"probe": True},
                    "timeout_seconds": 30,
                    "idempotency_key": idem,
                },
            )
            duplicate = (duplicate_response.get_json() or {}).get("job") or {}

            lease_response = client.get("/v1/device/jobs/next", headers=device_headers)
            leased = (lease_response.get_json() or {}).get("job") or {}

            result_response = client.post(
                "/v1/device/jobs/" + str(created.get("id", "")) + "/result",
                headers=device_headers,
                json={"ok": True, "output": "persistence-route-probe"},
            )

            get_response = client.get(
                "/v1/control/jobs/" + str(created.get("id", "")) + "?device_id=" + device,
                headers=control_headers,
            )
            recovered_via_route = (get_response.get_json() or {}).get("job") or {}

        recovered_after_new_store = build_store().get_job(device, str(created.get("id", "")))
        checks = {
            "created_via_control_route": created_response.status_code == 201 and created.get("status") == "queued",
            "idempotency_via_control_route": duplicate_response.status_code == 201 and duplicate.get("id") == created.get("id"),
            "lease_via_device_route": lease_response.status_code == 200 and leased.get("status") == "leased" and leased.get("id") == created.get("id"),
            "completion_via_device_route": result_response.status_code == 200,
            "retrieval_via_control_route": get_response.status_code == 200 and recovered_via_route.get("status") == "done",
            "recovery_with_fresh_store": (recovered_after_new_store or {}).get("status") == "done",
            "result_recovered": ((recovered_after_new_store or {}).get("result") or {}).get("output") == "persistence-route-probe",
        }
        return {
            "ok": all(checks.values()),
            "checks": checks,
            "test_job_id": created.get("id"),
        }
    finally:
        if old_hash is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = old_hash


def _restart_recovery_proof():
    """Create a durable sentinel once; subsequent boots must recover it as done."""
    existing = _durable_store.enqueue(
        _RESTART_DEVICE,
        "ping",
        {"probe": "restart"},
        120,
        idempotency_key=_RESTART_IDEMPOTENCY_KEY,
    )
    recovered_from_previous_boot = existing.get("status") == "done"

    if existing.get("status") == "queued":
        leased = _durable_store.lease_next(_RESTART_DEVICE, lease_seconds=30)
        if leased and leased.get("id") == existing.get("id"):
            _durable_store.complete(
                _RESTART_DEVICE,
                existing["id"],
                {"ok": True, "output": "restart-sentinel"},
            )

    current = build_store().get_job(_RESTART_DEVICE, existing["id"])
    return {
        "ok": (current or {}).get("status") == "done",
        "recovered_from_previous_boot": recovered_from_previous_boot,
        "sentinel_job_id": existing.get("id"),
        "current_status": (current or {}).get("status"),
        "result_recovered": ((current or {}).get("result") or {}).get("output") == "restart-sentinel",
    }


def _run_persistence_proof():
    try:
        route_cycle = _route_cycle_proof()
        restart = _restart_recovery_proof()
        return {
            "ok": bool(route_cycle.get("ok") and restart.get("ok")),
            "backend": "postgres",
            "route_cycle": route_cycle,
            "restart": restart,
        }
    except Exception as exc:
        app.logger.exception("ARA canary persistence proof failed")
        return {"ok": False, "backend": "postgres", "error": type(exc).__name__}


_PERSISTENCE_PROOF = _run_persistence_proof()


@app.get("/_canary/persistence-proof")
def ara_persistence_proof():
    # Read-only proof. It exposes booleans and synthetic job identifiers only.
    return jsonify(_PERSISTENCE_PROOF), (200 if _PERSISTENCE_PROOF.get("ok") else 503)


@app.get("/healthz")
def ara_canary_health():
    try:
        with _durable_store._conn() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            ready = cursor.fetchone()[0] == 1
        return {
            "ok": ready and bool(_PERSISTENCE_PROOF.get("ok")),
            "backend": "postgres",
            "persistence_cycle": bool(_PERSISTENCE_PROOF.get("ok")),
            "restart_recovered": bool((_PERSISTENCE_PROOF.get("restart") or {}).get("recovered_from_previous_boot")),
        }, (200 if ready and _PERSISTENCE_PROOF.get("ok") else 503)
    except Exception:
        app.logger.exception("ARA PostgreSQL readiness check failed")
        return {"ok": False, "backend": "postgres"}, 503
