#!/usr/bin/env python3
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "infra"))
os.environ["ARA_SHARED"] = "mesh-secret"
os.environ["ANTHARES_BROWSER_URL"] = "https://browser.invalid"
os.environ["ANTHARES_BROWSER_TOKEN"] = "browser-secret"

from flask import Flask
import anthares_runtime_mesh as mesh


def reset():
    with mesh._LOCK:
        mesh._BROWSER_LEASE.update(owner=None, token=None, generation=0, expires_at=0.0)
    with mesh._remote._LOCK:
        mesh._remote._DEVICES.clear()


def app_client():
    app = Flask(__name__)
    mesh.register(app)
    return app.test_client()


def auth(extra=None):
    headers = {"Authorization": "Bearer mesh-secret"}
    headers.update(extra or {})
    return headers


def acquire(c, owner="runner-a"):
    r = c.post("/v1/runtime/browser/lease/acquire", headers=auth(), json={"owner": owner, "ttl_seconds": 300})
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def test_health_fail_closed_and_no_host_fallback():
    reset(); c = app_client()
    fake = SimpleNamespace(ok=True, status_code=200, headers={"content-type": "application/json"}, json=lambda: {"ok": True, "cdp_ready": True})
    with patch.object(mesh.requests, "get", return_value=fake):
        body = c.get("/v1/runtime/health").get_json()
    assert body["ok"] is True
    assert body["host_desktop_fallback"] is False
    assert body["browser"]["healthy"] is True
    assert body["control_authority"] == "anthares-control/cloudflare"


def test_browser_requires_control_auth():
    reset(); c = app_client()
    assert c.post("/v1/runtime/browser/lease/acquire", json={"owner": "x"}).status_code == 401
    assert c.get("/v1/runtime/browser/page").status_code == 401


def test_browser_single_writer_conflict():
    reset(); c = app_client(); first = acquire(c, "runner-a")
    second = c.post("/v1/runtime/browser/lease/acquire", headers=auth(), json={"owner": "runner-b"})
    assert second.status_code == 409
    assert second.get_json()["error"] == "lease_conflict"
    assert first["generation"] == 1


def test_stale_generation_fenced_after_release_and_reacquire():
    reset(); c = app_client(); first = acquire(c, "runner-a")
    h1 = auth({"X-Anthares-Lease-Token": first["token"], "X-Anthares-Lease-Generation": str(first["generation"])})
    assert c.post("/v1/runtime/browser/lease/release", headers=h1).status_code == 200
    second = acquire(c, "runner-b")
    assert second["generation"] == first["generation"] + 1
    stale = c.post("/v1/runtime/browser/navigate", headers=h1, json={"url": "https://example.com"})
    assert stale.status_code == 409
    assert stale.get_json()["error"] in {"stale_generation", "invalid_lease_token"}


def test_browser_mutation_proxies_only_with_live_lease():
    reset(); c = app_client(); lease = acquire(c)
    headers = auth({"X-Anthares-Lease-Token": lease["token"], "X-Anthares-Lease-Generation": str(lease["generation"])})
    fake = SimpleNamespace(status_code=200, json=lambda: {"ok": True, "url": "https://example.com"}, text="", headers={"content-type":"application/json"})
    with patch.object(mesh.requests, "request", return_value=fake) as req:
        r = c.post("/v1/runtime/browser/navigate", headers=headers, json={"url": "https://example.com"})
    assert r.status_code == 200
    assert req.call_args.args[:2] == ("POST", "https://browser.invalid/navigate")
    assert req.call_args.kwargs["headers"]["Authorization"] == "Bearer browser-secret"


def test_remote_execute_uses_remote_queue_boundary():
    reset(); c = app_client()
    result = {"status": "done", "result": {"ok": True, "output": "pong"}}
    with patch.object(mesh, "_remote_wait", return_value=result):
        r = c.post("/v1/runtime/remote/execute", headers=auth(), json={"device_id":"DESKTOP-FTDK0HP", "type":"ping", "timeout_seconds": 5})
    body = r.get_json()
    assert r.status_code == 200
    assert body["ok"] is True and body["output"] == "pong"
    with mesh._remote._LOCK:
        assert len(mesh._remote._DEVICES["DESKTOP-FTDK0HP"]["queue"]) == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test(); print("PASS", test.__name__)
    print(f"RUNTIME_MESH_TESTS={len(tests)} PASS")
