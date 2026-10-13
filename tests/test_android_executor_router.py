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


def ready(queue=0):
    return {"healthy": True, "ready": True, "queue_seconds": queue}


class AndroidExecutorRoutingTests(unittest.TestCase):
    def test_circleci_first_when_ready(self):
        self.assertEqual(router.choose(MANIFEST, {"circleci": ready(), "bitrise": ready()}), "circleci")

    def test_queue_over_threshold_fails_over_to_bitrise(self):
        self.assertEqual(router.choose(MANIFEST, {"circleci": ready(91), "bitrise": ready()}), "bitrise")

    def test_queue_exactly_at_threshold_is_allowed(self):
        self.assertEqual(router.choose(MANIFEST, {"circleci": ready(90)}), "circleci")

    def test_firebase_only_is_not_valid_for_manual_login(self):
        self.assertIsNone(router.choose(MANIFEST, {"firebase_test_lab": ready()}, workload="manual_auth"))

    def test_firebase_can_handle_generic_noninteractive_android(self):
        self.assertEqual(router.choose(MANIFEST, {"firebase_test_lab": ready()}, workload="generic_android"), "firebase_test_lab")

    def test_manual_auth_prefers_bitrise_over_firebase(self):
        self.assertEqual(router.choose(MANIFEST, {"circleci": ready(91), "bitrise": ready(), "firebase_test_lab": ready()}, workload="manual_auth"), "bitrise")

    def test_disabled_provider_skipped(self):
        s = ready()
        s["disabled"] = True
        self.assertIsNone(router.choose(MANIFEST, {"circleci": s}))

    def test_unhealthy_provider_skipped(self):
        s = ready()
        s["healthy"] = False
        self.assertIsNone(router.choose(MANIFEST, {"circleci": s}))

    def test_invalid_queue_does_not_crash_router(self):
        self.assertEqual(router.choose(MANIFEST, {"circleci": ready("unknown"), "bitrise": ready()}), "bitrise")

    def test_negative_queue_fails_closed(self):
        self.assertIsNone(router.choose(MANIFEST, {"circleci": ready(-1)}))

    def test_missing_status_does_not_assume_ready(self):
        self.assertIsNone(router.choose(MANIFEST, {}))

    def test_ineligible_render_never_chosen_for_android(self):
        m = router.load_manifest()
        m["android_execution"]["priority"].insert(0, "render")
        self.assertEqual(router.choose(m, {"render": ready(), "circleci": ready()}), "circleci")

    def test_explicit_inactive_provider_skipped(self):
        m = router.load_manifest()
        m["providers"]["circleci"]["active"] = False
        self.assertIsNone(router.choose(m, {"circleci": ready()}))

    def test_main_reports_selection_not_dispatch(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "manual_auth", "ANTHARES_EXECUTOR_STATUS_JSON": '{"circleci":{"healthy":true,"ready":true,"queue_seconds":0}}'}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(router.main(), 0)
        text = output.getvalue()
        self.assertIn("ANDROID_EXECUTOR_SELECTED=circleci", text)
        self.assertIn("ANDROID_EXECUTOR_DISPATCHED=0", text)
        self.assertIn("ANDROID_EXECUTOR_SELECTION_ONLY=1", text)

    def test_main_rejects_unknown_workload(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "manual_and_publish"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(router.main(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
