"""Failover only for transport and backend failures; never for rate limits."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from tools import cortes_queue_ha as ha

class Resp:
    def __init__(self,data):self.raw=json.dumps(data)
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return self.raw.encode("utf-8")

def jwt():return "a"*90

class HaTests(unittest.TestCase):
    def setUp(self):
        healthy=patch.object(ha,'is_healthy',return_value=True)
        healthy.start()
        self.addCleanup(healthy.stop)

    def test_primary_success_never_switches(self):
        requested=[]
        def open_req(req,timeout):
            requested.append(req.full_url)
            return Resp({"ok":True,"status":"primary"})
        with patch.object(ha.urllib.request,"urlopen",side_effect=open_req):
            value=ha.post("buffer-pending",{},jwt)
        self.assertEqual(value["status"],"primary")
        self.assertEqual(len(requested),1)

    def test_neon_503_fails_over_to_secondary_for_safe_read(self):
        requested=[]
        def open_req(req,timeout):
            requested.append(req.full_url)
            if len(requested)==1:raise urllib.error.HTTPError(req.full_url,503,"unavailable",{},io.BytesIO())
            self.assertIn("vercel.app",req.full_url)
            self.assertTrue(req.get_header("Authorization").startswith("Bearer "))
            return Resp({"ok":True,"jobs":[]})
        with patch.object(ha.urllib.request,"urlopen",side_effect=open_req):
            result=ha.post("buffer-pending",{},jwt)
        self.assertEqual(result["jobs"],[])
        self.assertEqual(len(requested),2)

    def test_timeout_crosses_to_fallback(self):
        def open_req(req,timeout):
            if "cortesqueue.compute" in req.full_url:raise TimeoutError("unknown response")
            return Resp({"ok":True})
        with patch.object(ha.urllib.request,"urlopen",side_effect=open_req):
            self.assertTrue(ha.post("enqueue",{"id":"same"},jwt)["ok"])

    def test_403_409_429_do_not_switch(self):
        for status in (401,403,409,429):
            calls=[]
            def open_req(req,timeout):
                calls.append(req.full_url)
                raise urllib.error.HTTPError(req.full_url,status,"denied",{},io.BytesIO())
            with self.subTest(status=status):
                with patch.object(ha.urllib.request,"urlopen",side_effect=open_req):
                    with self.assertRaisesRegex(ha.BackendUnavailable,str(status)):
                        ha.post("buffer-pending",{},jwt)
                self.assertEqual(len(calls),1)

    def test_all_provider_failures_are_reported_not_claimed(self):
        with patch.object(ha.urllib.request,"urlopen",side_effect=TimeoutError("transport timeout")):
            with self.assertRaisesRegex(ha.BackendUnavailable,"ALL_PROVIDERS_UNAVAILABLE"):
                ha.post("enqueue",{"id":"same"},jwt)

    def test_fails_closed_on_forbidden_operation(self):
        with self.assertRaisesRegex(ValueError,"ACTION_NOT_ALLOWED"):
            ha.post("confirm",{},jwt)

    def test_no_tokens_in_error(self):
        secret="a"*90
        with patch.object(ha.urllib.request,"urlopen",side_effect=urllib.error.HTTPError("https://host",403,"bad",{},io.BytesIO())):
            with self.assertRaises(ha.BackendUnavailable) as cm:
                ha.post("buffer-pending",{},lambda:secret)
        self.assertNotIn(secret,str(cm.exception))
if __name__=="__main__":unittest.main()
