"""Offline contract tests for the SpawnDroid Hobby Android probe.

Never makes network calls or creates a cloud runner.
"""
import importlib.util
import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


PATH = Path(__file__).resolve().parents[1]/"tools"/"kwai_spawndroid_probe.py"
spec=importlib.util.spec_from_file_location("kwai_spawndroid_probe",PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Response:
    def __init__(self, value):
        self.payload=json.dumps(value).encode()
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def read(self, limit=None):
        return self.payload[:limit]


class FakeAPI:
    def __init__(self):
        self.calls=[]
        self.package="com.kwai.video"
        self.ready=True
        self.key_idempotent=False
    def __call__(self, req, timeout=None):
        path=req.full_url.removeprefix(module.API)
        self.calls.append((req.get_method(),path,req))
        if path=="/api/apps":
            return Response({"apps":[{"slug":"kwai-official-v1","packageName":self.package}]})
        if path=="/api/device-profiles":
            return Response({"profiles":[{"id":"android-14-phone"}]})
        if path=="/api/v1/sessions" and req.get_method()=="POST":
            self.key_idempotent=bool(req.headers.get("Idempotency-key"))
            return Response({"sessionId":"sess_abc123","state":"booting",
                             "webdriverUrl":"https://secret.example/tok_123/wd/hub"})
        if path=="/api/v1/sessions/sess_abc123" and req.get_method()=="GET":
            return Response({"sessionId":"sess_abc123",
                             "state":"ready" if self.ready else "failed",
                             "package":"com.kwai.video",
                             "device":{"serial":"device-1234"}})
        if path=="/api/v1/sessions/sess_abc123" and req.get_method()=="DELETE":
            return Response({"ok":True})
        raise AssertionError("unrecognized mocked request "+path)


class TestSpawnDroidAdapter(unittest.TestCase):
    def setUp(self):
        self.fake=FakeAPI()
        self.api=module.SpawnClient("dummy-local-test-only",transport=self.fake)

    def test_status_is_read_only(self):
        data=self.api.inventory()
        self.assertEqual(len(data["apps"]),1)
        self.assertEqual([call[0] for call in self.fake.calls],["GET","GET"])

    def test_missing_key_is_safe(self):
        with self.assertRaisesRegex(module.SpawnError,"api_key_missing"):
            module.SpawnClient("")

    def test_off_by_default_canary(self):
        with self.assertRaisesRegex(module.SpawnError,"manual_canary_gate_disabled"):
            self.api.canary("kwai-official-v1")
        self.assertEqual(self.fake.calls,[])

    def test_free_plan_confirmation_gate(self):
        with self.assertRaisesRegex(module.SpawnError,"manual_canary_gate_disabled"):
            self.api.canary("kwai-official-v1",run_enabled=True,hobby_free_confirmed=False)
        self.assertEqual(self.fake.calls,[])

    def test_reject_wrong_apk(self):
        self.fake.package="com.example.other"
        with self.assertRaisesRegex(module.SpawnError,"kwai_package_unverified"):
            self.api.canary("kwai-official-v1",run_enabled=True,hobby_free_confirmed=True)
        self.assertFalse(any(x[0]=="POST" for x in self.fake.calls))

    def test_probe_and_teardown(self):
        result=self.api.canary("kwai-official-v1",run_enabled=True,
                               hobby_free_confirmed=True,max_seconds=30)
        self.assertEqual(result["status"],"android_boot_verified")
        self.assertFalse(result["published"])
        self.assertFalse(result["account_tested"])
        self.assertTrue(self.fake.key_idempotent)
        self.assertEqual([x[0] for x in self.fake.calls],
                         ["GET","GET","POST","GET","DELETE"])

    def test_failed_boot_tears_down(self):
        self.fake.ready=False
        with self.assertRaisesRegex(module.SpawnError,"cloud_android_launch_failed"):
            self.api.canary("kwai-official-v1",run_enabled=True,hobby_free_confirmed=True)
        self.assertEqual(self.fake.calls[-1][0],"DELETE")

    def test_hobby_quota_402_redacted(self):
        def denied(req,timeout=None):
            raise urllib.error.HTTPError(req.full_url,402,
                "Payment Required",{},io.BytesIO(b'{"secret":"SECRET_SHOULD_NOT_LEAK"}'))
        other=module.SpawnClient("secret-key",transport=denied)
        with self.assertRaises(module.SpawnError) as caught:
            other.inventory()
        self.assertEqual(str(caught.exception),"free_quota_exhausted")
        self.assertNotIn("secret",str(caught.exception))

    def test_untrusted_artifact_identifier(self):
        for bad in ("../private", "https://other.site", "x/y", "", "kwai?x=1"):
            with self.subTest(bad=bad),self.assertRaises(module.SpawnError):
                self.api.find_kwai_artifact(bad,[])

    def test_cannot_extend_canary(self):
        with self.assertRaisesRegex(module.SpawnError,"canary_duration_invalid"):
            self.api.canary("kwai-official-v1",run_enabled=True,
                            hobby_free_confirmed=True,max_seconds=500)
        self.assertEqual(self.fake.calls,[])

    def test_no_publication_path_by_design(self):
        source=PATH.read_text(encoding="utf-8")
        self.assertNotIn("kwai-confirm",source)
        self.assertNotIn("kwai-start",source)
        self.assertNotIn("Neon",source.split("class SpawnClient:")[1])


if __name__=="__main__":
    unittest.main()
