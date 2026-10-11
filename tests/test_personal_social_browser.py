#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, mark_attempt, reserve
from social_adapters.personal_browser import canonical_post_url, external_id_from_url, publish


class PersonalSocialBrowserTests(unittest.TestCase):
    def test_x_url_normalization_and_id(self):
        url = canonical_post_url("x", "Lucas", "/someone/status/123456789")
        self.assertEqual(url, "https://x.com/lucas/status/123456789")
        self.assertEqual(external_id_from_url("x", url), "123456789")

    def test_instagram_url_normalization_and_id(self):
        url = canonical_post_url("instagram", "Lucas", "/reel/ABC_def-12/?utm_source=x")
        self.assertEqual(url, "https://www.instagram.com/reel/ABC_def-12/")
        self.assertEqual(external_id_from_url("instagram", url), "ABC_def-12")

    def test_evidence_accepts_x_and_instagram(self):
        validate_evidence(
            PublicationEvidence("x", "lucas", "123", "https://x.com/lucas/status/123"),
            "x",
            "lucas",
        )
        validate_evidence(
            PublicationEvidence("instagram", "lucas", "ABC", "https://www.instagram.com/reel/ABC/"),
            "instagram",
            "lucas",
        )

    def test_evidence_rejects_wrong_host(self):
        with self.assertRaises(ValueError):
            validate_evidence(
                PublicationEvidence("x", "lucas", "123", "https://example.com/lucas/status/123"),
                "x",
                "lucas",
            )

    def test_ledger_reserves_and_confirms_x(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            row = reserve(db, "live-1", 1000, 9000, "x", "lucas", "a" * 64)
            self.assertTrue(mark_attempt(db, row["id"]))
            self.assertTrue(confirm(db, row["id"], "123", "https://x.com/lucas/status/123"))
            again = reserve(db, "live-1", 1000, 9000, "x", "lucas", "a" * 64)
            self.assertTrue(again["already_published"])

    def test_same_clip_can_target_different_platforms(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            first = reserve(db, "live-2", 1000, 9000, "x", "lucas", "b" * 64)
            second = reserve(db, "live-2", 1000, 9000, "instagram", "lucas", "b" * 64)
            self.assertNotEqual(first["id"], second["id"])

    def test_dry_run_needs_no_playwright_session(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            video.write_bytes(b"synthetic-video")
            out = publish("x", str(video), "caption", "lucas", Path(td) / "profile", commit=False)
            self.assertEqual(out["status"], "DRY_RUN")
            self.assertEqual(len(out["content_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
