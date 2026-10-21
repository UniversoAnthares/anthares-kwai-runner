import os
import unittest
from unittest.mock import patch
from tools import cortes_buffer_linkedin_cloud as publisher


class LinkedInCloudContracts(unittest.TestCase):
    def test_no_local_publish(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","RUNNER_OS":"Windows","RUNNER_ENVIRONMENT":"self-hosted"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"CLOUD_ONLY"):
                publisher.cloud_only()

    def test_target_pin_and_duration(self):
        row={"target_key":"linkedin:primary","duration_class":"short",
             "payload":{"platform":"linkedin","account_id":"primary",
                        "media_url":"https://anthares.us/clip.mp4","title":"Test","duration_seconds":55}}
        self.assertEqual(publisher.safe_payload(row)["platform"],"linkedin")
        with self.assertRaisesRegex(RuntimeError,"TARGET_INVALID"):
            publisher.safe_payload({**row,"target_key":"linkedin:other"})

    def test_scheduled_not_confirmed(self):
        row={"id":"id1","target_key":"linkedin:primary","duration_class":"short",
             "lease_generation":2,"payload":{"platform":"linkedin","account_id":"primary",
             "media_url":"https://anthares.us/clip.mp4","title":"Test","duration_seconds":55}}
        seen=[]
        def call(action,payload=None):
            seen.append((action,payload))
            if action=="lease":return {"ok":True,"job":row}
            return {"ok":True}
        with patch.object(publisher,"queue",side_effect=call),patch.object(publisher,"schedule",return_value={"status":"SCHEDULED_IN_BUFFER","remote_id":"buffer123"}):
            self.assertEqual(publisher.publish_once(),"SCHEDULED_IN_BUFFER")
        self.assertEqual([x[0] for x in seen],["lease","start","scheduled"])
        self.assertEqual(seen[-1][1]["buffer_post_id"],"buffer123")

    def test_failure_after_start_no_retry(self):
        row={"id":"id1","target_key":"linkedin:primary","duration_class":"short",
             "lease_generation":2,"payload":{"platform":"linkedin","account_id":"primary",
             "media_url":"https://anthares.us/clip.mp4","title":"Test","duration_seconds":55}}
        actions=[]
        def call(action,payload=None):
            actions.append(action)
            return {"ok":True,"job":row} if action=="lease" else {"ok":True}
        with patch.object(publisher,"queue",side_effect=call),patch.object(publisher,"schedule",side_effect=RuntimeError("unknown")):
            with self.assertRaises(RuntimeError):
                publisher.publish_once()
        self.assertEqual(actions,["lease","start","fail"])

    def test_sent_post_validates_channel(self):
        with patch.object(publisher,"api",return_value={"post":{"id":"buffer123","status":"sent","channelId":publisher.LINKEDIN_ID,
                        "schedulingType":"automatic","externalLink":"https://www.linkedin.com/feed/update/urn:li:activity:123"}}):
            self.assertIn("linkedin.com",publisher.verify_sent_post("buffer123"))

    def test_scheduled_post_never_confirmed(self):
        with patch.object(publisher,"api",return_value={"post":{"id":"buffer123","status":"scheduled","channelId":publisher.LINKEDIN_ID,
                        "schedulingType":"automatic","externalLink":None}}):
            self.assertIsNone(publisher.verify_sent_post("buffer123"))

    def test_wrong_channel_not_confirmed(self):
        with patch.object(publisher,"api",return_value={"post":{"id":"buffer123","status":"sent","channelId":"other",
                        "schedulingType":"automatic","externalLink":"https://linkedin.com/feed/update/abc"}}):
            with self.assertRaisesRegex(RuntimeError,"IDENTITY_UNVERIFIED"):
                publisher.verify_sent_post("buffer123")


if __name__=="__main__":
    unittest.main()
