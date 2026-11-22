"""Contract tests for TikTok one-comment-per-confirmed-publication feature."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cortes_tiktok_after_publish_comment as c


class StableRandom:
    def choice(self, seq):
        return seq[0]

    def shuffle(self, values):
        values.reverse()


class CommentTests(unittest.TestCase):
    def test_messages_never_repeat_any_of_30_previous(self):
        recent = [{"comment_text": text} for text in c.COMMENT_LIBRARY[:30]]
        self.assertEqual(c.select_message(recent, StableRandom()), c.COMMENT_LIBRARY[30])
        self.assertEqual(len(c.COMMENT_LIBRARY), len(set(x.casefold() for x in c.COMMENT_LIBRARY)))

    def test_last_30_only(self):
        recent = [{"comment_text": c.COMMENT_LIBRARY[0]}] * 30 + [
            {"comment_text": c.COMMENT_LIBRARY[1]}]
        result = c.select_message(recent, StableRandom())
        self.assertNotEqual(result, c.COMMENT_LIBRARY[0])

    def test_rejects_own_accounts_and_external_links(self):
        self.assertIsNone(c.normalize_candidate("https://www.tiktok.com/@lucasrosalem4/video/1234567890123456",
                                                 "universo.anthares"))
        self.assertIsNone(c.normalize_candidate("https://evil.example/@someone/video/1234567890123456",
                                                 "lucasrosalem4"))
        self.assertIsNone(c.normalize_candidate("http://www.tiktok.com/@someone/video/1234567890123456",
                                                 "lucasrosalem4"))
        self.assertEqual(
            c.normalize_candidate("https://www.tiktok.com/@somecreator/video/1234567890123456?foo=bar",
                                  "universo.anthares"),
            ("https://www.tiktok.com/@somecreator/video/1234567890123456", "1234567890123456"))

    def test_unconfirmed_reservation_never_posts(self):
        calls = []
        with patch.object(c, "verify_owner"), patch.object(
            c, "select_target", return_value=("1234567890123457", "https://www.tiktok.com/@person/video/1234567890123457")
        ), patch.object(c, "prepare_comment", return_value=object()), patch.object(c, "post_comment_once", side_effect=lambda *args: calls.append("click") or True):
            result = c._execute(
                object(), "universo.anthares", "1234567890123456", [],
                c.COMMENT_LIBRARY[0],
                lambda payload: {"ok": False, "reserved": False},
                lambda payload: calls.append("complete"))
        self.assertEqual(result, "already_reserved")
        self.assertEqual(calls, [])

    def test_reservation_is_one_click_and_one_receipt(self):
        submitted = []
        receipts = []
        with patch.object(c, "verify_owner"), patch.object(
            c, "select_target", return_value=("1234567890123457", "https://www.tiktok.com/@person/video/1234567890123457")
        ), patch.object(c, "prepare_comment", return_value=object()), patch.object(c, "post_comment_once", side_effect=lambda *args: submitted.append(1) or True):
            result = c._execute(object(), "lucasrosalem4", "1234567890123456", [],
                                c.COMMENT_LIBRARY[0],
                                lambda payload: {"ok": True, "reserved": True},
                                lambda payload: receipts.append(payload))
        self.assertEqual(result, "posted")
        self.assertEqual(len(submitted), 1)
        self.assertEqual(receipts, [{
            "source_video_id": "1234567890123456",
            "target_video_id": "1234567890123457",
            "status": "posted"}])

    def test_ambiguous_click_stays_uncertain_no_retry(self):
        receipts = []
        with patch.object(c, "verify_owner"), patch.object(
            c, "select_target", return_value=("1234567890123457", "https://www.tiktok.com/@person/video/1234567890123457")
        ), patch.object(c, "prepare_comment", return_value=object()), patch.object(c, "post_comment_once", side_effect=TimeoutError("ambiguous")) as action:
            with self.assertRaises(TimeoutError):
                c._execute(object(), "lucasrosalem4", "1234567890123456", [],
                           c.COMMENT_LIBRARY[0],
                           lambda payload: {"ok": True, "reserved": True},
                           lambda payload: receipts.append(payload))
        self.assertEqual(action.call_count, 1)
        self.assertEqual(receipts[0]["status"], "uncertain")

    def test_failure_is_optional_after_confirmation(self):
        with patch.dict(os.environ, {"TIKTOK_POST_COMMENT_ENABLED": "true"}), patch.object(
            c, "verify_owner", side_effect=RuntimeError("login_required")):
            result = c.after_confirmed(
                account="universo.anthares", source_video_id="1234567890123456",
                recent_call=lambda: {"ok": True, "recent": []},
                reserve_call=lambda payload: self.fail("must not reserve"),
                complete_call=lambda payload: self.fail("must not complete"),
                existing_page=object())
        self.assertEqual(result, "unavailable")

    def test_disabled_means_no_requests(self):
        with patch.dict(os.environ, {"TIKTOK_POST_COMMENT_ENABLED": "false"}):
            result = c.after_confirmed(
                account="universo.anthares", source_video_id="1234567890123456",
                recent_call=lambda: self.fail("disabled"),
                reserve_call=lambda payload: self.fail("disabled"),
                complete_call=lambda payload: self.fail("disabled"),
                existing_page=object())
        self.assertEqual(result, "disabled")

    def test_account_identity_required(self):
        result = c.after_confirmed(
            account="someotheruser", source_video_id="1234567890123456",
            recent_call=lambda: self.fail("identity_invalid"),
            reserve_call=lambda payload: self.fail("identity_invalid"),
            complete_call=lambda payload: self.fail("identity_invalid"),
            existing_page=object())
        self.assertEqual(result, "identity_invalid")




    def test_editor_failure_occurs_before_any_neon_reservation(self):
        calls=[]
        with patch.object(c, "verify_owner"), patch.object(
            c, "select_target", return_value=(
                "1234567890123457", "https://www.tiktok.com/@person/video/1234567890123457")
        ), patch.object(c, "prepare_comment", side_effect=TimeoutError("not-clickable")), patch.object(
            c, "post_comment_once", side_effect=lambda *a: calls.append("clicked")):
            result=c._execute(
                object(), "lucasrosalem4", "1234567890123456", [],
                c.COMMENT_LIBRARY[0],
                lambda p: calls.append("reserve"),
                lambda p: calls.append("complete"))
        self.assertEqual(result, "composer_unavailable")
        self.assertEqual(calls, [])

    def test_prepared_button_is_passed_to_only_click_after_reservation(self):
        button=object()
        order=[]
        with patch.object(c, "verify_owner"), patch.object(
            c, "select_target", return_value=(
                "1234567890123457", "https://www.tiktok.com/@person/video/1234567890123457", button)
        ), patch.object(c, "prepare_comment", side_effect=AssertionError("already prepared")), patch.object(
            c, "post_comment_once", side_effect=lambda *args: (
                order.append(("click", args[2] is button)) or True)):
            result=c._execute(
                object(), "lucasrosalem4", "1234567890123456", [],
                c.COMMENT_LIBRARY[0],
                lambda p: order.append(("reserve", True)) or {"ok":True,"reserved":True},
                lambda p: order.append(("complete", p["status"])))
        self.assertEqual(result, "posted")
        self.assertEqual(order, [("reserve",True),("click",True),("complete","posted")])


class FeedDiscoveryTests(unittest.TestCase):
    """Regression for both observed TikTok home page layouts."""

    class Random:
        def randint(self, low, high):
            return low

        def shuffle(self, seq):
            seq.reverse()

    class FakeLinks:
        def __init__(self, parent):
            self.parent = parent

        def evaluate_all(self, script):
            if self.parent.in_detail:
                return []
            if self.parent.scrolls < 2:
                return []
            return [
                "https://www.tiktok.com/@anotherwriter/video/7711043089078471944",
                "https://www.tiktok.com/@universo.anthares/video/7711044202028682516",
            ]

    class FakePage:
        def __init__(self):
            self.url = "https://www.tiktok.com/"
            self.scrolls = 0
            self.in_detail = False
            self.initial_sources = []

        def goto(self, url, **kwargs):
            self.url = url
            self.in_detail = "/video/" in url
            if not self.in_detail:
                self.initial_sources.append(url)
                self.scrolls = 0

        def wait_for_timeout(self, duration):
            pass

        def locator(self, selector):
            if selector != 'a[href*="/video/"]':
                raise AssertionError("unexpected selector: " + selector)
            return FeedDiscoveryTests.FakeLinks(self)

        def evaluate(self, script):
            self.scrolls += 1
            return {"container": "feed", "before": self.scrolls - 1,
                    "after": self.scrolls}

    def test_home_scroll_finds_real_video_link_after_initial_empty_dom(self):
        page = self.FakePage()
        with patch.object(c, "guard_page"), patch.object(c, "open_comment_editor",
                                                      return_value=object()):
            target = c.select_target(page, "lucasrosalem4", [], self.Random())
        self.assertEqual(target, ("7711043089078471944",
                                  "https://www.tiktok.com/@anotherwriter/video/7711043089078471944"))
        self.assertEqual(page.initial_sources, ["https://www.tiktok.com/"])

    def test_recent_target_is_excluded_after_scroll(self):
        page = self.FakePage()
        recent = [{"target_video_id": "7711043089078471944"}]
        with patch.object(c, "guard_page"), patch.object(c, "open_comment_editor",
                                                      return_value=object()):
            target = c.select_target(page, "lucasrosalem4", recent, self.Random())
        self.assertIsNone(target)

    def test_scroller_targets_virtualized_feed_not_only_window(self):
        class Page:
            def evaluate(self, script):
                self.script = script
                return {"container": "feed", "before": 0, "after": 868}
        page = Page()
        self.assertEqual(c.scroll_discovery(page)["after"], 868)
        self.assertIn("#column-list-container", page.script)

    def test_tiktok_slider_modal_is_security_challenge_before_any_comment(self):
        class Node:
            def __init__(self, shown):
                self.shown=shown

            @property
            def first(self):
                return self

            def count(self):
                return int(self.shown)

            def is_visible(self, **kwargs):
                return self.shown

        class Page:
            url = "https://www.tiktok.com/@danteachr/video/7710173903745764616"

            def locator(self, selector):
                return Node("captcha-verify-container" in selector)

        with self.assertRaisesRegex(RuntimeError,"TIKTOK_COMMENT_SECURITY_CHALLENGE"):
            c.guard_page(Page())

    def test_after_confirmed_reports_slider_and_never_reserves(self):
        with patch.dict(os.environ,{"TIKTOK_POST_COMMENT_ENABLED":"true"}), patch.object(
            c,"verify_owner",side_effect=RuntimeError("TIKTOK_COMMENT_SECURITY_CHALLENGE")
        ):
            r=c.after_confirmed(
                account="lucasrosalem4",source_video_id="7711050254891633928",
                recent_call=lambda:{"ok":True,"recent":[]},
                reserve_call=lambda payload:self.fail("security challenge forbids reservation"),
                complete_call=lambda payload:self.fail("security challenge forbids completion"),
                existing_page=object())
        self.assertEqual(r,"security_challenge")

    def test_hidden_captcha_does_not_block_legitimate_pages(self):
        class Node:
            def __init__(self, visible):
                self.visible = visible

            @property
            def first(self):
                return self

            def count(self):
                return 1

            def is_visible(self, **kwargs):
                return self.visible

        class Page:
            url = "https://www.tiktok.com/explore"

            def __init__(self, visible):
                self.visible = visible

            def locator(self, selector):
                return Node(self.visible and "captcha" in selector)

        c.guard_page(Page(False))
        with self.assertRaisesRegex(RuntimeError, "SECURITY_CHALLENGE"):
            c.guard_page(Page(True))


if __name__ == "__main__":
    unittest.main()
