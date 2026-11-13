"""No-network proof for future persistent cloud Android's dual Kwai lease client."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from tools import kwai_persistent_cloud_queue as cloud

TOKEN = "A" * 43
JOB_ID = "kwai-cortes-" + "a" * 18


class CloudQueueTests(unittest.TestCase):
    def test_target_and_expected_account_cannot_be_overridden(self):
        for account in cloud.ACCOUNTS:
            with self.subTest(account=account):
                d = cloud.envelope(account, "lease", {})
                self.assertEqual(d["target_key"], "kwai:" + account)
                self.assertEqual(d["expected_account"], account)
                self.assertEqual(d["lease_seconds"], 180)
                with self.assertRaisesRegex(cloud.CloudQueueError, "TARGET"):
                    cloud.envelope(account, "lease", {"target_key": "kwai:wrong"})
                with self.assertRaisesRegex(cloud.CloudQueueError, "ACCOUNT"):
                    cloud.envelope(account, "lease", {"expected_account": "wrong"})

    def test_fence_is_strict_and_no_unknown_write_actions(self):
        for action in ("renew", "start", "confirm", "fail"):
            with self.subTest(action=action):
                with self.assertRaisesRegex(cloud.CloudQueueError, "FENCE"):
                    cloud.envelope("lucasrosalem", action,
                                   {"id": JOB_ID, "lease_generation": 0})
        with self.assertRaises(cloud.CloudQueueError):
            cloud.envelope("lucasrosalem", "delete", {})
        with self.assertRaises(cloud.CloudQueueError):
            cloud.envelope("lucasrosalem", "start",
                           {"id": JOB_ID, "lease_generation": True})

    def test_confirm_requires_external_attestation(self):
        base = {"id": JOB_ID, "lease_generation": 1,
                "remote_id": "abc123",
                "confirmation_evidence": {
                    "account": "universoanthares",
                    "attestation_hmac": "d" * 64}}
        with self.assertRaisesRegex(cloud.CloudQueueError, "CONFIRMATION"):
            cloud.envelope("lucasrosalem", "confirm", base)
        good = dict(base, confirmation_evidence={
            "account": "lucasrosalem", "attestation_hmac": "a" * 64})
        self.assertEqual(cloud.envelope("lucasrosalem", "confirm", good)
                         ["expected_account"], "lucasrosalem")

    def test_fail_requires_uncertain_quarantine(self):
        with self.assertRaisesRegex(cloud.CloudQueueError, "QUARANTINE"):
            cloud.envelope("universoanthares", "fail", {
                "id": JOB_ID, "lease_generation": 1,
                "published_possible": False})
        good = cloud.envelope("universoanthares", "fail", {
            "id": JOB_ID, "lease_generation": 1,
            "published_possible": True})
        self.assertTrue(good["published_possible"])

    def test_lease_and_renew_ttl_bound(self):
        for ttl in (0, 59, 601, -1, "180", True):
            for action in ("lease", "renew"):
                with self.subTest(ttl=ttl, action=action):
                    payload = {"lease_seconds": ttl}
                    if action == "renew":
                        payload.update(id=JOB_ID, lease_generation=1)
                    with self.assertRaises(cloud.CloudQueueError):
                        cloud.envelope("lucasrosalem", action, payload)

    def test_token_only_from_host_environment(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(cloud.CloudQueueError, "UNCONFIGURED"):
                cloud.credential()
        self.assertEqual(cloud.credential({"KWAI_PERSISTENT_CLOUD_TOKEN": TOKEN}), TOKEN)

    def test_network_does_not_retry_ambiguous_result(self):
        with patch.object(cloud, "urlopen", side_effect=URLError("lost")) as net:
            with self.assertRaisesRegex(cloud.CloudQueueError, "UNKNOWN_STOP"):
                cloud.request_once("lucasrosalem", "lease", {}, token=TOKEN)
            self.assertEqual(net.call_count, 1)

    def test_cloud_client_sends_only_scoped_target(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_): return b'{"ok":true,"job":null}'
        with patch.object(cloud, "urlopen", return_value=FakeResponse()) as net:
            result = cloud.request_once("universoanthares", "lease", {}, token=TOKEN)
            self.assertIsNone(result["job"])
            request = net.call_args[0][0]
            self.assertEqual(json.loads(request.data)["target_key"],
                             "kwai:universoanthares")
            self.assertIn("Bearer " + TOKEN, request.headers["Authorization"])

    def test_lease_file_0600_and_no_overwrite(self):
        def reply(*_args, **_kwargs):
            return {"ok": True, "job": {
                "id": JOB_ID, "target_key": "kwai:lucasrosalem",
                "lease_generation": "3", "payload": json.dumps({
                    "expected_account": "lucasrosalem",
                    "video_url": "https://anthares.us/video.mp4"})}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lease.json"
            argv = ["client", "lease", "--account", "lucasrosalem",
                    "--lease-file", str(path)]
            with patch.object(sys, "argv", argv), patch.object(
                    cloud, "request_once", side_effect=reply), contextlib.redirect_stdout(
                    io.StringIO()) as output:
                self.assertEqual(cloud.main(), 0)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["lease_generation"], 3)
            self.assertNotIn("video_url", output.getvalue())
            with patch.object(sys, "argv", argv), patch.object(
                    cloud, "request_once", side_effect=reply):
                with self.assertRaises(FileExistsError):
                    cloud.main()


if __name__ == "__main__":
    unittest.main()
