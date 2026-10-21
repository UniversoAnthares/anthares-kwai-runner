"""Contract tests: no network, no publications."""
import os
import unittest
from unittest.mock import patch
from social_adapters import buffer_three_channels as b

def master(platform="instagram"):
    return {"platform": platform, "title": "Uma narrativa", "description": "#Literatura", "duration_seconds": 54,
            "media_url": "https://anthares.us/wp-content/uploads/2026/10/teste.mp4"}


class BufferThreeChannelTests(unittest.TestCase):
    def test_editorial_metadata_all_three(self):
        for platform in b.SERVICES:
            with self.subTest(platform=platform):
                result = b.prepare(master(platform))
                self.assertTrue(result["caption"].splitlines()[0].endswith(" ● Universo Anthares"))
                self.assertIn("www.anthares.us", result["caption"])

    def test_block_wrong_service(self):
        with self.assertRaisesRegex(b.BufferBlocked, "SERVICE_MISMATCH"):
            b.validate_channel("linkedin", "a", [{"id":"a","service":"instagram","name":"Universo Anthares"}])

    def test_block_linkedin_personal_profile(self):
        with self.assertRaisesRegex(b.BufferBlocked, "LINKEDIN_PAGE_NAME_MISMATCH"):
            b.validate_channel("linkedin", "a", [{"id":"a","service":"linkedin","name":"Lucas Rosalem"}])

    def test_block_wrong_instagram(self):
        with self.assertRaisesRegex(b.BufferBlocked, "INSTAGRAM_IDENTITY_UNVERIFIED"):
            b.validate_channel("instagram", "a", [{"id":"a","service":"instagram","name":"someone_else"}])

    def test_block_wrong_pinterest(self):
        with self.assertRaisesRegex(b.BufferBlocked, "PINTEREST_IDENTITY_UNVERIFIED"):
            b.validate_channel("pinterest", "a", [{"id":"a","service":"pinterest","name":"someone_else"}])

    def test_queue_paused_is_blocked(self):
        with self.assertRaisesRegex(b.BufferBlocked, "CHANNEL_UNAVAILABLE"):
            b.validate_channel("linkedin", "a", [{"id":"a","service":"linkedin","name":"Universo Anthares","isQueuePaused":True}])

    def test_dry_run_never_network(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT":"0"}), patch.object(b, "api", side_effect=AssertionError("NETWORK")):
            result=b.schedule(master())
            self.assertEqual(result["status"],"DRY_RUN")

    def test_no_schedule_without_id(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_INSTAGRAM_CHANNEL_ID":""}):
            with patch.object(b, "channels", return_value=[]):
                with self.assertRaisesRegex(b.BufferBlocked, "CHANNEL_ID_REQUIRED"):
                    b.schedule(master())

    def test_schedule_never_confirms_publication(self):
        with patch.dict(os.environ, {"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_LINKEDIN_CHANNEL_ID":"a"}):
            with patch.object(b, "channels", return_value=[{"id":"a","service":"linkedin","name":"Universo Anthares","externalLink":"https://www.linkedin.com/company/145345334/","type":"Page"}]):
                with patch.object(b, "api", return_value={"createPost":{"post":{"id":"buffer-123"}}}):
                    result=b.schedule(master("linkedin"))
        self.assertEqual(result["status"],"SCHEDULED_IN_BUFFER")
        self.assertFalse(result["confirmed_on_social_network"])

    def test_linkedin_profile_url_rejected(self):
        with self.assertRaisesRegex(b.BufferBlocked, "LINKEDIN_PAGE_URL_UNVERIFIED"):
            b.validate_channel("linkedin", "a", [{"id":"a","service":"linkedin","name":"Universo Anthares","externalLink":"https://www.linkedin.com/in/someone","type":"Page"}])

    def test_reject_external_video(self):
        with self.assertRaisesRegex(b.BufferBlocked, "MASTER_MP4_URL_INVALID"):
            b.prepare({**master(),"media_url":"https://example.org/other.mp4"})

if __name__=="__main__":
    unittest.main()
