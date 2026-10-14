"""Fail-closed Android provider selection tests; selection is not execution."""
import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import android_executor_router as router

MANIFEST = router.load_manifest()


def ready(queue=0, authenticated=True):
    return {
        "online": True,
        "healthy": True,
        "ready": True,
        "authenticated": authenticated,
        "queue_seconds": queue,
        "consecutive_failures": 0,
        "last_failure_class": "",
    }


class AndroidExecutorRoutingTests(unittest.TestCase):
    def test_physical_device_is_primary(self):
        self.assertEqual(MANIFEST["android_execution"]["priority"][0], "physical_android")
        self.assertEqual(router.choose(MANIFEST, {"physical_android": ready(), "memu_android": ready()}, "kwai_publish"), "physical_android")

    def test_memu_is_never_primary_while_physical_ready(self):
        self.assertNotEqual(router.choose(MANIFEST, {"physical_android": ready(), "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_memu_fallback_when_physical_missing(self):
        self.assertEqual(router.choose(MANIFEST, {"memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_memu_fallback_when_physical_explicitly_offline(self):
        physical = {"online": False, "healthy": False, "ready": False, "authenticated": False, "queue_seconds": 0}
        self.assertEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_single_device_failure_does_not_open_circuit(self):
        physical = ready()
        physical.update({"healthy": False, "ready": False, "last_failure_class": "adb", "consecutive_failures": 1})
        self.assertNotEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_three_device_failures_open_memu_fallback(self):
        physical = ready()
        physical.update({"healthy": False, "ready": False, "last_failure_class": "adb", "consecutive_failures": 3})
        self.assertEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_policy_failure_never_retries_on_memu(self):
        physical = ready()
        physical.update({"healthy": False, "ready": False, "last_failure_class": "policy", "consecutive_failures": 99})
        self.assertNotEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_content_failure_never_retries_on_memu(self):
        physical = ready()
        physical.update({"healthy": False, "ready": False, "last_failure_class": "content", "consecutive_failures": 99})
        self.assertNotEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_kwai_publish_requires_authenticated_executor(self):
        self.assertIsNone(router.choose(MANIFEST, {"physical_android": ready(authenticated=False)}, "kwai_publish"))

    def test_queue_exactly_at_threshold_is_allowed(self):
        self.assertEqual(router.choose(MANIFEST, {"physical_android": ready(90)}, "kwai_publish"), "physical_android")

    def test_queue_over_threshold_can_fall_through(self):
        physical = ready(91)
        physical["online"] = False
        self.assertEqual(router.choose(MANIFEST, {"physical_android": physical, "memu_android": ready()}, "kwai_publish"), "memu_android")

    def test_disabled_provider_skipped(self):
        s = ready(); s["disabled"] = True
        self.assertIsNone(router.choose(MANIFEST, {"physical_android": s}, "kwai_publish"))

    def test_malformed_json_status_fails_closed(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_STATUS_JSON": "{not-json"}):
            self.assertEqual(router.load_state(), {})

    def test_main_reports_selection_not_dispatch(self):
        payload = '{"physical_android":{"online":true,"healthy":true,"ready":true,"authenticated":true,"queue_seconds":0}}'
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "kwai_publish", "ANTHARES_EXECUTOR_STATUS_JSON": payload}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(router.main(), 0)
        text = output.getvalue()
        self.assertIn("ANDROID_EXECUTOR_SELECTED=physical_android", text)
        self.assertIn("ANDROID_EXECUTOR_DISPATCHED=0", text)
        self.assertIn("ANDROID_EXECUTOR_REASON=primary_physical_device", text)

    def test_main_rejects_unknown_workload(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "manual_and_publish"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(router.main(), 2)

    def test_firebase_only_is_not_valid_for_manual_login(self):
        m = router.load_manifest(); m["providers"]["firebase_test_lab"]["active"] = True
        self.assertIsNone(router.choose(m, {"firebase_test_lab": ready()}, workload="manual_auth"))

    def test_render_never_selected_for_android(self):
        m = router.load_manifest(); m["android_execution"]["priority"].insert(0, "render")
        self.assertEqual(router.choose(m, {"render": ready(), "physical_android": ready()}, "kwai_publish"), "physical_android")


if __name__ == "__main__":
    unittest.main(verbosity=2)
