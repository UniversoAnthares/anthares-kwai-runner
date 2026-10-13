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
    def test_github_actions_first_when_ready(self):
        self.assertEqual(router.choose(MANIFEST, {"github_actions": ready(), "bitrise": ready()}), "github_actions")

    def test_queue_over_threshold_fails_over_to_proven_bitrise(self):
        m = router.load_manifest()
        m["providers"]["bitrise"]["active"] = True
        self.assertEqual(router.choose(m, {"github_actions": ready(91), "bitrise": ready()}), "bitrise")

    def test_queue_exactly_at_threshold_is_allowed(self):
        self.assertEqual(router.choose(MANIFEST, {"github_actions": ready(90)}), "github_actions")

    def test_firebase_only_is_not_valid_for_manual_login(self):
        self.assertIsNone(router.choose(MANIFEST, {"firebase_test_lab": ready()}, workload="manual_auth"))

    def test_unspecified_workload_never_routes_manual_login_to_firebase(self):
        self.assertIsNone(router.choose(MANIFEST, {"firebase_test_lab": ready()}))

    def test_firebase_can_handle_generic_noninteractive_android(self):
        m = router.load_manifest()
        m["providers"]["firebase_test_lab"]["active"] = True
        self.assertEqual(router.choose(m, {"firebase_test_lab": ready()}, workload="generic_android"), "firebase_test_lab")

    def test_manual_auth_prefers_bitrise_over_firebase(self):
        m = router.load_manifest()
        m["providers"]["bitrise"]["active"] = True
        self.assertEqual(router.choose(m, {"github_actions": ready(91), "bitrise": ready(), "firebase_test_lab": ready()}, workload="manual_auth"), "bitrise")

    def test_disabled_provider_skipped(self):
        s = ready()
        s["disabled"] = True
        self.assertIsNone(router.choose(MANIFEST, {"github_actions": s}))

    def test_unhealthy_provider_skipped(self):
        s = ready()
        s["healthy"] = False
        self.assertIsNone(router.choose(MANIFEST, {"circleci": s}))

    def test_invalid_queue_does_not_crash_router(self):
        m = router.load_manifest()
        m["providers"]["bitrise"]["active"] = True
        self.assertEqual(router.choose(m, {"github_actions": ready("unknown"), "bitrise": ready()}), "bitrise")

    def test_negative_queue_fails_closed(self):
        self.assertIsNone(router.choose(MANIFEST, {"github_actions": ready(-1)}))

    def test_missing_status_does_not_assume_ready(self):
        self.assertIsNone(router.choose(MANIFEST, {}))

    def test_ineligible_render_never_chosen_for_android(self):
        m = router.load_manifest()
        m["android_execution"]["priority"].insert(0, "render")
        self.assertEqual(router.choose(m, {"render": ready(), "github_actions": ready()}), "github_actions")

    def test_explicit_inactive_provider_skipped(self):
        m = router.load_manifest()
        m["providers"]["github_actions"]["active"] = False
        self.assertIsNone(router.choose(m, {"github_actions": ready()}))

    def test_main_reports_selection_not_dispatch(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "manual_auth", "ANTHARES_EXECUTOR_STATUS_JSON": '{"github_actions":{"healthy":true,"ready":true,"queue_seconds":0}}'}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(router.main(), 0)
        text = output.getvalue()
        self.assertIn("ANDROID_EXECUTOR_SELECTED=github_actions", text)
        self.assertIn("ANDROID_EXECUTOR_DISPATCHED=0", text)
        self.assertIn("ANDROID_EXECUTOR_SELECTION_ONLY=1", text)

    def test_malformed_json_status_fails_closed(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_STATUS_JSON": "{not-json"}):
            self.assertEqual(router.load_state(), {})

    def test_array_json_status_fails_closed(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_STATUS_JSON": "[]"}):
            self.assertEqual(router.load_state(), {})

    def test_retired_circleci_never_selected_even_if_healthy(self):
        self.assertNotIn("circleci", MANIFEST["android_execution"]["priority"])
        self.assertIsNone(router.choose(MANIFEST, {"circleci": ready()}))

    def test_unproven_bitrise_is_disabled_until_live_proof(self):
        self.assertIsNone(router.choose(MANIFEST, {"bitrise": ready()}))

    def test_browser_routing_primary_gitlab(self):
        self.assertEqual(MANIFEST["browser_execution"]["priority"][0], "gitlab")
        self.assertTrue(MANIFEST["providers"]["gitlab"]["active"])

    def test_main_rejects_unknown_workload(self):
        with patch.dict(os.environ, {"ANTHARES_EXECUTOR_WORKLOAD": "manual_and_publish"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(router.main(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
