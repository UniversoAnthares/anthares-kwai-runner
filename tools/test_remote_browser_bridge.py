#!/usr/bin/env python3
"""Acceptance for Anthares Remote to isolated Anthares-browser read-only routes."""
import os
import sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "infra"))
os.environ["ARA_SHARED"] = "acceptance-secret"
from flask import Flask
import anthares_runtime_mesh as mesh

app = Flask(__name__)
mesh.register(app)
client = app.test_client()
routes = {
    "/v1/runtime/browser/screenshot": "/screenshot",
    "/v1/runtime/browser/targets": "/targets",
    "/v1/runtime/browser/session/evidence": "/session/evidence",
}
for route, upstream in routes.items():
    denied = client.get(route)
    assert denied.status_code == 401, (route, denied.status_code)
    with patch.object(mesh, "_browser_request", return_value=(None, {"ok": True, "source": upstream}, 200)) as call:
        response = client.get(route, headers={"Authorization": "Bearer acceptance-secret"})
        assert response.status_code == 200
        assert response.json["source"] == upstream
        call.assert_called_once_with("GET", upstream)
    with patch.object(mesh, "_browser_request", return_value=(None, {"ok": False, "error": "browser_unreachable"}, 503)):
        response = client.get(route, headers={"Authorization": "Bearer acceptance-secret"})
        assert response.status_code == 503
print("ANTHARES_REMOTE_BROWSER_BRIDGE_OK=1")
