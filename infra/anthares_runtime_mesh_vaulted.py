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


def _diagnostic_code(result):
    detail = str(result.get("error_detail") or "").lower()
    if "host system is missing dependencies" in detail or "missing dependencies" in detail:
        return "playwright_system_dependencies_missing"
    if "executable doesn't exist" in detail or "executable does not exist" in detail:
        return "chromium_executable_missing"
    if "browser has been closed" in detail or "target page, context or browser has been closed" in detail:
        return "chromium_closed_during_startup"
    if "permission denied" in detail:
        return "browser_permission_denied"
    if result.get("restore_status") == "vault_unavailable":
        return "vault_unavailable"
    if result.get("last_persist_ok") is False:
        return "vault_persist_failed"
    if result.get("error"):
        return "browser_start_failed"
    return "unclassified"


def _hybrid_ready():
    url, _ = _mesh._browser_cfg()
    if url:
        return _ORIGINAL_READY()
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
        """Expose only non-sensitive durability evidence for external health checks."""
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
        if not fields["persistence_proven"]:
            code = _diagnostic_code(result)
            fields["diagnostic"] = code
            app.logger.warning(
                "browser_persistence_unproven diagnostic=%s healthy=%s restore=%s persist=%s",
                code,
                fields["healthy"],
                fields["restore_status"],
                fields["last_persist_ok"],
            )
        body = "\n".join(f"{key}={value}" for key, value in fields.items()) + "\n"
        return Response(body, status=200 if fields["healthy"] else 503, mimetype="text/plain")

    _mesh._browser_ready = _hybrid_ready
    _mesh._browser_request = _hybrid_request
    return _mesh.register(app)
