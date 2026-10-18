import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from android_adb_inventory import online_devices


class AdbInventoryTests(unittest.TestCase):
    def test_real_windows_padded_listing(self):
        result = online_devices('List of devices attached\n993fce720408           device product:galahad_eea model:M2004J19C device:galahad transport_id:14\n')
        self.assertEqual(result[0]['serial'], '993fce720408')
        self.assertEqual(result[0]['model'], 'M2004J19C')

    def test_tab_and_tcp_serial(self):
        self.assertEqual(online_devices('127.0.0.1:21543\tdevice model:MEmu\n')[0]['serial'], '127.0.0.1:21543')

    def test_offline_unauthorized_and_header_are_not_eligible(self):
        self.assertEqual(online_devices('List of devices attached\na offline\nb unauthorized\n* daemon started successfully *\n'), [])
