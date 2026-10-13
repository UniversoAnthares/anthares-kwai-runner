"""Security and WebSocket regression tests for the Anthares Browser noVNC ingress."""
import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import novnc_gateway as gateway

SECRET = "gateway-test-control-token-longer-than-24"


class EchoBackend:
    subprotocol = "binary"

    def __init__(self):
        import asyncio
        self.queue = asyncio.Queue()

    async def send(self, value):
        await self.queue.put(value)

    async def __aiter__(self):
        while True:
            yield await self.queue.get()


@contextlib.asynccontextmanager
async def fake_connect(*args, **kwargs):
    assert args[0] == gateway.WS_BACKEND
    yield EchoBackend()


class NoVNCGatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "vnc.html").write_text("<html>noVNC</html>")
        (self.root / "app").mkdir()
        (self.root / "app" / "ui.js").write_text("const novnc = true")
        self.env = patch.dict(os.environ, {
            "CONTROL_TOKEN": SECRET, "NOVNC_COOKIE_SECURE": "0",
            "NOVNC_STATIC_ROOT": str(self.root),
        })
        self.env.start()
        self.static = patch.object(gateway, "NOVNC_ROOT", self.root)
        self.static.start()
        gateway.REVOKED.clear()
        app = FastAPI()
        app.include_router(gateway.router)
        self.client = TestClient(app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.static.stop()
        self.env.stop()
        self.tmp.cleanup()
        gateway.REVOKED.clear()

    def login(self):
        r = self.client.post("/novnc/session", headers={"Authorization": "Bearer " + SECRET})
        self.assertEqual(r.status_code, 200)
        return r

    def test_session_requires_bearer(self):
        self.assertEqual(self.client.post("/novnc/session").status_code, 401)

    def test_session_rejects_wrong_bearer(self):
        self.assertEqual(self.client.post("/novnc/session", headers={"Authorization": "Bearer bad"}).status_code, 401)

    def test_session_fails_closed_if_secret_missing(self):
        with patch.dict(os.environ, {"CONTROL_TOKEN": ""}):
            self.assertEqual(self.client.post("/novnc/session").status_code, 503)

    def test_session_cookie_is_httponly_samesite_strict(self):
        cookie = self.login().headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=strict", cookie)
        self.assertIn("path=/novnc", cookie)
        self.assertNotIn(SECRET, cookie)

    def test_secure_cookie_default(self):
        with patch.dict(os.environ, {"NOVNC_COOKIE_SECURE": "1"}):
            self.assertIn("secure", self.login().headers["set-cookie"].lower())

    def test_unauthorized_static(self):
        self.assertEqual(self.client.get("/novnc/vnc.html").status_code, 401)

    def test_authorized_static_and_subasset(self):
        self.login()
        self.assertIn("noVNC", self.client.get("/novnc/vnc.html").text)
        self.assertIn("novnc", self.client.get("/novnc/app/ui.js").text)

    def test_root_redirects_after_login(self):
        self.login()
        r = self.client.get("/novnc", follow_redirects=False)
        self.assertEqual(r.status_code, 303)
        self.assertEqual(r.headers["location"], "/novnc/vnc.html")

    def test_missing_file_is_404(self):
        self.login()
        self.assertEqual(self.client.get("/novnc/unknown.html").status_code, 404)

    def test_symlink_escape_is_404(self):
        secret_file = self.root.parent / (self.root.name + "-secret")
        secret_file.write_text("secret")
        try:
            (self.root / "leak").symlink_to(secret_file)
            self.login()
            self.assertEqual(self.client.get("/novnc/leak").status_code, 404)
        finally:
            secret_file.unlink()

    def test_tampered_cookie_rejected(self):
        self.login()
        self.client.cookies.set(gateway.COOKIE_NAME, "tampered", path="/novnc", domain="testserver.local")
        self.assertEqual(self.client.get("/novnc/vnc.html").status_code, 401)

    def test_expired_token_rejected(self):
        with patch.object(gateway.time, "time", return_value=1000):
            self.login()
        with patch.object(gateway.time, "time", return_value=2000):
            self.assertEqual(self.client.get("/novnc/vnc.html").status_code, 401)

    def test_logout_revokes_cookie(self):
        self.login()
        self.assertEqual(self.client.post("/novnc/logout", headers={"Authorization": "Bearer " + SECRET}).status_code, 200)
        self.assertEqual(self.client.get("/novnc/vnc.html").status_code, 401)

    def test_websocket_rejects_missing_cookie(self):
        with self.assertRaises(WebSocketDisconnect) as cm:
            with self.client.websocket_connect("/novnc/websockify", headers={"origin": "http://testserver"}):
                pass
        self.assertEqual(cm.exception.code, 1008)

    def test_websocket_rejects_foreign_origin(self):
        self.login()
        with self.assertRaises(WebSocketDisconnect) as cm:
            with self.client.websocket_connect("/novnc/websockify", headers={"origin": "http://evil.test"}):
                pass
        self.assertEqual(cm.exception.code, 1008)

    def test_websocket_rejects_missing_origin(self):
        self.login()
        with self.assertRaises(WebSocketDisconnect) as cm:
            with self.client.websocket_connect("/novnc/websockify"):
                pass
        self.assertEqual(cm.exception.code, 1008)

    def test_websocket_binary_echo(self):
        self.login()
        with patch.object(gateway, "connect", fake_connect):
            with self.client.websocket_connect("/novnc/websockify", headers={"origin": "http://testserver"}, subprotocols=["binary"]) as ws:
                ws.send_bytes(b"\\x00\\x01\\x02")
                self.assertEqual(ws.receive_bytes(), b"\\x00\\x01\\x02")

    def test_websocket_text_echo(self):
        self.login()
        with patch.object(gateway, "connect", fake_connect):
            with self.client.websocket_connect("/novnc/websockify", headers={"origin": "http://testserver"}, subprotocols=["binary"]) as ws:
                ws.send_text("ping")
                self.assertEqual(ws.receive_text(), "ping")


if __name__ == "__main__":
    unittest.main(verbosity=2)
