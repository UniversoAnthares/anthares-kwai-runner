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

    def test_no_cloud_credentials_fails_without_queue_call(self):
        with patch.dict(p.os.environ,{"GITHUB_ACTIONS":"false","BUFFER_API_KEY":""}):
            with self.assertRaisesRegex(RuntimeError,"CLOUD_ONLY"):
                p.cloud_only()


if __name__=="__main__":
    unittest.main()
