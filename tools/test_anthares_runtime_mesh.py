#!/usr/bin/env python3
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "infra"))
os.environ["ARA_SHARED"] = "mesh-test-token"
os.environ["ANTHARES_BROWSER_URL"] = "https://browser.invalid"
os.environ["ANTHARES_BROWSER_TOKEN"] = "browser-test-token"

from flask import Flask
import anthares_runtime_mesh as mesh


def reset():
    with mesh._LOCK:
        mesh._BROWSER_LEASE.update(owner=None, token=None, generation=0, expires_at=0.0)
    if hasattr(mesh._remote, "_DEVICES"):
        with mesh._remote._LOCK:
            mesh._remote._DEVICES.clear()


def app_client():
    app = Flask(__name__)
    mesh.register(app)
    return app.test_client()


def auth(extra=None):
    headers = {"Authorization": "Bearer mesh-test-token"}
    headers.update(extra or {})
    return headers


def acquire(c, owner="runner-a"):
    r = c.post("/v1/runtime/browser/lease/acquire", headers=auth(), json={"owner": owner, "ttl_seconds": 300})
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def test_health_fail_closed_and_no_host_fallback():
    reset(); c = app_client()
    fake = SimpleNamespace(ok=True, status_code=200, headers={"content-type": "application/json"}, json=lambda: {"ok": True, "cdp_ready": True, "chromium_running": True})
    with patch.object(mesh.requests, "get", return_value=fake):
        body = c.get("/v1/runtime/health").get_json()
    assert body["ok"] is True
    assert body["host_desktop_fallback"] is False
    assert body["browser"]["healthy"] is True
    assert body["control_authority"] == "anthares-control/cloudflare"
    assert body["global_lease_authority"] == "anthares-control/cloudflare"


def test_no_implicit_desktop_target():
    reset(); c = app_client()
    r = c.post("/v1/runtime/remote/execute", headers=auth(), json={"type": "ping"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "device_id_required_no_local_fallback"
    with patch.object(mesh.requests, "get", side_effect=RuntimeError("offline")):
        health = c.get("/v1/runtime/health").get_json()
    assert health["remote"]["device_id"] is None
    assert health["remote"]["connected"] is False


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
    assert first["scope"] == "local_browser_profile_fence"


def test_same_owner_cannot_steal_live_lease():
    reset(); c = app_client(); first = acquire(c, "runner-a")
    second = c.post("/v1/runtime/browser/lease/acquire", headers=auth(), json={"owner": "runner-a"})
    assert second.status_code == 409
    assert "token" not in second.get_json()
    h = auth({"X-Anthares-Lease-Token": first["token"], "X-Anthares-Lease-Generation": str(first["generation"])})
    assert c.post("/v1/runtime/browser/lease/renew", headers=h, json={"ttl_seconds": 300}).status_code == 200


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
    fake = SimpleNamespace(status_code=200, json=lambda: {"ok": True, "url": "https://example.com"}, text="", headers={"content-type": "application/json"})
    with patch.object(mesh.requests, "request", return_value=fake) as req:
        r = c.post("/v1/runtime/browser/navigate", headers=headers, json={"url": "https://example.com"})
    assert r.status_code == 200
    assert req.call_args.args[:2] == ("POST", "https://browser.invalid/navigate")
    assert req.call_args.kwargs["headers"]["Authorization"] == "Bearer browser-test-token"


def test_remote_execute_legacy_queue_boundary():
    reset(); c = app_client()
    result = {"id": "legacy-job", "status": "done", "result": {"ok": True, "output": "pong"}}
    with patch.object(mesh, "_legacy_wait", return_value=result):
        r = c.post("/v1/runtime/remote/execute", headers=auth(), json={"device_id": "DESKTOP-FTDK0HP", "type": "ping", "timeout_seconds": 5})
    body = r.get_json()
    assert r.status_code == 200
    assert body["ok"] is True and body["output"] == "pong"
    with mesh._remote._LOCK:
        assert len(mesh._remote._DEVICES["DESKTOP-FTDK0HP"]["queue"]) == 1


def test_remote_execute_prefers_durable_backend_when_available():
    reset(); c = app_client()
    durable = {"id": "durable-job", "status": "done", "result": {"ok": True, "output": "durable"}}
    with patch.object(mesh._remote, "execute_job", create=True, return_value=durable) as execute_job:
        r = c.post("/v1/runtime/remote/execute", headers=auth(), json={"device_id": "DESKTOP-FTDK0HP", "type": "ping", "timeout_seconds": 5})
    assert r.status_code == 200
    assert r.get_json()["output"] == "durable"
    execute_job.assert_called_once()


def test_health_prefers_durable_device_status_when_available():
    reset(); c = app_client()
    browser = SimpleNamespace(ok=True, status_code=200, headers={"content-type": "application/json"}, json=lambda: {"ok": True, "cdp_ready": True})
    with patch.object(mesh._remote, "device_status", create=True, return_value={"connected": True}), patch.object(mesh.requests, "get", return_value=browser):
        body = c.get("/v1/runtime/health?device_id=test-remote-device").get_json()
    assert body["remote"]["device_id"] == "test-remote-device"
    assert body["remote"]["connected"] is True


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test(); print("PASS", test.__name__)
    print(f"RUNTIME_MESH_TESTS={len(tests)} PASS")
