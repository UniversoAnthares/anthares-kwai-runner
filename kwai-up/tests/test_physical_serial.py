"""Fail-closed ADB serial selection regression tests (no phone required)."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import kwai_up_physical as physical


def adb_devices(*rows):
    return "List of devices attached\n" + "".join(f"{serial}\t{state}\n" for serial, state in rows)


class SerialIdentityTests(unittest.TestCase):
    USB = "993fce720408"
    WIFI = "192.168.1.35:5555"

    def test_requested_usb_wins_over_wifi(self):
        raw = adb_devices((self.WIFI, "device"), (self.USB, "device"))
        self.assertEqual(physical.choose_serial(raw, self.USB), self.USB)

    def test_missing_usb_must_not_switch_to_wifi(self):
        raw = adb_devices((self.WIFI, "device"))
        with self.assertRaisesRegex(physical.ku.KwaiUpError, "adb-serial-stale"):
            physical.choose_serial(raw, self.USB)

    def test_offline_usb_must_not_switch_to_wifi(self):
        raw = adb_devices((self.USB, "offline"), (self.WIFI, "device"))
        with self.assertRaisesRegex(physical.ku.KwaiUpError, "adb-serial-stale"):
            physical.choose_serial(raw, self.USB)

    def test_unauthorized_usb_must_not_switch_to_wifi(self):
        raw = adb_devices((self.USB, "unauthorized"), (self.WIFI, "device"))
        with self.assertRaisesRegex(physical.ku.KwaiUpError, "adb-serial-stale"):
            physical.choose_serial(raw, self.USB)

    def test_missing_wifi_must_not_switch_to_usb(self):
        raw = adb_devices((self.USB, "device"))
        with self.assertRaisesRegex(physical.ku.KwaiUpError, "adb-serial-stale"):
            physical.choose_serial(raw, self.WIFI)

    def test_no_requested_unique_usb_allowed(self):
        self.assertEqual(physical.choose_serial(adb_devices((self.USB, "device"))), self.USB)

    def test_no_requested_unique_wifi_allowed(self):
        self.assertEqual(physical.choose_serial(adb_devices((self.WIFI, "device"))), self.WIFI)

    def test_no_requested_multiple_usb_fails(self):
        raw = adb_devices((self.USB, "device"), ("otherusb", "device"))
        with self.assertRaises(physical.ku.KwaiUpError):
            physical.choose_serial(raw)

    def test_requested_serial_not_accepted_if_absent(self):
        for state in ("offline", "unauthorized", "recovery", "no permissions"):
            with self.subTest(state=state):
                with self.assertRaises(physical.ku.KwaiUpError):
                    physical.choose_serial(adb_devices((self.USB, state)), self.USB)

    def test_recovery_preserves_identity_or_fails(self):
        adb = physical.PhysicalADB.__new__(physical.PhysicalADB)
        adb.executable = "adb"
        adb.serial = self.USB
        completed = types.SimpleNamespace(returncode=0, stdout=adb_devices((self.WIFI, "device")))
        with patch.object(physical.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(physical.ku.KwaiUpError, "adb-serial-stale"):
                adb._recover_transport()
        self.assertEqual(adb.serial, self.USB)


if __name__ == "__main__":
    unittest.main()
