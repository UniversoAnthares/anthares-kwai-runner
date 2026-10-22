import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from social_adapters.buffer_three_channels import BufferBlocked
from tools import cortes_buffer_pinterest_cloud as p


class PinterestBatchReceipts(unittest.TestCase):
    def setUp(self):
        self.jobs = [
            {"id": "job-" + str(i), "remote_id": "bufferid" + str(i)}
            for i in range(8)
        ]

    def test_eight_receipts_one_graphql_read_and_only_sent_confirmed(self):
        calls = []
        def queue(action, payload=None):
            calls.append((action, payload))
            if action == "pending":
                return {"jobs": self.jobs}
            if action == "reconcile":
                return {"ok": True}
            raise AssertionError(action)

        def api(query):
            self.assertEqual(query.count(": post(input:"), 8)
            self.assertNotIn("dueAt", query)
            return {
                "p"+str(i): {
                    "id": "bufferid"+str(i),
                    "channelId": p.PINTEREST_ID,
                    "schedulingType": "automatic",
                    "status": "sent" if i < 2 else "scheduled",
                    "dueAt": "2030-01-01T12:00:00Z",
                    "externalLink": ("https://www.pinterest.com/pin/"+str(819514463494250001+i)
                                     if i < 2 else ""),
                }
                for i in range(8)
            }

        with patch.object(p, "queue", side_effect=queue), patch.object(p, "api", side_effect=api) as requested:
            with redirect_stdout(io.StringIO()):
                total = p.reconcile()
        self.assertEqual(total, 2)
        requested.assert_called_once()
        confirms = [payload for action, payload in calls if action == "reconcile"]
        self.assertEqual(len(confirms), 2)
        self.assertEqual({x["remote_id"] for x in confirms}, {"bufferid0", "bufferid1"})
        self.assertEqual(len([x for x in calls if x[0] == "pending"]), 1)

    def test_spoofed_sent_row_never_confirms(self):
        def api(query):
            return {
                "p"+str(i): {
                    "id": "WRONG" if i == 0 else "bufferid"+str(i),
                    "channelId": p.PINTEREST_ID,
                    "schedulingType": "automatic",
                    "status": "sent" if i == 0 else "scheduled",
                    "dueAt": "2030-01-01T12:00:00Z",
                    "externalLink": "https://www.pinterest.com/pin/819514463494250001",
                } for i in range(8)
            }
        def queue(action, payload=None):
            if action == "pending":
                return {"jobs": self.jobs}
            raise AssertionError("Unexpected state mutation: " + action)
        with patch.object(p, "queue", side_effect=queue), patch.object(p, "api", side_effect=api):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(p.reconcile(), 0)

    def test_graphql_batch_rejection_falls_back_to_two_rotated_ids(self):
        inspected = []
        def queue(action, payload=None):
            if action == "pending":
                return {"jobs": self.jobs}
            raise AssertionError(action)
        def single(remote):
            inspected.append(remote)
            return None
        with patch.object(p, "queue", side_effect=queue), \
             patch.object(p, "verify_sent_posts_batch", side_effect=BufferBlocked("BUFFER_GRAPHQL_OR_DATA_ERROR")), \
             patch.object(p, "verify_sent_post", side_effect=single), \
             patch.object(p.time, "time", return_value=0):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(p.reconcile(), 0)
        self.assertEqual(inspected, ["bufferid0", "bufferid1"])

    def test_rate_limit_stops_without_retries(self):
        with patch.object(p, "queue", return_value={"jobs": self.jobs}), \
             patch.object(p, "verify_sent_posts_batch", side_effect=BufferBlocked("BUFFER_HTTP_429")), \
             patch.object(p, "verify_sent_post") as single:
            with self.assertRaises(BufferBlocked):
                p.reconcile()
            single.assert_not_called()


if __name__ == "__main__":
    unittest.main()
