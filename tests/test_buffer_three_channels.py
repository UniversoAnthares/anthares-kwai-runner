"""No network and no publishing; pinned real channel identities."""
import os
import unittest
from unittest.mock import patch
from social_adapters import buffer_three_channels as b

def master(platform="instagram"):
    return {"platform":platform,"title":"Uma narrativa","description":"#Literatura","duration_seconds":54,
            "media_url":"https://anthares.us/wp-content/uploads/2026/10/teste.mp4"}

def channel(platform):
    names={"instagram":"universoanthares","pinterest":"lucasyahn","linkedin":"Universo Anthares"}
    urls={"instagram":"https://instagram.com/universoanthares",
          "pinterest":"https://www.pinterest.com/lucasyahn",
          "linkedin":"https://www.linkedin.com/company/145345334"}
    return {"id":b.PINNED_CHANNELS[platform][0],"service":platform,
            "name":names[platform],"displayName":names[platform],"externalLink":urls[platform]}

class BufferPinnedTests(unittest.TestCase):
    def test_all_three_verified_accounts(self):
        for platform in b.SERVICES:
            c=channel(platform)
            self.assertEqual(b.validate_channel(platform,c["id"],[c]),c)

    def test_wrong_destination_id_rejected(self):
        for platform in b.SERVICES:
            with self.assertRaisesRegex(b.BufferBlocked,"NOT_PINNED"):
                b.validate_channel(platform,"other",[channel(platform)])

    def test_wrong_destination_name_rejected(self):
        for platform in b.SERVICES:
            c=channel(platform); c["displayName"]="Wrong Account"
            with self.assertRaisesRegex(b.BufferBlocked,"NAME_UNVERIFIED"):
                b.validate_channel(platform,c["id"],[c])

    def test_fake_linkedin_profile_rejected(self):
        c=channel("linkedin"); c["externalLink"]="https://www.linkedin.com/in/145345334"
        with self.assertRaisesRegex(b.BufferBlocked,"URL_UNVERIFIED"):
            b.validate_channel("linkedin",c["id"],[c])

    def test_wrong_pinterest_link_rejected(self):
        c=channel("pinterest");c["externalLink"]="https://www.pinterest.com/other"
        with self.assertRaisesRegex(b.BufferBlocked,"URL_UNVERIFIED"):
            b.validate_channel("pinterest",c["id"],[c])

    def test_queue_paused_rejected(self):
        c=channel("linkedin");c["isQueuePaused"]=True
        with self.assertRaisesRegex(b.BufferBlocked,"CHANNEL_UNAVAILABLE"):
            b.validate_channel("linkedin",c["id"],[c])

    def test_branded_metadata(self):
        for platform in b.SERVICES:
            caption=b.prepare(master(platform))["caption"]
            self.assertTrue(caption.splitlines()[0].endswith(" ● Universo Anthares"))
            self.assertIn("www.anthares.us",caption)

    def test_dry_run_no_network(self):
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"0"}),patch.object(b,"api",side_effect=AssertionError("NETWORK")):
            self.assertEqual(b.schedule(master())["status"],"DRY_RUN")

    def test_schedule_is_not_publication_confirmation(self):
        platform="linkedin";c=channel(platform)
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_LINKEDIN_CHANNEL_ID":c["id"],"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted","RUNNER_OS":"Linux"}):
            with patch.object(b,"channels",return_value=[c]), patch.object(b,"api",return_value={"createPost":{"post":{"id":"buffer123"}}}):
                output=b.schedule(master(platform))
        self.assertEqual(output["status"],"SCHEDULED_IN_BUFFER")
        self.assertFalse(output["confirmed_on_social_network"])

    def test_local_pc_cannot_publish(self):
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","GITHUB_ACTIONS":"false","RUNNER_ENVIRONMENT":"","RUNNER_OS":"Windows"}):
            with patch.object(b,"api",side_effect=AssertionError("NETWORK")):
                with self.assertRaisesRegex(b.BufferBlocked,"CLOUD_HOSTED_RUNNER_REQUIRED"):
                    b.schedule(master())

    def test_self_hosted_actions_cannot_publish(self):
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"self-hosted","RUNNER_OS":"Windows"}):
            with patch.object(b,"api",side_effect=AssertionError("NETWORK")):
                with self.assertRaisesRegex(b.BufferBlocked,"CLOUD_HOSTED_RUNNER_REQUIRED"):
                    b.schedule(master())

    def test_external_master_blocked(self):
        with self.assertRaisesRegex(b.BufferBlocked,"MASTER_MP4_URL_INVALID"):
            b.prepare({**master(),"media_url":"https://example.com/clip.mp4"})

if __name__=="__main__":
    unittest.main()
