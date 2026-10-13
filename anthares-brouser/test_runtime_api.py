"""Runtime API regression checks; no external browser or credentials needed."""
import importlib.util
import os
import pathlib
import unittest
from unittest.mock import patch

os.environ["CONTROL_TOKEN"] = "ci-only-test-token"
spec = importlib.util.spec_from_file_location("anthares_browser_app", pathlib.Path(__file__).with_name("app.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from fastapi.testclient import TestClient

class BrowserRuntimeAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(module.app)

    def test_health_is_liveness_not_browser_readiness(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readiness_path"], "/ready")

    def test_control_requires_authentication(self):
        self.assertEqual(self.client.get("/status").status_code, 401)
        self.assertEqual(self.client.get("/status", headers={"Authorization": "Bearer incorrect"}).status_code, 401)

    def test_readiness_fails_closed_without_browser(self):
        with patch.object(module, "chromium_processes", return_value=[]):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["detail"]["ok"])
        self.assertFalse(response.json()["detail"]["durable_volume_verified"])

if __name__ == "__main__":
    unittest.main()
