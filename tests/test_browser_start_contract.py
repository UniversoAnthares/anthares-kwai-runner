"""Static deployment contract for Anthares Browser lifecycle and port isolation."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "anthares-brouser" / "start.sh"


class BrowserStartContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_bash_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_render_port_honored(self):
        self.assertIn("API_PORT=${PORT:-8080}", self.source)
        self.assertIn('--port "$API_PORT"', self.source)

    def test_websockify_remains_loopback(self):
        self.assertIn("127.0.0.1:6080 localhost:5900", self.source)

    def test_vnc_remains_loopback(self):
        self.assertIn("-rfbport 5900 -localhost", self.source)

    def test_cdp_remains_loopback(self):
        self.assertIn("--remote-debugging-address=127.0.0.1", self.source)

    def test_control_api_stays_up_for_diagnostics(self):
        self.assertIn('wait "$API_PID"', self.source)
        self.assertNotIn('wait -n "$API_PID"', self.source)

    def test_required_secrets(self):
        self.assertIn('"${CONTROL_TOKEN:?CONTROL_TOKEN is required}"', self.source)
        self.assertIn('"${VNC_PASSWORD:?VNC_PASSWORD is required}"', self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
