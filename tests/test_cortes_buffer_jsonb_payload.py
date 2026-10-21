"""Regression: Neon Functions can return a JSONB payload as serialized text."""
import json
import unittest
from tools import cortes_buffer_instagram_cloud as instagram
from tools import cortes_buffer_pinterest_cloud as pinterest
from tools import cortes_buffer_linkedin_cloud as linkedin

class JsonbPayloadTests(unittest.TestCase):
    def test_jsonb_text_accepted_by_three_consumers(self):
        accounts=[(instagram,"instagram:universoanthares","instagram","universoanthares"),
                  (pinterest,"pinterest:lucasyahn","pinterest","lucasyahn"),
                  (linkedin,"linkedin:primary","linkedin","primary")]
        for worker,target,platform,account in accounts:
            with self.subTest(platform=platform):
                row={"target_key":target,"duration_class":"short","payload":json.dumps({
                     "platform":platform,"account_id":account,
                     "duration_seconds":42,"title":"Corte",
                     "media_url":"https://anthares.us/test.mp4"})}
                payload=worker.safe_payload(row)
                self.assertEqual(payload["platform"],platform)
    def test_invalid_json_stops_before_publication(self):
        row={"target_key":"pinterest:lucasyahn","duration_class":"short",
             "payload":"{corrompido"}
        with self.assertRaisesRegex(RuntimeError,"INVALID_JSON"):
            pinterest.safe_payload(row)

if __name__=="__main__":
    unittest.main()
