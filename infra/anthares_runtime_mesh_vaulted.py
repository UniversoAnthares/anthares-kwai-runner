"""Bind the vault-backed local browser to the generic Anthares runtime mesh."""
from __future__ import annotations

from flask import Response, jsonify

import anthares_runtime_mesh as _mesh
import anthares_runtime_browser_local as _local

_ORIGINAL_READY = _mesh._browser_ready
_ORIGINAL_REQUEST = _mesh._browser_request


def _diagnostic_local_health():
    try:
        return _local.health()
    except Exception as exc:
        return {
            "configured": True,
            "healthy": False,
            "backend": "local_playwright_vault",
            "isolated": True,
            "headless": True,
            "chromium_running": False,
            "host_desktop_fallback": False,
            "error": type(exc).__name__,
            "error_detail": str(exc)[:1000],
        }


def _external_ready():
    """Use the browser readiness contract, never its liveness-only /health route."""
    url, token = _mesh._browser_cfg()
    if not url or not token:
        return {"configured": False, "healthy": False, "error": "browser_not_configured"}
    try:
        response = _mesh.requests.get(url + "/ready", timeout=8)
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        evidence = body.get("detail") if isinstance(body.get("detail"), dict) else body
        cdp_ready = bool(evidence.get("cdp_ready"))
        chromium_running = bool(evidence.get("chromium_running"))
        ready = bool(response.ok and evidence.get("ok") and cdp_ready and chromium_running)
        return {
            "configured": True,
            "healthy": ready,
            "status": response.status_code,
            "cdp_ready": cdp_ready,
            "chromium_running": chromium_running,
            "profile_dir_exists": bool(evidence.get("profile_dir_exists")),
            "profile_dir_writable": bool(evidence.get("profile_dir_writable")),
            "durable_volume_verified": bool(evidence.get("durable_volume_verified")),
            "readiness_path": "/ready",
        }
    except Exception as exc:
        return {"configured": True, "healthy": False, "error": type(exc).__name__, "readiness_path": "/ready"}


def _hybrid_ready():
    url, _ = _mesh._browser_cfg()
    if url:
        return _external_ready()
    result = _diagnostic_local_health()
    if not result.get("healthy") and "error_detail" not in result:
        try:
            _local._ensure_browser()
        except Exception as exc:
            result["error_detail"] = str(exc)[:1000]
    return result


def _hybrid_request(method, path, payload=None):
    url, _ = _mesh._browser_cfg()
    return _ORIGINAL_REQUEST(method, path, payload) if url else _local.browser_request(method, path, payload)


def register(app):
    @app.get("/v1/runtime/browser/signing-public-key")
    def browser_signing_public_key():
        try:
            return jsonify(ok=True, algorithm="ECDSA-P256-SHA256", jwk=_local.public_jwk())
        except Exception as exc:
            return jsonify(ok=False, error=type(exc).__name__), 503

    @app.get("/v1/runtime/browser/persistence-status")
    def browser_persistence_status():
        result = _diagnostic_local_health()
        fields = {
            "healthy": bool(result.get("healthy")),
            "backend": result.get("backend"),
            "vault_enabled": bool(result.get("vault_enabled")),
            "restore_status": result.get("restore_status"),
            "last_persist_ok": result.get("last_persist_ok"),
            "host_desktop_fallback": bool(result.get("host_desktop_fallback")),
        }
        fields["persistence_proven"] = bool(
            fields["healthy"]
            and fields["vault_enabled"]
            and fields["restore_status"] == "restored"
            and fields["last_persist_ok"] is True
            and not fields["host_desktop_fallback"]
        )
        app.logger.warning(
            "ANTHARES_BROWSER_PERSISTENCE healthy=%s restore=%s persist=%s proven=%s",
            fields["healthy"], fields["restore_status"], fields["last_persist_ok"], fields["persistence_proven"]
        )
        body = "\n".join(f"{key}={value}" for key, value in fields.items()) + "\n"
        return Response(body, status=200 if fields["healthy"] else 503, mimetype="text/plain")

    _mesh._browser_ready = _hybrid_ready
    _mesh._browser_request = _hybrid_request
    return _mesh.register(app)
