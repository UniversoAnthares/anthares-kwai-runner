"""Offline controller tests: no emulator or network required."""
import unittest
from unittest.mock import patch
from anthares_android_cloud import controller


class ControllerTests(unittest.TestCase):
    @patch.object(controller, "sdk_tool", return_value="/sdk/adb")
    @patch.object(controller, "run", side_effect=["List of devices attached\n", ""])
    def test_no_device(self, _run, _sdk):
        self.assertEqual(controller.status(), {"connected": False, "booted": False})

    @patch.object(controller, "sdk_tool", return_value="/sdk/adb")
    @patch.object(controller, "run", side_effect=["List of devices attached\nemulator-5554\tdevice", "1"])
    def test_booted(self, _run, _sdk):
        self.assertTrue(controller.status()["booted"])

    @patch.object(controller, "sdk_tool", return_value="/sdk/adb")
    @patch.object(controller, "run", side_effect=["List of devices attached\nemulator-5554\tdevice", "0"])
    def test_not_booted(self, _run, _sdk):
        self.assertFalse(controller.status()["booted"])


if __name__ == "__main__":
    unittest.main()
