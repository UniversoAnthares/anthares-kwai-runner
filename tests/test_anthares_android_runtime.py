import unittest

from anthares_android_runtime.runtime import BackendState, health_score, parse_adb_devices


class RuntimeUnitTests(unittest.TestCase):
    def test_parse_devices(self):
        text = "List of devices attached\n127.0.0.1:21543        offline transport_id:2\nemulator-5554 device product:sdk model:x\n"
        self.assertEqual(parse_adb_devices(text)["127.0.0.1:21543"], "offline")
        self.assertEqual(parse_adb_devices(text)["emulator-5554"], "device")

    def test_health_score(self):
        self.assertEqual(health_score(True, "offline", False), 20)
        self.assertEqual(health_score(True, "device", True, True, True, True), 100)

    def test_state_value(self):
        self.assertEqual(BackendState.RUNNING_TRANSPORT_OFFLINE.value, "RUNNING_TRANSPORT_OFFLINE")


if __name__ == "__main__":
    unittest.main()
