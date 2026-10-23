"""X account ownership and public video readback on one authenticated tab.

No credentials, X network, media upload, browser launch or ledger mutation.
"""
import ast
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


SOURCE = Path(__file__).resolve().parents[1] / "tools/x_github_anthares_browser_publisher.py"


class FakeTime:
    def __init__(self):
        self.count = 0

    def monotonic(self):
        self.count += 31
        return self.count


class Locator:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def all_text_contents(self):
        return self.items

    def count(self):
        return len(self.items)


class Anchor:
    def get_attribute(self, name):
        assert name == "href"
        return "/lucasyahn/status/123456789"


class Article:
    def __init__(self, text):
        self.text = text

    def inner_text(self, **kwargs):
        return self.text

    def locator(self, selector):
        assert selector == "a"
        return Locator([Anchor()])


class FakeContext:
    def __init__(self):
        self.new_pages = 0

    def new_page(self):
        self.new_pages += 1
        raise AssertionError("second browser tab forbidden")


class FakePage:
    def __init__(self, context, redirect=False, has_post=False):
        self.context = context
        self.url = "https://x.com/home"
        self.events = []
        self.redirect = redirect
        self.has_post = has_post

    def goto(self, url, **kwargs):
        self.events.append(("goto", url))
        if self.redirect and url == "https://x.com/lucasyahn":
            self.url = "https://x.com/otheraccount"
        else:
            self.url = url

    def wait_for_timeout(self, _):
        pass

    def locator(self, query):
        if query == "article":
            return Locator([Article("caption")] if self.has_post else [])
        if query == '[data-testid="tweetText"]':
            return Locator(["caption"])
        if query == "video":
            return Locator([object()])
        raise AssertionError("unexpected locator " + query)


def build_proof(mode="valid"):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    func = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "proof")
    def account(page):
        page.events.append(("account", page.url))
        if mode == "wrong_initial":
            raise RuntimeError("X_CLOUD_WRONG_ACCOUNT")
        if mode == "wrong_on_restore" and page.url == "https://x.com/home" and len(
                [v for v in page.events if v[0] == "goto"]) > 0:
            raise RuntimeError("X_CLOUD_WRONG_ACCOUNT")
        if mode == "missing_on_restore" and len(
                [v for v in page.events if v[0] == "goto"]) > 0:
            raise RuntimeError("X_CLOUD_IDENTITY_NOT_PROVEN")
    namespace = {"account": account, "urlparse": urlparse, "re": re,
                 "time": FakeTime()}
    exec(compile(ast.Module(body=[func],type_ignores=[]),"<proof>","exec"),namespace)
    return namespace["proof"]


class SingleTabProof(unittest.TestCase):
    def test_requires_verified_page_same_context(self):
        context = FakeContext()
        with self.assertRaisesRegex(RuntimeError,"INDEPENDENT_IDENTITY_REQUIRED"):
            build_proof()(context,"caption")
        other = FakePage(FakeContext())
        with self.assertRaisesRegex(RuntimeError,"INDEPENDENT_IDENTITY_REQUIRED"):
            build_proof()(context,"caption",verified_page=other)

    def test_wrong_account_denied_before_timeline(self):
        context=FakeContext()
        page=FakePage(context)
        with self.assertRaisesRegex(RuntimeError,"WRONG_ACCOUNT"):
            build_proof("wrong_initial")(context,"caption",verified_page=page)
        self.assertEqual(context.new_pages,0)
        self.assertEqual(page.events,[("account","https://x.com/home")])

    def test_no_match_restores_home_without_second_tab(self):
        context=FakeContext()
        page=FakePage(context)
        self.assertIsNone(build_proof()(context,"caption",verified_page=page))
        self.assertEqual(page.url,"https://x.com/home")
        self.assertEqual(context.new_pages,0)
        self.assertEqual([e[0] for e in page.events],
                         ["account","goto","goto","account"])

    def test_exact_owner_caption_and_video_confirm(self):
        context=FakeContext()
        page=FakePage(context,has_post=True)
        uri=build_proof()(context,"caption",verified_page=page)
        self.assertEqual(uri,"https://x.com/lucasyahn/status/123456789")
        self.assertEqual(page.url,"https://x.com/home")
        self.assertEqual(context.new_pages,0)

    def test_wrong_profile_redirect_denied_and_home_restored(self):
        context=FakeContext()
        page=FakePage(context,redirect=True)
        with self.assertRaisesRegex(RuntimeError,"TIMELINE_PROFILE_MISMATCH"):
            build_proof()(context,"caption",verified_page=page)
        self.assertEqual(page.url,"https://x.com/home")
        self.assertEqual(context.new_pages,0)

    def test_wrong_account_on_return_remains_blocked(self):
        context=FakeContext()
        page=FakePage(context)
        with self.assertRaisesRegex(RuntimeError,"WRONG_ACCOUNT"):
            build_proof("wrong_on_restore")(context,"caption",verified_page=page)
        self.assertEqual(page.url,"https://x.com/home")

    def test_missing_identity_on_return_never_ignored(self):
        context=FakeContext()
        page=FakePage(context)
        with self.assertRaisesRegex(RuntimeError,"HOME_IDENTITY_NOT_RESTORED"):
            build_proof("missing_on_restore")(context,"caption",verified_page=page)
        self.assertEqual(page.url,"https://x.com/home")

    def test_repeated_trials_prove_account_each_time(self):
        context=FakeContext()
        page=FakePage(context)
        self.assertIsNone(build_proof()(context,"caption",attempts=2,verified_page=page))
        self.assertEqual(len([v for v in page.events if v[0]=="account"]),4)
        self.assertEqual(context.new_pages,0)


if __name__ == "__main__":
    unittest.main()
