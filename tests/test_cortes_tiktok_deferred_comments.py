"""Contracts for the five-window deferred TikTok comment scheduler."""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cortes_tiktok_deferred_comments as d


class MockContext:
    def __init__(self):
        self.closed = False
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def close(self):
        self.closed = True
    def new_page(self):
        return object()


class MockBrowser:
    def __init__(self):
        self.context = MockContext()
        self.closed = False
    def new_context(self, **kwargs):
        return self.context
    def close(self):
        self.closed = True


class MockRuntime:
    def __init__(self):
        self.browser = MockBrowser()
        self.chromium = self
    def launch(self, **kwargs):
        return self.browser
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None


class DeferredTests(unittest.TestCase):
    def test_rejects_cross_account_pending(self):
        with self.assertRaisesRegex(RuntimeError, "PENDING_UNVERIFIED"):
            d.pending_ids({"ok":True,"account":"other","pending":[]}, "lucasrosalem4")

    def test_rejects_duplicate_and_invalid_video_identifiers(self):
        duplicate={"ok":True,"account":"lucasrosalem4",
                   "pending":[{"source_video_id":"7711053609256963349"}]*2}
        with self.assertRaisesRegex(RuntimeError,"SOURCE_ID_INVALID"):
            d.pending_ids(duplicate,"lucasrosalem4")
        with self.assertRaisesRegex(RuntimeError,"SOURCE_ID_INVALID"):
            d.pending_ids({"ok":True,"account":"lucasrosalem4",
                           "pending":[{"source_video_id":"777;DROP"}]},"lucasrosalem4")

    def test_max_five_items_per_run(self):
        ids=[{"source_video_id":str(7711053609256963349+i)} for i in range(6)]
        with self.assertRaisesRegex(RuntimeError,"PENDING_INVALID"):
            d.pending_ids({"ok":True,"account":"lucasrosalem4","pending":ids},"lucasrosalem4")

    def test_empty_pending_avoids_browser_and_state_mutation(self):
        calls=[]
        def request(action,payload=None):
            calls.append(action)
            return {"ok":True,"account":"universo.anthares","pending":[]}
        r=d.run_account("universo.anthares",{"cookies":[]},request,
                        action=lambda **kw: self.fail("no posting"))
        self.assertEqual(r["state"],"idle")
        self.assertEqual(calls,["comment-pending"])

    def test_captcha_hold_uses_neon_read_only_and_never_launches_browser(self):
        calls = []
        def request(action, payload=None):
            calls.append((action, payload))
            return {"ok": True, "account": "universo.anthares",
                    "pending": [{"source_video_id": "7711107796988693781"}]}
        result = d.run_account("universo.anthares", {"cookies": [{}]},
                               request, allow_browser=False,
                               action=lambda **kw: self.fail("CAPTCHA hold must not interact"))
        self.assertEqual(result, {"account": "universo.anthares",
                                  "attempted": 0, "state": "manual_hold"})
        self.assertEqual(calls, [("comment-pending", None)])

    def test_challenge_stops_and_leaves_later_pending_clips(self):
        sources=["7711053609256963349","7711050254891633928"]
        runtime=MockRuntime()
        call_order=[]
        def request(action,payload=None):
            if action=="comment-pending":
                return {"ok":True,"account":"lucasrosalem4",
                        "pending":[{"source_video_id":x} for x in sources]}
            call_order.append(action)
            return {"ok":True}
        def action(**kwargs):
            call_order.append(kwargs["source_video_id"])
            return "security_challenge"
        with patch.dict(sys.modules,{"playwright":types.ModuleType("playwright"),
                                     "playwright.sync_api":types.SimpleNamespace(sync_playwright=lambda: runtime)}):
            result=d.run_account("lucasrosalem4",{"cookies":[{}]},request,
                                 play_runtime=runtime,action=action)
        self.assertEqual(result["state"],"security_challenge")
        self.assertEqual(result["attempted"],1)
        self.assertEqual(call_order,[sources[0]])
        self.assertTrue(runtime.browser.closed)
        self.assertTrue(runtime.browser.context.closed)

    def test_eligible_receipts_are_processed_once_per_pending_source(self):
        sources=["7711053609256963349","7711050254891633928"]
        runtime=MockRuntime()
        attempts=[]
        def request(action,payload=None):
            if action=="comment-pending":
                return {"ok":True,"account":"lucasrosalem4",
                        "pending":[{"source_video_id":x} for x in sources]}
            return {"ok":True}
        def action(**kwargs):
            attempts.append(kwargs["source_video_id"])
            return "posted"
        with patch.dict(sys.modules,{"playwright":types.ModuleType("playwright"),
                                     "playwright.sync_api":types.SimpleNamespace(sync_playwright=lambda: runtime)}):
            result=d.run_account("lucasrosalem4",{"cookies":[{}]},request,
                                 play_runtime=runtime,action=action)
        self.assertEqual(attempts,sources)
        self.assertEqual(result["state"],"complete")
        self.assertEqual(result["attempted"],2)


class SessionLoadingTests(unittest.TestCase):
    def modules(self, state_load):
        primary = types.ModuleType("cortes_tiktok_queue_consumer")
        primary.qcall = lambda *args: self.fail("legacy queue must not be used")
        primary.oidc = lambda: {"Authorization": "Bearer " + "x"*210}
        secondary = types.ModuleType("cortes_tiktok_lucasrosalem4_cloud_publish")
        secondary.state_from_secret = lambda: state_load("lucasrosalem4")
        secondary.call = lambda *args: self.fail("legacy queue must not be used")
        secondary.oidc = lambda: "x"*210
        vault = types.ModuleType("tiktok_session_authority")
        vault.load_canonical_state = lambda: (state_load("universo.anthares"), "test")
        return {
            "cortes_tiktok_queue_consumer": primary,
            "cortes_tiktok_lucasrosalem4_cloud_publish": secondary,
            "tiktok_session_authority": vault,
        }

    def test_scheduled_hold_reads_neon_without_loading_tiktok_state(self):
        attempted = []
        def forbidden_load(account):
            self.fail("HOLD cannot load TikTok browser state: " + account)
        def read_pending(account, token, action, payload=None):
            self.assertEqual(action, "comment-pending")
            self.assertIsNone(payload)
            attempted.append(account)
            return {"ok": True, "account": account,
                    "pending": [{"source_video_id": "7711053609256963349"}]}
        with patch.dict(sys.modules, self.modules(forbidden_load)), \
             patch.object(d, "recovery_request", side_effect=read_pending):
            for account in d.ACCOUNTS:
                with self.subTest(account=account), patch.dict(
                    "os.environ",
                    {"TIKTOK_DEFERRED_ACCOUNT": account,
                     "TIKTOK_COMMENT_RECOVERY_ENABLED": "true",
                     "TIKTOK_COMMENT_BROWSER_CLEARED": "false"}, clear=True
                ):
                    self.assertEqual(d.main(), 0)
        self.assertEqual(attempted, list(d.ACCOUNTS))

    def test_manual_clearance_still_requires_authenticated_state(self):
        loaded = []
        def state_load(account):
            loaded.append(account)
            return {"cookies": [{"name": "dummy", "value": "test"}]}
        def run_assert(account, state, request, *, allow_browser):
            self.assertTrue(allow_browser)
            self.assertEqual(state, {"cookies": [{"name": "dummy", "value": "test"}]})
            return {"account": account, "attempted": 0, "state": "idle"}
        with patch.dict(sys.modules, self.modules(state_load)), \
             patch.object(d, "run_account", side_effect=run_assert):
            for account in d.ACCOUNTS:
                with self.subTest(account=account), patch.dict(
                    "os.environ",
                    {"TIKTOK_DEFERRED_ACCOUNT": account,
                     "TIKTOK_COMMENT_RECOVERY_ENABLED": "true",
                     "TIKTOK_COMMENT_BROWSER_CLEARED": "true"}, clear=True
                ):
                    self.assertEqual(d.main(), 0)
        self.assertEqual(loaded, list(d.ACCOUNTS))


class RecoveryTransportTests(unittest.TestCase):
    def test_disallows_upload_actions_and_cross_account(self):
        with self.assertRaisesRegex(RuntimeError, "ROUTE_REJECTED"):
            d.recovery_request("other-account", "x"*210, "comment-pending")
        with self.assertRaisesRegex(RuntimeError, "ROUTE_REJECTED"):
            d.recovery_request("universo.anthares", "x"*210, "publish")
        with self.assertRaisesRegex(RuntimeError, "AUTH_MISSING"):
            d.recovery_request("universo.anthares", "", "comment-pending")

    def test_recovery_pending_uses_exact_signed_origin(self):
        import json
        sent=[]
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):return json.dumps({
                "ok":True,"account":"lucasrosalem4","pending":[]}).encode()
        def call(req,timeout):
            sent.append(req)
            self.assertEqual(timeout,25)
            return Response()
        with patch("urllib.request.urlopen",side_effect=call):
            r=d.recovery_request("lucasrosalem4","x"*210,"comment-pending")
        self.assertEqual(r["pending"],[])
        self.assertEqual(sent[0].get_method(),"GET")
        self.assertEqual(sent[0].full_url,
            d.COMMENT_RECOVERY_ENDPOINTS["lucasrosalem4"]+"?action=comment-pending")

    def test_primary_signed_oidc_header_matches_secondary_raw_jwt(self):
        import json
        sent=[]
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):return json.dumps({
                "ok":True,"account":"universo.anthares","pending":[]}).encode()
        def fetch(req,timeout):
            sent.append(req)
            return Response()
        with patch("urllib.request.urlopen",side_effect=fetch):
            got=d.recovery_request("universo.anthares",
                                   {"Authorization":"Bearer "+"x"*210},
                                   "comment-pending")
        self.assertEqual(got["account"],"universo.anthares")
        self.assertEqual(sent[0].get_header("Authorization"),
                         "Bearer "+"x"*210)

    def test_fails_closed_if_backend_returns_another_account(self):
        import json
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):return json.dumps({
                "ok":True,"account":"universo.anthares","pending":[]}).encode()
        with patch("urllib.request.urlopen",return_value=Response()):
            with self.assertRaisesRegex(RuntimeError, "IDENTITY_MISMATCH"):
                d.recovery_request("lucasrosalem4","x"*210,"comment-pending")


if __name__=="__main__":
    unittest.main()
