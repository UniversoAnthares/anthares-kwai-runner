"""Bind the vault-backed local browser to the generic Anthares runtime mesh."""
from __future__ import annotations

import anthares_runtime_mesh as _mesh
from anthares_runtime_browser_local import browser_request as _local_request
from anthares_runtime_browser_local import health as _local_health

_ORIGINAL_READY = _mesh._browser_ready
_ORIGINAL_REQUEST = _mesh._browser_request


def _hybrid_ready():
    url, _ = _mesh._browser_cfg()
    return _ORIGINAL_READY() if url else _local_health()


def _hybrid_request(method, path, payload=None):
    url, _ = _mesh._browser_cfg()
    return _ORIGINAL_REQUEST(method, path, payload) if url else _local_request(method, path, payload)


def register(app):
    _mesh._browser_ready = _hybrid_ready
    _mesh._browser_request = _hybrid_request
    return _mesh.register(app)
