import unittest

from android_executor_router import choose, load_manifest


class AndroidExecutorRoutingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest()

    def test_role_specific_priorities(self):
        self.assertEqual(self.manifest["android_execution"]["priority"], ["circleci", "bitrise", "firebase_test_lab"])
        self.assertEqual(self.manifest["browser_execution"]["priority"], ["circleci", "bitrise", "render"])

    def test_ineligible_and_retired_providers_are_not_android_active(self):
        active = self.manifest["android_execution"]["priority"]
        self.assertNotIn("cirrus", active)
        self.assertNotIn("render", active)
        self.assertNotIn("gitlab", active)
        self.assertNotIn("github_actions", active)
        for name in ("cirrus", "render", "gitlab", "github_actions"):
            self.assertIs(self.manifest["providers"][name].get("android_eligible"), False)

    def test_missing_live_state_fails_closed(self):
        self.assertIsNone(choose(self.manifest, {}))

    def test_circleci_primary(self):
        state = {"circleci": {"healthy": True, "ready": True, "queue_seconds": 10}, "bitrise": {"healthy": True, "ready": True, "queue_seconds": 0}}
        self.assertEqual(choose(self.manifest, state), "circleci")

    def test_queue_failover_to_bitrise(self):
        state = {"circleci": {"healthy": True, "ready": True, "queue_seconds": 91}, "bitrise": {"healthy": True, "ready": True, "queue_seconds": 2}}
        self.assertEqual(choose(self.manifest, state), "bitrise")

    def test_firebase_is_tertiary(self):
        state = {"circleci": {"healthy": False, "ready": False}, "bitrise": {"healthy": False, "ready": False}, "firebase_test_lab": {"healthy": True, "ready": True, "queue_seconds": 0}}
        self.assertEqual(choose(self.manifest, state), "firebase_test_lab")


if __name__ == "__main__":
    unittest.main()
