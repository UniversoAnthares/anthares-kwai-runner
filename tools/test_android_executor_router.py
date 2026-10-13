import unittest

from android_executor_router import choose, load_manifest


class AndroidExecutorRoutingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest()

    def test_active_provider_order(self):
        self.assertEqual(self.manifest["android_execution"]["priority"], ["circleci", "bitrise", "firebase_test_lab"])
        self.assertEqual(self.manifest["browser_execution"]["priority"], ["circleci", "gitlab", "bitrise"])

    def test_retired_provider_cannot_be_active(self):
        retired = set(self.manifest.get("retired_providers", {}))
        active = set(self.manifest["android_execution"]["priority"]) | set(self.manifest["browser_execution"]["priority"])
        self.assertTrue(retired.isdisjoint(active))
        self.assertIn("cirrus", retired)

    def test_missing_live_state_is_not_ready(self):
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
