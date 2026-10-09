#!/usr/bin/env python3
"""Non-secret offline checkpoint acceptance; no network or Android required."""
import os
import pathlib
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SCRIPT = pathlib.Path(__file__).with_name("kwai_android_checkpoint.sh")
state = {"payload": None}

class Storage(BaseHTTPRequestHandler):
    def do_PUT(self):
        n = int(self.headers["Content-Length"])
        if self.headers.get("Authorization") != "Bearer test-token":
            self.send_error(403); return
        state["payload"] = self.rfile.read(n)
        self.send_response(200); self.end_headers()
    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer test-token" or not state["payload"]:
            self.send_error(404); return
        self.send_response(200); self.end_headers(); self.wfile.write(state["payload"])
    def log_message(self, *_): pass

with tempfile.TemporaryDirectory() as root:
    root = pathlib.Path(root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Storage)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    avd = root / "source"; avd.mkdir()
    (avd / "kwai-speed.avd").mkdir()
    (avd / "kwai-speed.avd" / "userdata-qemu.img").write_bytes(b"test-image-state")
    (avd / "kwai-speed.ini").write_text("path=kwai-speed.avd\n")
    # Fake adb supports stop on non-Android CI.
    fake = root / "bin"; fake.mkdir()
    adb = fake / "adb"; adb.write_text("#!/bin/sh\nexit 0\n"); adb.chmod(0o755)
    env = dict(os.environ, AVD_DIR=str(avd), KWAI_CHECKPOINT_KEY="temporary-test-key",
               KWAI_PRIVATE_CHECKPOINT_URL=f"http://127.0.0.1:{server.server_port}/checkpoint",
               KWAI_PRIVATE_CHECKPOINT_TOKEN="test-token", PATH=str(fake)+os.pathsep+os.environ["PATH"],
               KWAI_TEST_ALLOW_HTTP_LOOPBACK="1")
    subprocess.run(["bash", str(SCRIPT), "save"], env=env, check=True, capture_output=True)
    assert state["payload"] and b"test-image-state" not in state["payload"]
    for i in (1, 2):
        dst = root / f"restore-{i}"; dst.mkdir()
        subprocess.run(["bash", str(SCRIPT), "restore"], env=dict(env, AVD_DIR=str(dst)), check=True, capture_output=True)
        assert (dst / "kwai-speed.avd" / "userdata-qemu.img").read_bytes() == b"test-image-state"
        print(f"CHECKPOINT_INDEPENDENT_RESTORE_{i}=PROVEN_SYNTHETIC")
    server.shutdown()
print("CHECKPOINT_ENCRYPTION_ROUNDTRIP=PROVEN_SYNTHETIC; AUTH_PERSISTENCE=NOT_TESTED")
