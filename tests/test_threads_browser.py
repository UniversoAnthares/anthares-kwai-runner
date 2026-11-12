#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, mark_attempt, reserve
from social_adapters.threads_browser import canonical_post_url, external_id_from_url, publish


class ThreadsBrowserTests(unittest.TestCase):
    def test_threads_url_normalization_and_id(self):
        url = canonical_post_url("Lucas", "/@Lucas/post/DHxAb12CdEf?xmt=tracking")
        self.assertEqual(url, "https://www.threads.com/@lucas/post/DHxAb12CdEf")
        self.assertEqual(external_id_from_url(url), "DHxAb12CdEf")

    def test_threads_net_is_accepted_and_normalized(self):
        url = canonical_post_url(
            "lucas", "https://www.threads.net/@lucas/post/ABC_def-12?utm_source=x"
        )
        self.assertEqual(url, "https://www.threads.com/@lucas/post/ABC_def-12")

    def test_threads_url_rejects_other_account(self):
        self.assertEqual(
            canonical_post_url("lucas", "https://www.threads.com/@other/post/ABC123"),
            "",
        )

    def test_threads_evidence_contract(self):
        validate_evidence(
            PublicationEvidence(
                "threads", "lucas", "ABC123", "https://www.threads.com/@lucas/post/ABC123"
            ),
            "threads",
            "lucas",
        )
        with self.assertRaises(ValueError):
            validate_evidence(
                PublicationEvidence(
                    "threads", "lucas", "ABC123", "https://www.threads.com/@other/post/ABC123"
                ),
                "threads",
                "lucas",
            )

    def test_ledger_reserves_and_confirms_threads(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            row = reserve(db, "live-threads", 1000, 9000, "threads", "lucas", "c" * 64)
            self.assertTrue(mark_attempt(db, row["id"]))
            self.assertTrue(
                confirm(
                    db,
                    row["id"],
                    "ABC123",
                    "https://www.threads.com/@lucas/post/ABC123",
                )
            )
            again = reserve(db, "live-threads", 1000, 9000, "threads", "lucas", "c" * 64)
            self.assertTrue(again["already_published"])

    def test_dry_run_needs_no_browser_session(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            video.write_bytes(b"synthetic-video")
            out = publish(
                "threads",
                str(video),
                "caption",
                "lucas",
                Path(td) / "profile",
                commit=False,
            )
            self.assertEqual(out["status"], "DRY_RUN")
            self.assertEqual(out["platform"], "threads")
            self.assertEqual(len(out["content_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
