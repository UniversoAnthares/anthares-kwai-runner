import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "infra" / "anthares_runtime_browser_local.py"


class XBrowserHealthIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(FILE.read_text(encoding="utf-8"))

    def test_health_never_launches_browser_or_waits_on_lock(self):
        node = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == "health")
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        self.assertNotIn("_ensure_browser", names)
        self.assertNotIn("sync_playwright", names)
        self.assertNotIn("_LOCK", names)
        # Compile only the isolated function: no Playwright/network needed.
        unit = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(unit)
        scope = {"Any": object, "_secret": lambda: "configured",
                 "_CONTEXT": None, "_BROWSER": None, "_RESTORE_STATUS": "empty",
                 "_LAST_PERSIST_OK": False}
        exec(compile(unit, str(FILE), "exec"), scope)
        result = scope["health"]()
        self.assertTrue(result["healthy"])
        self.assertFalse(result["chromium_running"])
        self.assertTrue(result["browser_preflight_required"])

    def test_chromium_launch_has_bounded_timeout(self):
        launch = [
            node for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == "launch"
        ]
        self.assertEqual(len(launch), 1)
        timeouts = [kw.value.value for kw in launch[0].keywords
                    if kw.arg == "timeout" and isinstance(kw.value, ast.Constant)]
        self.assertEqual(timeouts, [25000])

    def test_x_health_reports_browser_state_independently(self):
        source = (ROOT / "infra" / "x_runtime_worker.py").read_text(encoding="utf-8")
        self.assertIn('browser_ready=bool(h.get("chromium_running"))', source)
        self.assertIn('browser_preflight_required=bool(h.get("browser_preflight_required"))', source)


if __name__ == "__main__":
    unittest.main()
