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
    def __init__(self,package="com.kwai.video",activate_ok=True):
        self.calls=[]
        self.package=package
        self.activate_ok=activate_ok
        self.teardown=True
    def __call__(self,req,timeout=None):
        method=req.get_method()
        path=req.full_url.removeprefix(mod.HUB)
        self.calls.append((method,path,req))
        if path=="/session" and method=="POST":
            data=json.loads(req.data)
            assert data["capabilities"]["alwaysMatch"]["spawndroid:app"]=="official-kwai"
            return Resp({"value":{"sessionId":"abc12345678","capabilities":{
                "spawndroid:appPackage":self.package}}})
        if path.endswith("/execute/sync") and method=="POST":
            if not self.activate_ok:
                raise urllib.error.HTTPError(req.full_url,502,"backend failed",{},
                                             io.BytesIO(b'{"secret":"DO_NOT_LOG"}'))
            self.assert_command=json.loads(req.data)
            return Resp({"value":None})
        if path.startswith("/session/abc12345678?result=") and method=="DELETE":
            return Resp({"value":None})
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
        self.assertEqual([x[0] for x in self.transport.calls],["POST","POST","DELETE"])
        self.assertEqual(self.transport.assert_command["script"],"mobile: activateApp")
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=passed")

    def test_wrong_package_never_launches_app(self):
        self.transport.package="com.other"
        with self.assertRaisesRegex(mod.HubError,"installed_package_mismatch"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertEqual([x[0] for x in self.transport.calls],["POST","DELETE"])
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=failed")

    def test_app_failure_is_reported_and_teardown(self):
        self.transport.activate_ok=False
        with self.assertRaisesRegex(mod.HubError,"host_unavailable"):
            self.hub.verify_kwai_once("official-kwai",enable=True,free_hobby=True)
        self.assertEqual([x[0] for x in self.transport.calls],["POST","POST","DELETE"])
        self.assertEqual(self.transport.calls[-1][1].split("?")[-1],"result=failed")

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
