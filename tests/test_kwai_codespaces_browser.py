"""Hosted offline QA for the private browser-only Kwai Codespaces handoff."""
import json
import os
import runpy
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / ".devcontainer"
GUARD = DEV / "kwai-identity-guard.py"


class CodespacesBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = runpy.run_path(str(GUARD), run_name="kwai_guard_tests")

    def test_devcontainer_private_port_scope(self):
        config = json.loads((DEV / "devcontainer.json").read_text())
        self.assertEqual(config["forwardPorts"], [6080, 8765])
        self.assertNotIn(5900, config["forwardPorts"])
        self.assertNotIn(9222, config["forwardPorts"])
        self.assertEqual(config["remoteEnv"]["KWAI_EXPECTED_HANDLE"], "universo.anthares")
        self.assertIn("kwai-install.sh", config["postCreateCommand"])
        self.assertIn("kwai-start.sh", config["postStartCommand"])

    def test_shell_scripts_parse(self):
        for name in ("kwai-install.sh", "kwai-start.sh", "kwai-clear-session.sh"):
            result = subprocess.run(["bash", "-n", str(DEV / name)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, name + ": " + result.stderr)

    def test_chrome_and_vnc_listen_loopback_only(self):
        script = (DEV / "kwai-start.sh").read_text()
        self.assertIn("127.0.0.1:6080", script)
        self.assertIn("127.0.0.1:5900", script)
        self.assertIn("--remote-debugging-address=127.0.0.1", script)
        self.assertIn("-localhost -rfbport 5900", script)
        self.assertNotIn("cloudflared", script)
        self.assertNotIn("ngrok", script)
        self.assertNotIn("adb ", script)

    def test_identity_fail_closed_on_empty_evidence(self):
        self.assertFalse(self.mod["assess_evidence"]({}))
        self.assertFalse(self.mod["assess_evidence"]({"login_controls_absent": True}))

    def test_identity_requires_independent_menu_proof(self):
        evidence = {
            "profile_url_matches": True,
            "owner_edit_control_visible": True,
            "account_menu_handle_matches": False,
            "login_controls_absent": True,
        }
        self.assertFalse(self.mod["assess_evidence"](evidence))
        evidence["account_menu_handle_matches"] = True
        self.assertTrue(self.mod["assess_evidence"](evidence))
        evidence["login_controls_absent"] = False
        self.assertFalse(self.mod["assess_evidence"](evidence))

    def test_inspector_never_exports_browser_state(self):
        source = GUARD.read_text()
        self.assertIn('"persistence_permitted"] = False', source)
        self.assertIn('"server_identity_verified"] = False', source)
        self.assertNotIn("storage_state(", source)
        self.assertNotIn("context.cookies(", source)
        self.assertNotIn("page.screenshot(", source)
        self.assertIn("hmac.compare_digest", source)
        self.assertIn("Cache-Control", source)

    def test_private_profile_not_in_repository(self):
        start = (DEV / "kwai-start.sh").read_text()
        self.assertIn('${HOME}/.kwai-remote-private', start)
        self.assertIn("--user-data-dir=", start)
        self.assertNotIn("git add", start)
        self.assertIn("chrome-profile", (DEV / "kwai-clear-session.sh").read_text())

    def test_guard_local_http_smoke(self):
        # Run in the hosted GitHub runner, not on the user's PC.
        proc = subprocess.Popen(
            [sys.executable, str(GUARD)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "KWAI_EXPECTED_HANDLE": "universo.anthares"},
        )
        try:
            ready = False
            for _ in range(30):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1) as res:
                        body = json.loads(res.read())
                        self.assertFalse(body["identity_verified"])
                        ready = True
                        break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.1)
            self.assertTrue(ready, "local identity guard failed to start")
            req = urllib.request.Request(
                "http://127.0.0.1:8765/check",
                data=b"csrf=incorrect",
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(req, timeout=3)
            self.assertEqual(exc.exception.code, 403)
            with urllib.request.urlopen("http://127.0.0.1:8765/", timeout=3) as res:
                self.assertIn(b"Verificar identidade", res.read())
                self.assertEqual(res.headers["X-Frame-Options"], "DENY")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    unittest.main()
