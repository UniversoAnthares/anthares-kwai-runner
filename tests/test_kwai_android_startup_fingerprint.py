import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from kwai_android_startup_fingerprint import summarize

class StartupFingerprintTests(unittest.TestCase):
    def test_installed_running_split_app(self):
        r=summarize("package:/data/base.apk\npackage:/data/split.apk","1234","com.kwai.video","1","state: CONNECTED","versionCode=123 primaryCpuAbi=x86_64")
        self.assertTrue(r["package_present"])
        self.assertEqual(r["apk_split_count"],2)
        self.assertTrue(r["app_running"])
        self.assertTrue(r["network_connected"])
        self.assertEqual(r["cpu_abi"],"x86_64")
    def test_missing_app_and_network(self):
        r=summarize("","","","0","","")
        self.assertFalse(r["package_present"])
        self.assertFalse(r["app_running"])
        self.assertFalse(r["network_connected"])
    def test_no_sensitive_strings_in_output(self):
        r=summarize("package:/private/secret.apk","123","secret user@example.com","1","connected","versionCode=5")
        output=str(r)
        self.assertNotIn("user@example.com",output)
        self.assertNotIn("/private/",output)
if __name__=="__main__":unittest.main()
