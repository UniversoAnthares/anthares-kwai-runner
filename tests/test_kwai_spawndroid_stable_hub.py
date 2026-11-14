import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"tools"/"kwai_spawndroid_stable_hub.py"
spec=importlib.util.spec_from_file_location("kwai_spawndroid_stable_hub",PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Resp:
    def __init__(self,data):
        self.body=json.dumps(data).encode()
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self,length=65536):
        return self.body[:length]


class FakeHub:
    def __init__(self,package="com.kwai.video",activate_ok=True,app_state=4,teardown_visible=True):
        self.calls=[]
        self.package=package
        self.activate_ok=activate_ok
        self.teardown=True
        self.app_state=app_state
        self.teardown_visible=teardown_visible
        self.closed=False
    def __call__(self,req,timeout=None):
        method=req.get_method()
        path=req.full_url.removeprefix(mod.HUB)
        self.calls.append((method,path,req))
        if path=="/session" and method=="POST":
            data=json.loads(req.data)
            assert data["capabilities"]["alwaysMatch"]["spawndroid:app"]=="official-kwai"
            return Resp({"value":{"sessionId":"abc12345678","capabilities":{
                "spawndroid:appPackage":self.package,
                "appium:udid":"cloud-android-1",
                "platformVersion":"14",
                "spawndroid:sessionId":"sess_mock123"}}})
        if path.endswith("/execute/sync") and method=="POST":
            if not self.activate_ok:
                raise urllib.error.HTTPError(req.full_url,502,"backend failed",{},
                                             io.BytesIO(b'{"secret":"DO_NOT_LOG"}'))
            self.assert_command=json.loads(req.data)
            if self.assert_command["script"]=="mobile: queryAppState":
                return Resp({"value":self.app_state})
            return Resp({"value":None})
        if path=="/session/abc12345678/source" and method=="GET":
            return Resp({"value":"<hierarchy><node class='android.view.View'/></hierarchy>"})
        if path.startswith("/session/abc12345678?result=") and method=="DELETE":
            self.closed=True
            return Resp({"value":None})
        if path=="/session/abc12345678" and method=="GET":
            if self.closed and self.teardown_visible:
                raise urllib.error.HTTPError(req.full_url,404,"gone",{},io.BytesIO(b"{}"))
            return Resp({"value":{"sessionId":"abc12345678"}})
        raise AssertionError("unexpected request "+method+" "+path)


class TestHub(unittest.TestCase):
    def setUp(self):
        self.transport=FakeHub()
        self.hub=mod.SpawnDroidHub("fake-only",transport=self.transport)

    def test_hub_key_required(self):
        with self.assertRaisesRegex(mod.HubError,"hub_token_missing"):
            mod.SpawnDroidHub("")

    def test_manual_gates(self):
        for enable,free in ((False,False),(True,False),(False,True)):
            with self.assertRaisesRegex(mod.HubError,"launch_guard_disabled"):
                self.hub.verify_kwai_once("official-kwai",enable=enable,free_hobby=free)
        self.assertFalse(self.transport.calls)

    def test_bad_slug_no_allocation(self):
        for slug in ("","../private","http://domain","a b","/"):
            with self.assertRaises(mod.HubError):
                self.hub.verify_kwai_once(slug,enable=True,free_hobby=True)
        self.assertFalse(self.transport.calls)

    def test_activation_and_teardown(self):
        proof=self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertTrue(proof["kwai_app_activated"])
        self.assertFalse(proof["publication_attempted"])
        self.assertTrue(proof["webdriver_session_terminated"])
        self.assertFalse(proof["provider_device_termination_verified"])
        self.assertEqual(proof["android_version"],"14")
        self.assertEqual(proof["android_device_id"],"cloud-android-1")
        self.assertEqual([x[0] for x in self.transport.calls],
                         ["POST","POST","POST","GET","DELETE","GET"])
        self.assertEqual(self.transport.assert_command["script"],"mobile: queryAppState")
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=passed")

    def test_wrong_package_never_launches_app(self):
        self.transport.package="com.other"
        with self.assertRaisesRegex(mod.HubError,"installed_package_mismatch"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertEqual([x[0] for x in self.transport.calls],["POST","DELETE","GET"])
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=failed")

    def test_app_failure_is_reported_and_teardown(self):
        self.transport.activate_ok=False
        with self.assertRaisesRegex(mod.HubError,"host_unavailable"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertEqual([x[0] for x in self.transport.calls],["POST","POST","DELETE","GET"])
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=failed")

    def test_app_not_in_foreground_is_failure_and_stops(self):
        self.transport.app_state=3
        with self.assertRaisesRegex(mod.HubError,"kwai_not_in_foreground"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertTrue(self.transport.closed)
        self.assertTrue(self.transport.calls[-2][1].endswith("?result=failed"))

    def test_delete_ack_without_invalid_session_is_not_terminal(self):
        self.transport.teardown_visible=False
        with self.assertRaisesRegex(mod.HubError,"hub_teardown_unverified"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertTrue(self.transport.closed)
        self.assertEqual(self.transport.calls[-1][0],"GET")

    def test_token_not_logged_in_http_error(self):
        def denied(req,timeout=None):
            raise urllib.error.HTTPError(req.full_url,401,"unauthorized",{},
                                         io.BytesIO(b'{"bearer":"SHOULD_NOT_LEAK"}'))
        c=mod.SpawnDroidHub("TOKEN_SECRET",transport=denied)
        with self.assertRaises(mod.HubError) as ctx:
            c.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertEqual(str(ctx.exception),"hub_auth_failed")
        self.assertNotIn("TOKEN_SECRET",str(ctx.exception))

    def test_no_publication_or_lease_calls(self):
        text=PATH.read_text()
        self.assertNotIn("kwai-lease",text)
        self.assertNotIn("kwai-start",text)
        self.assertNotIn("kwai-confirm",text)
        self.assertNotIn("mobile: click",text)


if __name__=="__main__":
    unittest.main()
