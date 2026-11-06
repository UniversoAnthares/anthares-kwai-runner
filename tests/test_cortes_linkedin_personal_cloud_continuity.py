"""Fail-closed LinkedIn personal continuity without touching real OAuth or Neon."""
import unittest
import io
import json
from contextlib import redirect_stdout
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
    
    def test_temporary_media_failure_releases_fenced_lease_and_reports_preupload(self):
        row={"id":"media-transient","lease_generation":4,"target_key":"linkedin:personal",
             "duration_class":"short","payload":{"platform":"linkedin","account_id":"personal",
             "media_url":"https://anthares.us/clip.mp4","title":"Test","duration_seconds":55}}
        events=[]
        def fakequeue(action,data):
            events.append(action)
            return {"ok":True,"job":row} if action=="lease" else {"ok":True}
        output=io.StringIO()
        with (patch.object(publisher,"cloud_only"),
              patch.object(publisher,"account_preflight"),
              patch.object(publisher,"reconcile_personal",return_value=0),
              patch.object(publisher,"queue",side_effect=fakequeue),
              patch.object(publisher,"media_available",
                           side_effect=RuntimeError("SOURCE_MEDIA_TEMPORARY_UNAVAILABLE")),
              patch.object(publisher,"linkedin",return_value={"status":"READY"}) as service,
              redirect_stdout(output)):
            exitcode=publisher.main()
        self.assertEqual(exitcode,2)
        final=json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(final,{"linkedin_personal":"BLOCKED_BEFORE_UPLOAD",
                                "reason":"SOURCE_MEDIA_TEMPORARY_UNAVAILABLE"})
        self.assertEqual(events,["lease","fail"])
        self.assertNotIn("PERSONAL_STAGE=queue_start",output.getvalue())
        self.assertNotIn("PERSONAL_STAGE=linkedin_upload",output.getvalue())
        self.assertEqual(service.call_count,1)
        self.assertFalse(service.call_args.kwargs["publish"])

    def test_unconfirmed_preupload_release_keeps_uncertainty_classification(self):
        row={"id":"media-unconfirmed","lease_generation":5,"target_key":"linkedin:personal",
             "duration_class":"short","payload":{"platform":"linkedin","account_id":"personal",
             "media_url":"https://anthares.us/clip.mp4","title":"Test","duration_seconds":55}}
        events=[]
        def fakequeue(action,data):
            events.append(action)
            if action=="lease":
                return {"ok":True,"job":row}
            raise RuntimeError("QUEUE_FENCE_UNCONFIRMED")
        output=io.StringIO()
        with (patch.object(publisher,"cloud_only"),
              patch.object(publisher,"account_preflight"),
              patch.object(publisher,"reconcile_personal",return_value=0),
              patch.object(publisher,"queue",side_effect=fakequeue),
              patch.object(publisher,"media_available",
                           side_effect=RuntimeError("SOURCE_MEDIA_TEMPORARY_UNAVAILABLE")),
              patch.object(publisher,"linkedin",return_value={"status":"READY"}) as service,
              redirect_stdout(output)):
            exitcode=publisher.main()
        self.assertEqual(exitcode,3)
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1]),
                         {"linkedin_personal":"BLOCKED_OR_UNCERTAIN","reason":"RuntimeError"})
        self.assertEqual(events,["lease","fail"])
        self.assertEqual(service.call_count,1)
        self.assertFalse(service.call_args.kwargs["publish"])

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
