"""Explicit Anthares Remote Agent canary entrypoint.

The dedicated canary uses its own Flask app, independent of the existing X worker.
"""
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
    """Token-gated synthetic persistence proof; this route exists on the canary only."""
    expected = os.getenv("ARA_PERSISTENCE_PROBE_TOKEN", "")
    supplied = request.headers.get("Authorization", "")
    supplied = supplied[7:] if supplied.startswith("Bearer ") else ""
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify(ok=False, error="unauthorized"), 401

    device = "persistence-probe-" + uuid.uuid4().hex
    idem = "persistence-probe-" + uuid.uuid4().hex
    created = _durable_store.enqueue(device, "ping", {"probe": True}, 30, idempotency_key=idem)
    duplicate = _durable_store.enqueue(device, "ping", {"probe": True}, 30, idempotency_key=idem)
    leased = _durable_store.lease_next(device, lease_seconds=15)
    if not leased or leased.get("id") != created.get("id"):
        return jsonify(ok=False, stage="lease", created_status=created.get("status")), 500
    completed = _durable_store.complete(device, created["id"], {"ok": True, "output": "persistence-probe"})
    recovered = build_store().get_job(device, created["id"])
    checks = {
        "created": created.get("status") == "queued",
        "idempotency": duplicate.get("id") == created.get("id"),
        "leased": leased.get("status") == "leased",
        "completed": (completed or {}).get("status") == "done",
        "recovered_after_new_store": (recovered or {}).get("status") == "done",
        "result_recovered": ((recovered or {}).get("result") or {}).get("output") == "persistence-probe",
    }
    return jsonify(ok=all(checks.values()), backend="postgres", checks=checks,
                   test_job_id=created["id"]), (200 if all(checks.values()) else 500)


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
