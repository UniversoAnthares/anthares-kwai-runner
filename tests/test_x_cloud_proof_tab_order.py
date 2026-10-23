"""Contract tests for X-only pre/post submission timeline readback order.

No browser, account, tokens, network, or submission is exercised.
"""
import ast
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


SOURCE = Path(__file__).resolve().parents[1] / "tools/x_github_anthares_browser_publisher.py"


class FakeLocator:
    def __init__(self, values=None):
        self.values = values or []

    def all(self):
        return self.values

    def all_text_contents(self):
        return self.values

    def count(self):
        return len(self.values)


class FakeLink:
    def __init__(self, href):
        self.href = href

    def get_attribute(self, key):
        assert key == "href"
        return self.href


class FakePost:
    def __init__(self, text="caption", href="/lucasyahn/status/123456789"):
        self.text = text
        self.href = href

    def inner_text(self, timeout=None):
        return self.text

    def locator(self, selector):
        assert selector == "a"
        return FakeLocator([FakeLink(self.href)])


class FakePage:
    def __init__(self, context, events, redirected=False, found=False):
        self.context = context
        self.events = events
        self.redirected = redirected
        self.found = found
        self.url = "https://x.com/home"

    def goto(self, target, **_):
        self.events.append("goto")
        self.url = ("https://x.com/otheraccount" if self.redirected and target.endswith("/lucasyahn")
                    else target)

    def wait_for_timeout(self, _):
        pass

    def locator(self, selector):
        if selector == "article":
            return FakeLocator([FakePost()] if self.found else [])
        if selector == '[data-testid="tweetText"]':
            return FakeLocator(["caption"])
        if selector == "video":
            return FakeLocator([object()])
        raise AssertionError("unexpected locator " + selector)

    def close(self):
        self.events.append("close")


class FakeContext:
    def __init__(self, redirected=False, found=False):
        self.events = []
        self.redirected = redirected
        self.found = found

    def new_page(self):
        self.events.append("new_page")
        return FakePage(self, self.events, self.redirected, self.found)


def load_proof(identity_ok=True):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == "proof")
    def account(page):
        page.events.append("account")
        if not identity_ok:
            raise RuntimeError("X_CLOUD_WRONG_ACCOUNT")
    namespace = {"account": account, "re": re, "urlparse": urlparse,
                 "RuntimeError": RuntimeError}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<x-proof>", "exec"),
         namespace)
    return namespace["proof"]


class TestXCloudProof(unittest.TestCase):
    def test_missing_verified_session_does_not_open_tab(self):
        context = FakeContext()
        with self.assertRaisesRegex(RuntimeError, "INDEPENDENT_IDENTITY_REQUIRED"):
            load_proof()(context, "caption", verified_page=None)
        self.assertEqual(context.events, [])

    def test_wrong_account_fails_before_opening_timeline(self):
        context = FakeContext()
        posting = FakePage(context, context.events)
        with self.assertRaisesRegex(RuntimeError, "WRONG_ACCOUNT"):
            load_proof(False)(context, "caption", verified_page=posting)
        self.assertEqual(context.events, ["account"])

    def test_empty_timeline_closes_tab(self):
        context = FakeContext()
        posting = FakePage(context, context.events)
        self.assertIsNone(load_proof()(context, "caption", verified_page=posting))
        self.assertEqual(context.events, ["account", "new_page", "goto", "close"])

    def test_exact_owner_caption_video_and_uri_succeed(self):
        context = FakeContext(found=True)
        posting = FakePage(context, context.events)
        url = load_proof()(context, "caption", verified_page=posting)
        self.assertEqual(url, "https://x.com/lucasyahn/status/123456789")
        self.assertEqual(context.events[0:2], ["account", "new_page"])
        self.assertEqual(context.events[-1], "close")

    def test_redirected_profile_rejected_without_bypassing_identity(self):
        context = FakeContext(redirected=True)
        posting = FakePage(context, context.events)
        with self.assertRaisesRegex(RuntimeError, "TIMELINE_PROFILE_MISMATCH"):
            load_proof()(context, "caption", verified_page=posting)
        self.assertEqual(context.events, ["account", "new_page", "goto", "close"])

    def test_identity_proven_per_attempt(self):
        context = FakeContext()
        posting = FakePage(context, context.events)
        self.assertIsNone(load_proof()(context, "caption", attempts=2,
                                     verified_page=posting))
        self.assertEqual(context.events, ["account", "new_page", "goto", "close",
                                          "account", "new_page", "goto", "close"])


if __name__ == "__main__":
    unittest.main()
