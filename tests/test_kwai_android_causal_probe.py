import importlib.util
import pathlib
import unittest

P=pathlib.Path(__file__).resolve().parents[1]/"tools"/"kwai_android_causal_probe.py"
spec=importlib.util.spec_from_file_location("causal",P)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CausalProbeTests(unittest.TestCase):
    def test_detect_crash_without_exposing_message(self):
        raw="10-10 20:00:00.000 123 456 E ActivityManager: Process com.kwai.video has died private=SECRET\n"
        result=mod.classify(raw)
        self.assertEqual(result["signals"]["process_crash"],1)
        self.assertNotIn("SECRET",str(result))
    def test_ignores_unrelated_process(self):
        raw="10-10 20:00:00.000 123 456 E ActivityManager: Process unrelated.app has died\n"
        self.assertEqual(mod.classify(raw)["events_detected"],0)
    def test_no_raw_authentication_data(self):
        raw="10-10 20:00:00.000 123 456 E AndroidRuntime: FATAL EXCEPTION OTP=123456 password=PRIVATE\n"
        result=mod.classify(raw)
        self.assertNotIn("123456",str(result))
        self.assertNotIn("PRIVATE",str(result))
    def test_detect_anr(self):
        raw="10-10 20:00:00.000 123 456 E ActivityManager: ANR in com.kwai.video\n"
        self.assertEqual(mod.classify(raw)["signals"]["application_not_responding"],1)

if __name__=="__main__":
    unittest.main()
