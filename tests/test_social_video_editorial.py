"""Pure and fail-closed tests; never contact Pinterest or LinkedIn."""
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from anthares_publisher.editorial import (
    SUFFIX, WEBSITE, add_site_to_keywords, branded_title, prepare_publication_metadata,
)
from anthares_publisher.media_model import Clip, Publication


class EditorialTests(unittest.TestCase):
    def test_brand_is_last_in_title_and_never_duplicated(self):
        title = branded_title("A poesia de Homero")
        self.assertEqual(title, "A poesia de Homero" + SUFFIX)
        self.assertEqual(branded_title(title), title)
        self.assertEqual(branded_title("A poesia de Homero | Universo Anthares"), title)
        self.assertEqual(branded_title("A poesia de Homero — Universo Anthares"), title)

    def test_title_limits_reserve_suffix(self):
        title = branded_title("Uma discussão extremamente longa sobre literatura", limit=28)
        self.assertTrue(title.endswith(SUFFIX))
        self.assertLessEqual(len(title), 28)

    def test_website_in_keywords_and_caption(self):
        out = prepare_publication_metadata({
            "title": "A teoria da narrativa",
            "description": "#Literatura #Livros",
            "tags": "Literatura, Narrativa",
            "keywords": "#Classicos",
            "media_url": "https://example.test/video.mp4",
        })
        self.assertTrue(out["title"].endswith(SUFFIX))
        for key in ("description", "text", "tags", "keywords"):
            self.assertIn(WEBSITE, out[key])
        self.assertEqual(prepare_publication_metadata(out)["title"], out["title"])
        self.assertEqual(prepare_publication_metadata(out)["description"].count(WEBSITE), 1)
        self.assertEqual(out["media_url"], "https://example.test/video.mp4")

    def test_hashtag_is_not_malformed_as_url(self):
        self.assertEqual(add_site_to_keywords("#Livros"), "#Livros " + WEBSITE)

    def test_pinterest_round_and_linkedin_daily_cap(self):
        clip = Clip("live-1", 0, 60000, "short", "1"*64)
        self.assertIsNone(Publication(clip, "pinterest", "primary").daily_limit)
        self.assertIsNone(Publication(clip, "instagram", "primary").daily_limit)
        self.assertIsNone(Publication(clip, "linkedin", "primary").daily_limit)


class VideoReadyTests(unittest.TestCase):
    def _call(self, platform, overrides=None):
        env = os.environ.copy()
        for key in ("PINTEREST_ACCESS_TOKEN", "PINTEREST_BOARD_ID", "PINTEREST_COVER_IMAGE_URL",
                    "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN", "ANTHARES_SOCIAL_COMMIT"):
            env.pop(key, None)
        env.update(overrides or {})
        p = subprocess.run(
            [sys.executable, "social_adapters/direct_social.py"],
            input=__import__("json").dumps({
                "platform": platform, "account_id": "primary",
                "title": "A tragédia grega",
                "media_url": "https://example.invalid/clip.mp4",
            }), text=True, capture_output=True, env=env, timeout=15,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        return __import__("json").loads(p.stdout)

    def test_pinterest_auth_gate(self):
        result = self._call("pinterest")
        self.assertEqual(result["status"], "AUTH_OR_CONFIG_REQUIRED")
        self.assertEqual(result["destination_key"], "pinterest:primary")

    def test_neon_consumer_is_fail_closed_without_explicit_arm(self):
        p = subprocess.run(
            [sys.executable, "tools/cortes_social_queue_consumer.py",
             "--platform", "pinterest", "--account", "primary", "--preflight"],
            capture_output=True, text=True,
            env={k:v for k,v in os.environ.items() if k != "ANTHARES_SOCIAL_COMMIT"},
            timeout=15,
        )
        self.assertEqual(p.returncode, 3)
        self.assertEqual(__import__("json").loads(p.stdout)["status"], "AUTH_OR_CONFIG_REQUIRED")

    def test_social_consumer_rejects_unsafe_job(self):
        from tools.cortes_social_queue_consumer import _safe_job
        baseline = {
            "target_key": "pinterest:primary", "duration_class": "short",
            "payload": {"title": "Um tema literário",
                        "media_url": "https://anthares.us/media/clip.mp4",
                        "duration_seconds": 60},
        }
        out = _safe_job(baseline, "pinterest", "primary")
        self.assertEqual(out["media_url"], baseline["payload"]["media_url"])
        bad = {**baseline, "payload": {**baseline["payload"],
                                    "media_url": "https://evil.invalid/private.mp4"}}
        with self.assertRaisesRegex(ValueError, "origin"):
            _safe_job(bad, "pinterest", "primary")

    def test_linkedin_auth_gate(self):
        result = self._call("linkedin")
        self.assertEqual(result["status"], "AUTH_OR_CONFIG_REQUIRED")
        self.assertEqual(result["destination_key"], "linkedin:primary")

    def test_pinterest_ready_does_not_upload(self):
        result = self._call("pinterest", {
            "PINTEREST_ACCESS_TOKEN": "synthetic",
            "PINTEREST_BOARD_ID": "synthetic-board",
            "PINTEREST_COVER_IMAGE_URL": "https://example.invalid/cover.jpg",
        })
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["title"].endswith(SUFFIX))

    def test_linkedin_ready_does_not_upload(self):
        result = self._call("linkedin", {
            "LINKEDIN_ACCESS_TOKEN": "synthetic",
            "LINKEDIN_AUTHOR_URN": "urn:li:organization:12345",
        })
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["title"].endswith(SUFFIX))


if __name__ == "__main__":
    unittest.main()
