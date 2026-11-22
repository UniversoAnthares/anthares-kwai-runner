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


if __name__=="__main__":
    unittest.main()
