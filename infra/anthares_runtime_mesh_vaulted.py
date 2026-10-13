"""Bind the vault-backed local browser to the generic Anthares runtime mesh."""
from __future__ import annotations

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
    _mesh._browser_ready = _hybrid_ready
    _mesh._browser_request = _hybrid_request
    return _mesh.register(app)
