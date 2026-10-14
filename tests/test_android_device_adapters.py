import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from android_device_adapters import PhysicalDeviceAdapter, MEmuAdapter, AndroidExecutorRouter


class Result:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


def good_run(cmd, **kwargs):
    if cmd[-1] == "get-state":
        return Result(0, "device\n")
    if "pm" in cmd and "path" in cmd:
        return Result(0, "package:/data/app/com.kwai.video/base.apk\n")
    return Result(0, "")


class AndroidDeviceAdapterTests(unittest.TestCase):
    def test_physical_fails_closed_without_serial(self):
        s = PhysicalDeviceAdapter("", run=good_run).probe()
        self.assertFalse(s.ready)
        self.assertEqual(s.last_failure_class, "offline")

    def test_memu_fails_closed_without_serial(self):
        s = MEmuAdapter("", run=good_run).probe()
        self.assertFalse(s.ready)
        self.assertEqual(s.executor_id, "memu_android")

    def test_physical_ready_requires_explicit_session_proof(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHARES_PHYSICAL_KWAI_AUTHENTICATED", None)
            s = PhysicalDeviceAdapter("SERIAL", run=good_run).probe()
        self.assertTrue(s.online)
        self.assertFalse(s.ready)
        self.assertFalse(s.authenticated)

    def test_physical_ready_after_session_proof(self):
        with patch.dict(os.environ, {"ANTHARES_PHYSICAL_KWAI_AUTHENTICATED": "1"}):
            s = PhysicalDeviceAdapter("SERIAL", run=good_run).probe()
        self.assertTrue(s.ready)
        self.assertTrue(s.authenticated)

    def test_memu_ready_after_session_proof(self):
        with patch.dict(os.environ, {"ANTHARES_MEMU_KWAI_AUTHENTICATED": "true"}):
            s = MEmuAdapter("127.0.0.1:21503", run=good_run).probe()
        self.assertTrue(s.ready)
        self.assertEqual(s.adb_serial, "127.0.0.1:21503")

    def test_router_reports_both_devices(self):
        with patch.dict(os.environ, {
            "ANTHARES_PHYSICAL_KWAI_AUTHENTICATED": "1",
            "ANTHARES_MEMU_KWAI_AUTHENTICATED": "1",
        }):
            r = AndroidExecutorRouter(
                PhysicalDeviceAdapter("PHONE", run=good_run),
                MEmuAdapter("MEMU", run=good_run),
            ).status()
        self.assertIn("physical_android", r)
        self.assertIn("memu_android", r)
        self.assertTrue(r["physical_android"]["ready"])
        self.assertTrue(r["memu_android"]["ready"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
