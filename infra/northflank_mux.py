"""Co-host ARA control and the X browser worker on one existing Northflank service.

ARA routes retain their original root paths. X is isolated under /x and uses
the Cloudflare runtime browser-state vault (never Render or the host desktop).
"""
import hashlib
import json
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware

os.environ.setdefault("ANTHARES_BROWSER_STATE_AUTHORITY", "runtime")
os.environ.setdefault("ANTHARES_BROWSER_STATE_VAULT_URL", "https://anthares-x-vault.anthares1.workers.dev/browser-state/runtime")

from ara_canary_app import app as ara_app
import x_render_worker_v3 as x_worker
import anthares_runtime_browser_local as browser_vault

x_worker.TOKEN = os.getenv("X_WORKER_TOKEN") or os.getenv("ARA_SHARED", "")
browser_vault.VAULT_URL = os.environ["ANTHARES_BROWSER_STATE_VAULT_URL"]


def _load_x_state():
    state = browser_vault._vault_pull()
    if not state or not state.get("cookies"):
        raise RuntimeError("X runtime browser state unavailable in durable vault")
    return x_worker._validate_state(state)


def _save_x_state(state):
    state = x_worker._validate_state(state)
    ciphertext = browser_vault._encrypt_state(state)
    body = json.dumps({
        "schema": "anthares.encrypted-browser-state.v1",
        "ciphertext": ciphertext,
        "sha256": hashlib.sha256(ciphertext.encode("ascii")).hexdigest(),
    }, separators=(",", ":"))
    response = browser_vault.requests.post(
        browser_vault.VAULT_URL,
        headers=browser_vault._signed_headers(body),
        data=body,
        timeout=20,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok") or not result.get("stored"):
        raise RuntimeError("X runtime browser vault did not acknowledge state")
    return result


x_worker._state = _load_x_state
x_worker._save_state = _save_x_state


class XAuthGate:
    """Keep X's state-changing and session-verification routes private."""

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/x/") and path not in {
            "/x/health",
            "/x/v1/runtime/browser/signing-public-key",
        }:
            expected = "Bearer " + (os.getenv("X_WORKER_TOKEN") or os.getenv("ARA_SHARED", ""))
            if expected == "Bearer " or environ.get("HTTP_AUTHORIZATION", "") != expected:
                start_response("401 Unauthorized", [("Content-Type", "application/json")])
                return [b'{"ok":false,"error":"unauthorized"}']
        return self.inner(environ, start_response)


app = XAuthGate(DispatcherMiddleware(ara_app, {"/x": x_worker.app}))
