"""Buffer LinkedIn scheduler contracts: no network or posting in tests."""
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from social_adapters import buffer_linkedin as b


class BufferVideoTests(unittest.TestCase):
    def payload(self):
        return {
            "platform": "linkedin", "account_id": "primary",
            "title": "O monstro da literatura",
            "media_url": "https://anthares.us/wp-content/uploads/anthares-clips/2026/10/corte.mp4",
            "description": "#Livros #Literatura",
            "duration_seconds": 58, "duration_class": "short",
        }

    def test_caption_brand_suffix_and_website(self):
        result = b.plan(self.payload())
        self.assertTrue(result["caption"].splitlines()[0].endswith(" ● Universo Anthares"))
        self.assertIn("www.anthares.us", result["caption"])
        self.assertIn("#Literatura", result["caption"])

    def test_reject_non_anthares_media(self):
        x = {**self.payload(), "media_url": "https://example.net/video.mp4"}
        with self.assertRaisesRegex(ValueError, "anthares"):
            b.plan(x)

    def test_no_post_without_arm(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT": "0"}), patch.object(b, "_request", side_effect=AssertionError("unexpected network")):
            out = b.schedule_video(self.payload())
        self.assertEqual(out["status"], "DRY_RUN")

    def test_live_fails_without_api_key(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT": "1", "BUFFER_API_KEY": "",
                                      "BUFFER_LINKEDIN_CHANNEL_ID": ""}):
            with self.assertRaises(b.NotConfigured):
                b.schedule_video(self.payload())

    def test_channel_rejects_personal_profile(self):
        with patch.dict(os.environ, {"BUFFER_LINKEDIN_CHANNEL_ID": "abc"}):
            with patch.object(b, "_organizations", return_value=[{"id": "org1"}]):
                with patch.object(b, "_channels", return_value=[
                    {"id": "abc", "service": "linkedin", "name": "Lucas Rosalem", "externalLink": "https://www.linkedin.com/in/example"}
                ]):
                    with self.assertRaisesRegex(b.ProviderRejected, "wrong_linkedin_page"):
                        b.resolve_linkedin_channel()

    def test_channel_verified_page(self):
        with patch.dict(os.environ, {"BUFFER_LINKEDIN_CHANNEL_ID": "abc"}):
            with patch.object(b, "_organizations", return_value=[{"id": "org1"}]):
                with patch.object(b, "_channels", return_value=[
                    {"id": "abc", "service": "linkedin", "name": "Universo Anthares",
                     "externalLink": "https://www.linkedin.com/company/145345334/"}
                ]):
                    self.assertEqual(b.resolve_linkedin_channel(), "abc")

    def test_schedule_is_never_reported_published(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT": "1"}):
            with patch.object(b, "resolve_linkedin_channel", return_value="abc"):
                with patch.object(b, "_request", return_value={"createPost": {
                    "post": {"id": "bufferpost123", "dueAt": "2026-10-21T16:00:00Z"}}}) as req:
                    out = b.schedule_video(self.payload())
                    self.assertIn("assets:", req.call_args.args[0])
                    self.assertIn("video:", req.call_args.args[0])
        self.assertEqual(out["status"], "SCHEDULED_IN_BUFFER")
        self.assertTrue(out["requires_linkedin_readback"])
        self.assertIsNone(out["confirmation_evidence"])

    def test_graphql_mutation_errors_fail_closed(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT": "1"}):
            with patch.object(b, "resolve_linkedin_channel", return_value="abc"):
                with patch.object(b, "_request", return_value={"createPost": {"message": "queue is full"}}):
                    with self.assertRaises(b.ProviderRejected):
                        b.schedule_video(self.payload())


if __name__ == "__main__":
    unittest.main()
