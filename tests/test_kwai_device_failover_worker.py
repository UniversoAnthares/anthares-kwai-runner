import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_queue_callback_requires_json_argv(self):
        with patch.dict(os.environ, {"ANTHARES_QUEUE_STARTED_COMMAND_JSON": '["python","callback.py"]'}):
            self.assertEqual(worker.callback_argv("started"), ["python", "callback.py"])

    def test_queue_callback_rejects_shell_string(self):
        with patch.dict(os.environ, {"ANTHARES_QUEUE_STARTED_COMMAND_JSON": "python callback.py"}):
            with self.assertRaises(RuntimeError):
                worker.callback_argv("started")

    def test_published_pending_ack_is_persisted_before_callback_repair(self):
        original = worker.ACK_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.ACK_PATH = Path(td) / "ack.json"
                worker.mark_pending_ack("job-1", "physical_android")
                state = worker.load_ack_state()
                self.assertEqual(state["job-1"]["state"], "published_pending_ack")
                self.assertEqual(state["job-1"]["executor"], "physical_android")
                worker.mark_acknowledged("job-1")
                state = worker.load_ack_state()
                self.assertEqual(state["job-1"]["state"], "completed_acknowledged")
        finally:
            worker.ACK_PATH = original

    def test_retry_pending_ack_never_republishes(self):
        original = worker.ACK_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.ACK_PATH = Path(td) / "ack.json"
                worker.mark_pending_ack("job-2", "memu_android")
                with patch.object(worker, "queue_callback", return_value=(True, "ok")) as callback:
                    self.assertEqual(worker.retry_pending_ack("job-2"), 0)
                callback.assert_called_once_with("complete", "memu_android")
                self.assertEqual(worker.load_ack_state()["job-2"]["state"], "completed_acknowledged")
        finally:
            worker.ACK_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
