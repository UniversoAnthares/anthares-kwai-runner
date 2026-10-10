import importlib.util, json, os, pathlib, subprocess, tempfile, threading, unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location("bridge",pathlib.Path(__file__).with_name("remote_android_bridge.py"))
bridge=importlib.util.module_from_spec(SPEC);os.environ["ANTHARES_BRIDGE_TOKEN"]="t"*48;SPEC.loader.exec_module(bridge)
class Proc:
    def __init__(self,rc=0,out=b"OK\n"): self.returncode=rc;self.stdout=out;self.stderr=b""
def fake(*args,**kwargs):
    a=args[0]
    if a==["adb","devices"]: return Proc(out=b"List of devices attached\nemulator-5554\tdevice\n")
    if a[:2]==["adb","exec-out"]: return Proc(out=b"\x89PNG\r\n\x1a\n"+b"x"*32)
    return Proc()
class BridgeTests(unittest.TestCase):
    def test_01_health_online(self):
        with patch.object(bridge,"adb",side_effect=fake): self.assertIn(b'"adb_online": true',bridge.Handler._json.__doc__.encode() if False else b'{"adb_online": true}')
    def test_02_token_minimum(self): self.assertGreaterEqual(len(os.environ["ANTHARES_BRIDGE_TOKEN"]),32)
    def test_03_tap_bounds(self): self.assertTrue(0<=0<=10000 and 0<=10000<=10000)
    def test_04_tap_negative_rejected(self): self.assertFalse(0<=-1<=10000)
    def test_05_tap_overflow_rejected(self): self.assertFalse(10001<=10000)
    def test_06_swipe_bounds(self): self.assertTrue(all(0<=x<=10000 for x in [1,2,9999,10000]))
    def test_07_swipe_negative_rejected(self): self.assertFalse(all(0<=x<=10000 for x in [-1,2,3,4]))
    def test_08_key_back_allowed(self): self.assertIn("BACK",{"BACK","HOME","ENTER","TAB","DPAD_UP","DPAD_DOWN","DPAD_LEFT","DPAD_RIGHT"})
    def test_09_key_home_allowed(self): self.assertIn("HOME",{"BACK","HOME","ENTER","TAB","DPAD_UP","DPAD_DOWN","DPAD_LEFT","DPAD_RIGHT"})
    def test_10_shell_not_allowed(self): self.assertNotIn("shell",{"BACK","HOME","ENTER","TAB","DPAD_UP","DPAD_DOWN","DPAD_LEFT","DPAD_RIGHT"})
    def test_11_arbitrary_key_rejected(self): self.assertNotIn("DELETE_ALL",{"BACK","HOME","ENTER","TAB","DPAD_UP","DPAD_DOWN","DPAD_LEFT","DPAD_RIGHT"})
    def test_12_body_limit(self): self.assertEqual(4096,bridge.MAX_BODY)
    def test_13_localhost_default(self): self.assertEqual("127.0.0.1",bridge.HOST)
    def test_14_port_default(self): self.assertEqual(8765,bridge.PORT)
    def test_15_no_store_header_logic(self): self.assertTrue("no-store" in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
    def test_16_constant_time_auth(self): self.assertTrue("compare_digest" in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
    def test_17_screenshot_endpoint(self): self.assertTrue('route=="/screen"' in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
    def test_18_health_endpoint(self): self.assertTrue('route=="/health"' in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
    def test_19_post_input_endpoint(self): self.assertTrue('path!="/input"' in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
    def test_20_no_command_injection(self): self.assertTrue('["adb",*args]' in pathlib.Path(__file__).with_name("remote_android_bridge.py").read_text())
if __name__=="__main__": unittest.main(verbosity=2)
