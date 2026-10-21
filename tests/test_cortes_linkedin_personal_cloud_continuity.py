"""Fail-closed LinkedIn personal continuity without touching real OAuth or Neon."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tools import cortes_linkedin_personal_cloud as publisher


class LinkedInPersonalContinuityTests(unittest.TestCase):
    def test_missing_media_skipped_without_start(self):
        one={"id":"missing","lease_generation":2,"target_key":"linkedin:personal",
             "duration_class":"short","payload":{"platform":"linkedin","account_id":"personal",
             "media_url":"https://anthares.us/missing.mp4","title":"Sample","duration_seconds":55}}
        events=[]
        def fakequeue(action,data):
            events.append(action)
            return {"ok":True,"job":one} if action=="lease" else {"ok":True}
        with (patch.object(publisher,"cloud_only"),
              patch.object(publisher,"account_preflight"),
              patch.object(publisher,"queue",side_effect=fakequeue),
              patch.object(publisher,"media_available",return_value=False),
              patch.object(publisher,"linkedin",return_value={"status":"READY"}) as provider):
            result=publisher.publish_one(skipped=10)
        self.assertEqual(result["linkedin_personal"],"SOURCE_MEDIA_MISSING_FOR_REPAIR")
        self.assertEqual(events,["lease","media-missing"])
        provider.assert_called_once()
    
    def test_one_unverified_post_does_not_repost_same_job(self):
        ids=["cut-A","cut-B"]
        events=[]
        def fakequeue(action,data):
            events.append((action,data.get("id")))
            if action=="lease":
                job_id=ids.pop(0)
                return {"ok":True,"job":{"id":job_id,"target_key":"linkedin:personal",
                   "duration_class":"short","lease_generation":3,
                   "payload":{"platform":"linkedin","account_id":"personal",
                   "media_url":"https://anthares.us/a.mp4","title":"Test","duration_seconds":44}}}
            return {"ok":True}
        def fakepost(payload,publish=False):
            return ({"status":"ACCEPTED_UNVERIFIED","remote_id":"urn:li:share:12345678901234567"}
                    if publish else {"status":"READY"})
        with (patch.object(publisher,"cloud_only"),patch.object(publisher,"account_preflight"),
              patch.object(publisher,"queue",side_effect=fakequeue),
              patch.object(publisher,"media_available",return_value=True),
              patch.object(publisher,"linkedin",side_effect=fakepost)):
            first=publisher.publish_one()
            second=publisher.publish_one()
        self.assertEqual(first["linkedin_personal"],"LINKEDIN_ACCEPTED_PENDING_PUBLIC_PROOF")
        self.assertEqual(second["linkedin_personal"],"LINKEDIN_ACCEPTED_PENDING_PUBLIC_PROOF")
        self.assertEqual([event for event in events if event[0]=="accepted"],
                         [("accepted","cut-A"),("accepted","cut-B")])

    def test_neon_lease_does_not_globally_freeze_on_uncertain(self):
        function=(Path(__file__).resolve().parents[1]/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        segment=function.split("async function personalAction(verb,b){",1)[1].split("if(!['start'",1)[0]
        self.assertNotIn("if(Number(unsettled[0]?.n||0)>0)",segment)
        self.assertIn("status='queued'",segment)

if __name__=="__main__":
    unittest.main()
