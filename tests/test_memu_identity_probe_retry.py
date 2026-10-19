"""MEmu identity proof stays fail-closed but tolerates one transient UI failure."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kwai_device_failover_worker as worker


class IdentityProbeRetryTests(unittest.TestCase):
    def test_transient_failure_is_followed_by_verified_identity(self):
        failure = SimpleNamespace(returncode=70, stdout="KWAI_UP_STATE=FAILED_SAFE")
        verified = SimpleNamespace(returncode=0, stdout="KWAI_UP_STATE=AUTHENTICATED_IDENTITY ACCOUNT=lucasrosalem")
        with patch.dict(os.environ, {"KWAI_EXPECTED_ACCOUNT": "lucasrosalem"}, clear=False):
            with patch.object(worker, "ensure_memu_transport", return_value=True), patch.object(worker.subprocess, "run", side_effect=[failure, verified]) as p, patch.object(worker.time, "sleep"):
                result = worker.verify_memu_standby_identity()
                self.assertTrue(result)
                self.assertEqual(p.call_count, 2)

    def test_missing_exact_identity_fails_closed(self):
        wrong = SimpleNamespace(returncode=0, stdout="KWAI_UP_STATE=AUTHENTICATED_IDENTITY ACCOUNT=other_account")
        with patch.dict(os.environ, {"KWAI_EXPECTED_ACCOUNT": "lucasrosalem"}, clear=False):
            with patch.object(worker, "ensure_memu_transport", return_value=True), patch.object(worker.subprocess, "run", return_value=wrong) as p, patch.object(worker.time, "sleep"):
                self.assertFalse(worker.verify_memu_standby_identity())
                self.assertEqual(p.call_count, 2)

    def test_offline_transport_never_attempts_authentication(self):
        with patch.object(worker, "ensure_memu_transport", return_value=False), patch.object(worker.subprocess, "run") as p:
            self.assertFalse(worker.verify_memu_standby_identity())
            p.assert_not_called()


if __name__ == "__main__":
    unittest.main()
