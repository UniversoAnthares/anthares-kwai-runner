#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, mark_attempt, reserve
from social_adapters.community_browser import (
    canonical_channel_url,
    canonical_platform,
    canonical_post_url,
    external_id_from_url,
    publish,
)


class CommunityBrowserTests(unittest.TestCase):
    def test_odyssey_alias(self):
        self.assertEqual(canonical_platform("odyssey"), "odysee")
        self.assertEqual(canonical_platform("ODYSEE"), "odysee")

    def test_discord_channel_and_message_urls(self):
        channel = canonical_channel_url("https://discord.com/channels/111/222/")
        self.assertEqual(channel, "https://discord.com/channels/111/222")
        url = canonical_post_url("discord", "https://discord.com/channels/111/222/333")
        self.assertEqual(url, "https://discord.com/channels/111/222/333")
        self.assertEqual(external_id_from_url("discord", url), "333")

    def test_linkedin_urls(self):
        url = canonical_post_url("linkedin", "/feed/update/urn:li:activity:123456789/")
        self.assertEqual(url, "https://www.linkedin.com/feed/update/urn:li:activity:123456789/")
        self.assertEqual(external_id_from_url("linkedin", url), "123456789")
        post = canonical_post_url("linkedin", "https://www.linkedin.com/posts/lucas_title-activity-987654321-abcd")
        self.assertEqual(external_id_from_url("linkedin", post), "987654321")

    def test_medium_url(self):
        url = canonical_post_url("medium", "https://medium.com/@lucas/a-story-deadbeef?source=x")
        self.assertEqual(url, "https://medium.com/@lucas/a-story-deadbeef")
        self.assertEqual(external_id_from_url("medium", url), "a-story-deadbeef")

    def test_rumble_url(self):
        url = canonical_post_url("rumble", "https://rumble.com/v6abc12-my-video.html?mref=x")
        self.assertEqual(url, "https://rumble.com/v6abc12-my-video.html")
        self.assertEqual(external_id_from_url("rumble", url), "v6abc12-my-video.html")

    def test_odysee_url(self):
        url = canonical_post_url("odysee", "https://odysee.com/@lucas:1/video-title:2?view=1")
        self.assertEqual(url, "https://odysee.com/@lucas:1/video-title:2")
        self.assertEqual(external_id_from_url("odysee", url), "video-title:2")

    def test_evidence_accepts_extended_platforms(self):
        cases = [
            ("discord", "lucas", "333", "https://discord.com/channels/111/222/333"),
            ("linkedin", "lucas", "123", "https://www.linkedin.com/feed/update/urn:li:activity:123/"),
            ("medium", "lucas", "story-deadbeef", "https://medium.com/@lucas/story-deadbeef"),
            ("rumble", "lucas", "v6abc-video.html", "https://rumble.com/v6abc-video.html"),
            ("odysee", "lucas", "video:2", "https://odysee.com/@lucas:1/video:2"),
        ]
        for platform, account, remote_id, url in cases:
            with self.subTest(platform=platform):
                validate_evidence(PublicationEvidence(platform, account, remote_id, url), platform, account)

    def test_evidence_rejects_wrong_shapes(self):
        bad = [
            ("discord", "333", "https://discord.com/channels/111/222"),
            ("linkedin", "123", "https://www.linkedin.com/in/lucas/123"),
            ("medium", "story", "https://medium.com/some-publication/story"),
            ("rumble", "notvideo", "https://rumble.com/notvideo"),
            ("odysee", "video:2", "https://odysee.com/video:2"),
        ]
        for platform, remote_id, url in bad:
            with self.subTest(platform=platform):
                with self.assertRaises(ValueError):
                    validate_evidence(PublicationEvidence(platform, "lucas", remote_id, url), platform, "lucas")

    def test_ledger_extended_platforms_are_independent(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            ids = []
            for platform in ("discord", "linkedin", "medium", "rumble", "odysee"):
                row = reserve(db, "live-extended", 1000, 9000, platform, "lucas", "c" * 64)
                ids.append(row["id"])
            self.assertEqual(len(ids), len(set(ids)))

    def test_ledger_confirms_discord(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            row = reserve(db, "clip-discord", 0, 5000, "discord", "lucas", "d" * 64)
            self.assertTrue(mark_attempt(db, row["id"]))
            self.assertTrue(confirm(db, row["id"], "333", "https://discord.com/channels/111/222/333"))

    def test_dry_run_all_extended_platforms(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            video.write_bytes(b"synthetic-video")
            for platform in ("discord", "linkedin", "medium", "rumble", "odysee", "odyssey"):
                out = publish(
                    platform,
                    str(video),
                    "caption",
                    "lucas",
                    Path(td) / platform,
                    commit=False,
                    destination="https://discord.com/channels/111/222" if platform == "discord" else "",
                    media_url="https://example.com/video" if platform == "medium" else "",
                    title="Title",
                )
                self.assertEqual(out["status"], "DRY_RUN")
                self.assertEqual(len(out["content_sha256"]), 64)
                if platform == "odyssey":
                    self.assertEqual(out["platform"], "odysee")


if __name__ == "__main__":
    unittest.main()
