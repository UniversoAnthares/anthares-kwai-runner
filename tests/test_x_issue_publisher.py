import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))

from tools.x_issue_publisher import eligible, fingerprint, markers
from x_durable_ledger import identity, begin, AlreadyStarted


class XConsumerTests(unittest.TestCase):
    def payload(self):
        return {
            "platform": "x", "account": "lucasyahn", "duration_class": "long",
            "caption": "Aula sobre literatura e forma narrativa.",
            "media_url": "https://raw.githubusercontent.com/UniversoAnthares/media/x.mp4",
            "source_id": "Youtube_source_17",
            "segment_start": 600.0,
            "segment_end": 1200.0,
            "microedit": {"final_duration": 560.0},
        }

    def issue(self, payload):
        return {"title": "[X-PUBLISH] abc", "number": 123,
                "state": "open",
                "body": "```json\n" + json.dumps(payload) + "\n```",
                "created_at": "2026-10-21T12:00:00Z"}

    def test_longform_issue_is_accepted(self):
        self.assertIsNotNone(eligible(self.issue(self.payload())))

    def test_short_form_or_fixture_is_rejected(self):
        p = self.payload()
        p["duration_class"] = "short"
        self.assertIsNone(eligible(self.issue(p)))
        p["duration_class"] = "long"
        p["test_fixture"] = True
        self.assertIsNone(eligible(self.issue(p)))

    def test_wrong_account_untrusted_url_is_rejected(self):
        p = self.payload()
        p["account"] = "hijacked"
        self.assertIsNone(eligible(self.issue(p)))
        p["account"] = "lucasyahn"
        p["media_url"] = "https://evil.example/clip.mp4"
        self.assertIsNone(eligible(self.issue(p)))

    def test_fingerprint_is_stable_and_segment_scoped(self):
        p = self.payload()
        a = fingerprint(p)
        p["segment_start"], p["segment_end"] = 1300., 1900.
        self.assertNotEqual(a, fingerprint(p))
        p = self.payload()
        p["scan_start"] = 780
        self.assertNotEqual(a, fingerprint(p))
        self.assertEqual(identity("x_" + a), identity("x_" + a))

    def test_only_bot_markers_block_retry(self):
        bot = {"user": {"login": "github-actions[bot]"},
               "body": "X_SUBMISSION_STARTED_V1"}
        user = {"user": {"login": "user"}, "body": "X_SUBMISSION_STARTED_V1"}
        self.assertEqual(markers([user]), [])
        self.assertEqual(markers([bot]), [bot["body"]])

    def test_idempotency_input_validation(self):
        with self.assertRaises(ValueError):
            identity("short")
        self.assertEqual(len(identity("x_" + ("a" * 64))), 64)

    @patch("x_durable_ledger._connection")
    def test_daily_hardcap_blocks_tenth_plus_one(self, factory):
        from x_durable_ledger import DailyLimitReached
        conn = factory.return_value.__enter__.return_value
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = (10,)
        with self.assertRaises(DailyLimitReached):
            begin("x_" + ("c" * 64))

    @patch("x_durable_ledger._connection")
    def test_existing_db_claim_is_never_reused(self, factory):
        conn = factory.return_value.__enter__.return_value
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = None
        with self.assertRaises(AlreadyStarted):
            begin("x_" + ("b" * 64))


if __name__ == "__main__":
    unittest.main()
