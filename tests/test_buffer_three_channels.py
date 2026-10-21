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

    def test_recover_board_from_own_sent_pins_when_buffer_metadata_fails(self):
        ch=b.PINNED_CHANNELS["pinterest"][0]
        def fake(query,token=None):
            if "channel(input:" in query:
                raise b.BufferBlocked("BUFFER_HTTP_500")
            if "organizations" in query:
                return {"account":{"organizations":[{"id":"org-1"}]}}
            return {"posts":{"edges":[{"node":{"channelId":ch,
                "metadata":{"board":{"serviceId":"123456","name":"Universo Anthares",
                                      "url":"https://pinterest.com/lucasyahn/anthares/"}}}}]}}
        with patch.dict(os.environ,{"BUFFER_PINTEREST_BOARD_ID":""}), patch.object(b,"api",side_effect=fake):
            self.assertEqual(b.resolve_pinterest_board(ch),"123456")

    def test_board_history_never_accepts_another_channel(self):
        ch=b.PINNED_CHANNELS["pinterest"][0]
        def fake(query,token=None):
            if "channel(input:" in query:
                raise b.BufferBlocked("BUFFER_HTTP_500")
            if "organizations" in query:
                return {"account":{"organizations":[{"id":"org-1"}]}}
            return {"posts":{"edges":[{"node":{"channelId":"attacker-other",
                "metadata":{"board":{"serviceId":"123456"}}}}]}}
        with patch.object(b,"api",side_effect=fake):
            with self.assertRaisesRegex(b.BufferBlocked,"BOARD_SELECTION_REQUIRED"):
                b.resolve_pinterest_board(ch)

    def test_select_single_board_or_explicit_board(self):
        choices=[{"serviceId":"1234","name":"Arte"},
                 {"serviceId":"5678","name":"Literatura"}]
        with self.assertRaisesRegex(b.BufferBlocked,"SELECTION_REQUIRED"):
            b.select_pinterest_board(choices)
        self.assertEqual(b.select_pinterest_board(choices,"5678"),"5678")
        with self.assertRaisesRegex(b.BufferBlocked,"NOT_OWNED"):
            b.select_pinterest_board(choices,"9876")
        self.assertEqual(b.select_pinterest_board(choices[:1]),"1234")

    def test_pinterest_video_mutation_includes_board_and_thumbnail(self):
        platform="pinterest"
        c=channel(platform)
        seen=[]
        def fake(query, token=None):
            seen.append(query)
            return {"createPost":{"post":{"id":"buffer-pin-123"}}}
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1",
                                     "BUFFER_PINTEREST_CHANNEL_ID":c["id"],
                                     "BUFFER_PINTEREST_BOARD_SERVICE_ID":"5678",
                                     "GITHUB_ACTIONS":"true",
                                     "RUNNER_ENVIRONMENT":"github-hosted",
                                     "RUNNER_OS":"Linux"}), \
             patch.object(b,"channels",return_value=[c]), \
             patch.object(b,"resolve_pinterest_board",return_value="5678"), \
             patch.object(b,"api",side_effect=fake):
            result=b.schedule(master(platform))
        self.assertEqual(result["status"],"SCHEDULED_IN_BUFFER")
        self.assertFalse(result["confirmed_on_social_network"])
        self.assertIn("boardServiceId",seen[0])
        self.assertIn("5678",seen[0])
        self.assertIn("thumbnailOffset: 2000",seen[0])

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

    def test_linkedin_same_day_uses_share_now_no_buffer_queue(self):
        profile=channel("linkedin")
        sent=[]
        def mock_api(query,token=None):
            sent.append(query)
            return {"createPost":{"post":{"id":"immediate-123"}}}
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_LINKEDIN_CHANNEL_ID":profile["id"],
                                  "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted","RUNNER_OS":"Linux"}):
            with patch.object(b,"channels",return_value=[profile]), patch.object(b,"api",side_effect=mock_api):
                out=b.schedule({**master("linkedin"),"same_day":True})
        self.assertEqual(out["status"],"SCHEDULED_IN_BUFFER")
        self.assertIn("mode: shareNow",sent[0])
        self.assertNotIn("mode: addToQueue",sent[0])
        self.assertFalse(out["confirmed_on_social_network"])

    def test_regular_buffer_mode_remains_queue(self):
        profile=channel("linkedin")
        sent=[]
        def mock_api(query,token=None):
            sent.append(query)
            return {"createPost":{"post":{"id":"scheduled-123"}}}
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_LINKEDIN_CHANNEL_ID":profile["id"],
                                  "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted","RUNNER_OS":"Linux"}):
            with patch.object(b,"channels",return_value=[profile]), patch.object(b,"api",side_effect=mock_api):
                b.schedule(master("linkedin"))
        self.assertIn("mode: addToQueue",sent[0])

    def test_instagram_mutation_forces_reel(self):
        profile=channel("instagram")
        captured=[]
        def mock_api(query, token=None):
            captured.append(query)
            return {"createPost":{"post":{"id":"ig-reel-1"}}}
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_INSTAGRAM_CHANNEL_ID":profile["id"],
                                 "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted","RUNNER_OS":"Linux"}):
            with patch.object(b,"channels",return_value=[profile]),patch.object(b,"api",side_effect=mock_api):
                result=b.schedule(master("instagram"))
        self.assertEqual(result["status"],"SCHEDULED_IN_BUFFER")
        self.assertIn("metadata: { instagram: { type: reel, shouldShareToFeed: true } }",captured[0])

    def test_pinterest_board_required_on_ambiguous_account(self):
        details={"channel":{"metadata":{"boards":[
            {"serviceId":"board-a","url":"https://www.pinterest.com/lucasyahn/a"},
            {"serviceId":"board-b","url":"https://www.pinterest.com/lucasyahn/b"}]}}}
        with patch.dict(os.environ,{"BUFFER_PINTEREST_BOARD_ID":""}):
            with patch.object(b,"api",return_value=details):
                with self.assertRaisesRegex(b.BufferBlocked,"PINTEREST_BOARD_NOT_VERIFIED"):
                    b.resolve_pinterest_board(b.PINNED_CHANNELS["pinterest"][0])

    def test_pinterest_verified_board_emitted_in_mutation(self):
        profile=channel("pinterest")
        captured=[]
        def mock_api(query,token=None):
            captured.append(query)
            if "channel(input:" in query:
                return {"channel":{"metadata":{"boards":[{"serviceId":"board-31","url":"https://pinterest.com/lucasyahn/anthares"}]}}}
            return {"createPost":{"post":{"id":"pin-1"}}}
        with patch.dict(os.environ,{"ANTHARES_SOCIAL_COMMIT":"1","BUFFER_PINTEREST_CHANNEL_ID":profile["id"],
                                 "BUFFER_PINTEREST_BOARD_ID":"board-31",
                                 "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted","RUNNER_OS":"Linux"}):
            with patch.object(b,"channels",return_value=[profile]),patch.object(b,"api",side_effect=mock_api):
                result=b.schedule(master("pinterest"))
        self.assertEqual(result["status"],"SCHEDULED_IN_BUFFER")
        self.assertIn("boardServiceId: \"board-31\"",captured[-1])
        self.assertIn("https://www.anthares.us",captured[-1])

    def test_pinterest_wrong_board_id_is_blocked(self):
        data={"channel":{"metadata":{"boards":[{"serviceId":"good","url":"https://pinterest.com/lucasyahn/a"}]}}}
        with patch.dict(os.environ,{"BUFFER_PINTEREST_BOARD_ID":"other"}),patch.object(b,"api",return_value=data):
            with self.assertRaisesRegex(b.BufferBlocked,"PINTEREST_BOARD_NOT_VERIFIED"):
                b.resolve_pinterest_board(b.PINNED_CHANNELS["pinterest"][0])

    def test_external_master_blocked(self):
        with self.assertRaisesRegex(b.BufferBlocked,"MASTER_MP4_URL_INVALID"):
            b.prepare({**master(),"media_url":"https://example.com/clip.mp4"})

if __name__=="__main__":
    unittest.main()
