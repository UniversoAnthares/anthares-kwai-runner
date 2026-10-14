import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kwai_device_failover_worker as worker


class KwaiDeviceFailoverWorkerTests(unittest.TestCase):
    def test_adb_failure_is_device_failure(self):
        self.assertEqual(worker.classify_failure("adb: device offline", 70), "device")

    def test_ui_timeout_is_device_failure(self):
        self.assertEqual(worker.classify_failure("uiautomator timed out", 79), "device")

    def test_policy_never_enters_device_failover(self):
        self.assertEqual(worker.classify_failure("content policy rejected", 70), "platform")

    def test_human_verification_never_enters_device_failover(self):
        self.assertEqual(worker.classify_failure("human-verification", 91), "platform")

    def test_irreversible_boundary_is_uncertain(self):
        self.assertEqual(worker.classify_failure("STATE=PUBLISH_REQUESTED", 90), "uncertain")

    def test_health_opens_circuit_after_three_device_failures(self):
        original = worker.STATE_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.STATE_PATH = Path(td) / "health.json"
                h = {}
                worker.record_result(h, "physical_android", False, "device", "one")
                worker.record_result(h, "physical_android", False, "device", "two")
                worker.record_result(h, "physical_android", False, "device", "three")
                self.assertEqual(h["physical_android"]["consecutive_failures"], 3)
                self.assertTrue(h["physical_android"]["degraded"])
                worker.record_result(h, "physical_android", True)
                self.assertEqual(h["physical_android"]["consecutive_failures"], 0)
                self.assertFalse(h["physical_android"]["degraded"])
        finally:
            worker.STATE_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
