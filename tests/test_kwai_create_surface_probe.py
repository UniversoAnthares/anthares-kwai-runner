"""Hosted offline QA for the read-only Codespaces create-surface probe."""
import importlib.util
import inspect
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / ".devcontainer" / "kwai-create-surface-probe.py"
spec = importlib.util.spec_from_file_location("kwai_create_surface_probe", PROBE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class KwaiCreateSurfaceProbeTests(unittest.TestCase):
    def test_login_gate_fails_closed(self):
        result = mod.classify_page_signals([{
            "login_gate_visible": True,
            "file_input_present": True,
            "create_control_visible": True,
            "upload_control_visible": True,
            "publish_control_visible": False,
            "studio_tab_present": True,
        }])
        self.assertTrue(result["kwai_tab_present"])
        self.assertTrue(result["create_or_upload_visible"])
        self.assertFalse(result["operational_create_surface"])

    def test_existing_create_surface_is_operational_without_login_gate(self):
        result = mod.classify_page_signals([{
            "login_gate_visible": False,
            "file_input_present": False,
            "create_control_visible": False,
            "upload_control_visible": True,
            "publish_control_visible": False,
            "studio_tab_present": False,
        }])
        self.assertTrue(result["create_or_upload_visible"])
        self.assertTrue(result["operational_create_surface"])
        self.assertTrue(result["read_only_probe"])
        self.assertFalse(result["session_exported"])

    def test_no_kwai_pages_fails_closed(self):
        result = mod.classify_page_signals([])
        self.assertFalse(result["kwai_tab_present"])
        self.assertFalse(result["operational_create_surface"])

    def test_file_input_alone_can_prove_create_surface(self):
        result = mod.classify_page_signals([{
            "login_gate_visible": False,
            "file_input_present": True,
            "studio_tab_present": True,
        }])
        self.assertTrue(result["file_input_present"])
        self.assertTrue(result["studio_tab_present"])
        self.assertTrue(result["operational_create_surface"])

    def test_source_is_read_only_and_never_launches_or_exports_session(self):
        source = PROBE.read_text()
        forbidden = (
            "launch(", "launch_persistent_context(", "storage_state(", ".cookies(",
            "screenshot(", "set_input_files(", ".click(", "localStorage", "sessionStorage",
        )
        for needle in forbidden:
            self.assertNotIn(needle, source, needle)
        self.assertIn("inspect_existing_pages", source)
        self.assertIn("context, \"pages\"", source)

    def test_public_contract_is_boolean_only(self):
        result = mod.classify_page_signals([{"upload_control_visible": True}])
        self.assertTrue(result)
        self.assertTrue(all(isinstance(v, bool) for v in result.values()))
        self.assertNotIn("url", result)
        self.assertNotIn("text", result)
        self.assertNotIn("handle", result)
        self.assertNotIn("cookie", result)


if __name__ == "__main__":
    unittest.main()
