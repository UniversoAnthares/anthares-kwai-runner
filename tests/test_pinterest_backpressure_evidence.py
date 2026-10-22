import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from tools import cortes_buffer_pinterest_cloud as publisher
from tools.pinterest_operational_evidence import inspect


class BufferBackpressureProof(unittest.TestCase):
    def test_pending_eight_is_explicit_blocker_without_new_post(self):
        def queue(action, payload=None):
            if action == "cooldown-status":
                return {"active": False}
            if action == "pending":
                return {"jobs": [{"id": str(i)} for i in range(8)]}
            raise AssertionError("Unexpected network action: " + action)
        with patch.object(publisher, "cloud_only"), \
             patch.object(publisher, "queue", side_effect=queue), \
             patch.object(publisher, "reconcile", return_value=0), \
             patch.object(publisher, "publish_once") as publish:
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(publisher.main(), 0)
            publish.assert_not_called()
        report = inspect(out.getvalue(), event="schedule", run_id="123", conclusion="success")
        self.assertEqual(report["result"], "WAITING_BUFFER_DELIVERY")
        self.assertEqual(report["buffer_pending_count"], 8)
        self.assertEqual(report["new_public_pin_count"], 0)


if __name__ == "__main__":
    unittest.main()
