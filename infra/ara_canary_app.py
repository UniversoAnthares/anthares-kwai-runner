"""Explicit Anthares Remote Agent canary entrypoint.

The dedicated canary uses its own Flask app, independent of the existing X worker.
"""
import os

from ara_state_store import build_store

# Fail at startup if durable storage or controller credentials are unavailable.
if not os.getenv("ARA_SHARED"):
    raise RuntimeError("ARA_SHARED must be configured before serving control routes")
if not (os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")):
    raise RuntimeError("ARA canary requires a durable PostgreSQL connection")
_durable_store = build_store()

from flask import Flask
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

@app.get("/healthz")
def ara_canary_health():
    # Do not expose DSNs, credentials, device identifiers or stored job data.
    try:
        with _durable_store._conn() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            ready = cursor.fetchone()[0] == 1
        return {"ok": ready, "backend": "postgres"}, (200 if ready else 503)
    except Exception:
        app.logger.exception("ARA PostgreSQL readiness check failed")
        return {"ok": False, "backend": "postgres"}, 503
