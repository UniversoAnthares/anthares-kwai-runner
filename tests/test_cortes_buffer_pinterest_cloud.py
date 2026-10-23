"""Safe Pinterest cloud consumer tests, no live queue or posts."""
import unittest
from unittest.mock import patch
from tools import cortes_buffer_pinterest_cloud as p


class PinterestCloudTests(unittest.TestCase):
    def test_correct_account_short_master(self):
        item={"target_key":"pinterest:lucasyahn","duration_class":"short",
              "payload":{"platform":"pinterest","account_id":"lucasyahn",
                         "title":"Literatura","media_url":"https://anthares.us/video.mp4",
                         "duration_seconds":45}}
        row=p.safe_payload(item)
        self.assertEqual(row["platform"],"pinterest")
        self.assertEqual(row["account_id"],"lucasyahn")

    def test_wrong_account_blocked(self):
        item={"target_key":"pinterest:lucasyahn","duration_class":"short",
              "payload":{"platform":"pinterest","account_id":"primary"}}
        with self.assertRaisesRegex(RuntimeError,"ACCOUNT_INVALID"):
            p.safe_payload(item)

    def test_sent_pin_requires_readback_url(self):
        pin="12345"
        def valid(_query):
            return {"post":{"id":pin,"channelId":p.PINTEREST_ID,
                            "schedulingType":"automatic","status":"sent",
                            "externalLink":"https://www.pinterest.com/pin/1234567/"}}
        with patch.object(p,"api",side_effect=valid):
            self.assertEqual(p.verify_sent_post(pin),
                             "https://www.pinterest.com/pin/1234567/")

    def test_unsent_pin_is_not_confirmed(self):
        def pending(_query):
            return {"post":{"id":"123","channelId":p.PINTEREST_ID,
                            "schedulingType":"automatic","status":"scheduled"}}
        with patch.object(p,"api",side_effect=pending):
            self.assertIsNone(p.verify_sent_post("123"))

    def test_missing_buffer_board_fails_ci_without_leasing(self):
        with patch.object(p,"cloud_only"), patch.object(p,"queue",side_effect=lambda action,*args: {"enabled":True,"remaining":10} if action=="policy" else {"active":False}), patch.object(p,"reconcile",return_value=0), \
             patch("social_adapters.buffer_three_channels.pinterest_boards",
                   return_value=[]), patch.object(p,"alternate_pinterest_boards",
                   return_value=[]), patch.object(p.time,"sleep"), \
             patch.object(p,"publish_once") as publish:
            with self.assertRaisesRegex(p.BufferBlocked,"BOARD_NOT_SYNCED"):
                p.main()
            publish.assert_not_called()

    def test_buffer_500_is_visible_incident_without_leasing(self):
        with patch.object(p,"cloud_only"), patch.object(p,"queue",side_effect=lambda action,*args: {"enabled":True,"remaining":10} if action=="policy" else {"active":False}), patch.object(p,"reconcile",return_value=0), \
             patch("social_adapters.buffer_three_channels.pinterest_boards",
                   side_effect=p.BufferBlocked("BUFFER_HTTP_500")), \
             patch.object(p,"alternate_pinterest_boards",
                   side_effect=p.BufferBlocked("BUFFER_HTTP_500")), \
             patch.object(p.time,"sleep"), patch.object(p,"publish_once") as publish:
            with self.assertRaisesRegex(p.BufferBlocked,"BOARD_READ_FAILED"):
                p.main()
            publish.assert_not_called()

    def test_alternate_board_resolver_recovers_500_safely(self):
        from social_adapters.buffer_three_channels import PINTEREST_PUBLIC_BOARD_ID
        with patch("social_adapters.buffer_three_channels.pinterest_boards",
                   side_effect=p.BufferBlocked("BUFFER_HTTP_500")), \
             patch.object(p,"alternate_pinterest_boards",
                   return_value=[{"serviceId":PINTEREST_PUBLIC_BOARD_ID}]), \
             patch.object(p.time,"sleep") as sleep:
            self.assertEqual(p.board_gate(),PINTEREST_PUBLIC_BOARD_ID)
            sleep.assert_not_called()

    def test_alternate_resolver_requires_pinned_pinterest_channel(self):
        from social_adapters.buffer_three_channels import PINTEREST_PUBLIC_BOARD_ID
        def fake(query):
            if "organizations" in query:
                return {"account":{"organizations":[{"id":"org-1"}]}}
            return {"channels":[
                {"id":"wrong-channel","service":"pinterest",
                 "metadata":{"boards":[{"serviceId":PINTEREST_PUBLIC_BOARD_ID}]}}
            ]}
        with patch.object(p,"api",side_effect=fake):
            self.assertEqual(p.alternate_pinterest_boards(),[])

    def test_alternate_resolver_finds_only_own_channel(self):
        from social_adapters.buffer_three_channels import PINTEREST_PUBLIC_BOARD_ID
        def fake(query):
            if "organizations" in query:
                return {"account":{"organizations":[{"id":"org-1"}]}}
            return {"channels":[
                {"id":p.PINTEREST_ID,"service":"pinterest",
                 "metadata":{"boards":[{"serviceId":PINTEREST_PUBLIC_BOARD_ID}]}}
            ]}
        with patch.object(p,"api",side_effect=fake):
            self.assertEqual(p.alternate_pinterest_boards(),
                             [{"serviceId":PINTEREST_PUBLIC_BOARD_ID}])

    def test_board_ready_can_resume_without_operator(self):
        from social_adapters.buffer_three_channels import PINTEREST_PUBLIC_BOARD_ID
        with patch.object(p,"cloud_only"), patch.object(p,"queue",side_effect=lambda action,*args: {"enabled":True,"remaining":10} if action=="policy" else {"active":False}), patch.object(p,"reconcile",return_value=0), \
             patch("social_adapters.buffer_three_channels.pinterest_boards",
                   return_value=[{"serviceId":PINTEREST_PUBLIC_BOARD_ID}]), \
             patch.object(p,"publish_once",return_value="SCHEDULED_IN_BUFFER") as publish:
            self.assertEqual(p.main(),0)
            publish.assert_called_once()

    def test_bad_readback_does_not_prevent_other_pins_reconciling(self):
        jobs=[{"id":"a","remote_id":"bad"},{"id":"b","remote_id":"good"},
              {"id":"c","remote_id":""}]
        def queue(action,payload=None):
            if action=="pending":return {"jobs":jobs}
            if action=="reconcile":return {"ok":True}
            raise AssertionError(action)
        def verify(remote_id):
            if remote_id=="bad":
                raise p.BufferBlocked("BUFFER_HTTP_500")
            return "https://www.pinterest.com/pin/123456/"
        with patch.object(p,"queue",side_effect=queue) as q, \
             patch.object(p,"verify_sent_post",side_effect=verify):
            self.assertEqual(p.reconcile(),1)
            self.assertEqual(q.call_count,2)

    def test_sent_pinterest_url_confirms_existing_neon_job_once(self):
        pin_url="https://www.pinterest.com/pin/819514463494241678/"
        calls=[]
        def backend(action,payload=None):
            calls.append((action,payload))
            if action=="pending":
                return {"jobs":[{"id":"original-job","remote_id":"6ad908b1c2fd6c7a0efc0f97"}]}
            if action=="reconcile":
                return {"ok":True,"job":{"status":"confirmed"}}
            raise AssertionError(action)
        with patch.object(p,"queue",side_effect=backend), \
             patch.object(p,"verify_sent_post",return_value=pin_url):
            self.assertEqual(p.reconcile(),1)
        self.assertEqual([x[0] for x in calls],["pending","reconcile"])
        self.assertEqual(calls[1][1],{
            "id":"original-job","remote_id":"6ad908b1c2fd6c7a0efc0f97",
            "external_link":pin_url,
        })

    def test_no_cloud_credentials_fails_without_queue_call(self):
        with patch.dict(p.os.environ,{"GITHUB_ACTIONS":"false","BUFFER_API_KEY":""}):
            with self.assertRaisesRegex(RuntimeError,"CLOUD_ONLY"):
                p.cloud_only()


class PinterestMediaPolicy(unittest.TestCase):
    def test_invalid_cloud_media_isolated_before_start(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        pub=(root/"tools"/"cortes_buffer_pinterest_cloud.py").read_text(encoding="utf8")
        neon=(root/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf8")
        self.assertIn('is_media_missing(payload["media_url"])',pub)
        self.assertIn('queue("media-missing",fence)',pub)
        self.assertIn('notify_media_p0(row["id"]',pub)
        self.assertIn("PINTEREST_MEDIA_MISSING_FENCE_REJECTED",neon)
        self.assertIn("retry_after_date",neon)
        self.assertIn("ORDER BY p.created_at,p.updated_at,p.id",neon)


class PinterestCooldownGate(unittest.TestCase):
    def test_cooldown_skips_buffer_api_completely(self):
        with patch.object(p,"cloud_only"), \
             patch.object(p,"queue",return_value={"active":True,"cooldown_until":"2026-10-22T05:00:00Z"}), \
             patch.object(p,"reconcile") as rec, patch.object(p,"board_gate") as board, \
             patch.object(p,"publish_once") as pub:
            self.assertEqual(p.main(),0)
            rec.assert_not_called()
            board.assert_not_called()
            pub.assert_not_called()


class PinterestRateLimitCooldown(unittest.TestCase):
    def test_fenced_neon_429_shared_backoff(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        py=(root/"tools"/"cortes_buffer_pinterest_cloud.py").read_text(encoding="utf8")
        neon=(root/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf8")
        self.assertIn('queue("cooldown-status")',py)
        self.assertIn('buffer_cooldown_seconds(exc,1800)',py)
        self.assertIn('if str(exc)=="BUFFER_HTTP_429"',py)
        self.assertIn("cortes_buffer_provider_cooldowns",neon)
        self.assertIn("cooldown_until>now()",neon)
        self.assertIn("cortes_buffer_provider_cooldowns",neon)


if __name__=="__main__":
    unittest.main()
