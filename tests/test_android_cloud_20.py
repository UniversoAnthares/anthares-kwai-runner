"""Twenty distinct offline checks for Android Cloud orchestration."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from anthares_android_cloud import controller as c

class AndroidCloudTwentyChecks(unittest.TestCase):
    def test_01_version(self): self.assertEqual(__import__('anthares_android_cloud').__version__, '0.1.0')
    def test_02_root_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError): c.sdk_tool('adb')
    def test_03_adb_path(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'platform-tools/adb'; p.parent.mkdir(); p.touch()
            with patch.dict(os.environ, {'ANDROID_SDK_ROOT':d}): self.assertEqual(c.sdk_tool('adb'),str(p))
    def test_04_emulator_path(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'emulator/emulator'; p.parent.mkdir(); p.touch()
            with patch.dict(os.environ, {'ANDROID_SDK_ROOT':d}): self.assertEqual(c.sdk_tool('emulator'),str(p))
    def test_05_avdmanager_path(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cmdline-tools/latest/bin/avdmanager'; p.parent.mkdir(parents=True); p.touch()
            with patch.dict(os.environ, {'ANDROID_SDK_ROOT':d}): self.assertEqual(c.sdk_tool('avdmanager'),str(p))
    def test_06_missing_binary(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict(os.environ, {'ANDROID_SDK_ROOT':d}):
                with self.assertRaises(FileNotFoundError): c.sdk_tool('adb')
    def test_07_sdk_home_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'platform-tools/adb'; p.parent.mkdir(); p.touch()
            with patch.dict(os.environ, {'ANDROID_HOME':d},clear=True): self.assertEqual(c.sdk_tool('adb'),str(p))
    def test_08_sdk_root_priority(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'platform-tools/adb'; p.parent.mkdir(); p.touch()
            with patch.dict(os.environ, {'ANDROID_SDK_ROOT':d,'ANDROID_HOME':'/missing'}): self.assertEqual(c.sdk_tool('adb'),str(p))
    def test_09_run_stdout(self):
        self.assertEqual(c.run(['python3','-c','print("ok")']), 'ok')
    def test_10_run_error(self):
        import subprocess
        with self.assertRaises(subprocess.CalledProcessError): c.run(['python3','-c','raise SystemExit(2)'])
    def test_11_run_timeout(self):
        import subprocess
        with self.assertRaises(subprocess.TimeoutExpired): c.run(['python3','-c','import time;time.sleep(2)'],timeout=1)
    def _status(self, devices, boot=None):
        answers=[devices]+([] if boot is None else [boot])
        with patch.object(c,'sdk_tool',return_value='/sdk/adb'),patch.object(c,'run',side_effect=answers):
            return c.status()
    def test_12_empty_devices(self): self.assertFalse(self._status('List of devices attached\n')['connected'])
    def test_13_offline_device(self): self.assertFalse(self._status('List of devices attached\nemulator-5554\toffline')['connected'])
    def test_14_unauthorized_device(self): self.assertFalse(self._status('List of devices attached\nemulator-5554\tunauthorized')['connected'])
    def test_15_booted(self): self.assertTrue(self._status('List of devices attached\nemulator-5554\tdevice','1')['booted'])
    def test_16_not_booted(self): self.assertFalse(self._status('List of devices attached\nemulator-5554\tdevice','0')['booted'])
    def test_17_serial(self): self.assertEqual(self._status('List of devices attached\nemulator-5554\tdevice','1')['serial'],'emulator-5554')
    def test_18_boot_crlf(self): self.assertTrue(self._status('List of devices attached\nemulator-5554\tdevice','1\r')['booted'])
    def test_19_wait_success(self):
        with patch.object(c,'status',side_effect=[{'booted':False},{'booted':True,'connected':True}]),patch.object(c.time,'sleep'): self.assertTrue(c.wait_boot(10)['booted'])
    def test_20_wait_timeout(self):
        with patch.object(c,'status',return_value={'booted':False}),patch.object(c.time,'monotonic',side_effect=[0,1]):
            with self.assertRaises(TimeoutError): c.wait_boot(0)
if __name__=='__main__': unittest.main()
