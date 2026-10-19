"""Fail-closed Kwai SYSTEM daemon MEmu identity preflight."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kwai_physical_queue_daemon as daemon


class MemuDaemonRetryTests(unittest.TestCase):
    def test_retry_exact_account_after_transient_error(self):
        bad=SimpleNamespace(returncode=70,stdout="KWAI_UP_STATE=FAILED_SAFE")
        good=SimpleNamespace(returncode=0,stdout="KWAI_UP_STATE=AUTHENTICATED_IDENTITY ACCOUNT=lucasrosalem")
        with patch.object(daemon,"ensure_memu_transport",return_value=True), \
             patch.object(daemon.subprocess,"run",side_effect=[bad,good]) as execute, \
             patch.object(daemon.time,"sleep"), patch.object(daemon,"log"):
            self.assertTrue(daemon.memu_identity_proven())
            self.assertEqual(execute.call_count,2)

    def test_wrong_account_is_never_promoted(self):
        bad=SimpleNamespace(returncode=0,stdout="KWAI_UP_STATE=AUTHENTICATED_IDENTITY ACCOUNT=other")
        with patch.object(daemon,"ensure_memu_transport",return_value=True), \
             patch.object(daemon.subprocess,"run",return_value=bad) as execute, \
             patch.object(daemon.time,"sleep"), patch.object(daemon,"log"):
            self.assertFalse(daemon.memu_identity_proven())
            self.assertEqual(execute.call_count,2)

    def test_offline_transport_short_circuits(self):
        with patch.object(daemon,"ensure_memu_transport",return_value=False), \
             patch.object(daemon.subprocess,"run") as execute:
            self.assertFalse(daemon.memu_identity_proven())
            execute.assert_not_called()


if __name__=="__main__":
    unittest.main()
