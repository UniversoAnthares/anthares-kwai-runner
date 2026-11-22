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
        ), patch.object(c, "post_comment_once", side_effect=lambda *args: calls.append("click") or True):
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
        ), patch.object(c, "post_comment_once", side_effect=lambda *args: submitted.append(1) or True):
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
        ), patch.object(c, "post_comment_once", side_effect=TimeoutError("ambiguous")) as action:
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


if __name__ == "__main__":
    unittest.main()
