import os
import unittest
from unittest.mock import patch
from social_adapters import linkedin_personal as personal

class LinkedInPersonalContracts(unittest.TestCase):
    def test_local_pc_is_disallowed(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","RUNNER_OS":"Windows"},clear=True):
            with self.assertRaisesRegex(personal.PersonalAuthRequired,"CLOUD_REQUIRED"):
                personal.cloud_only()

    def test_member_requires_individual_oauth(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                                   "RUNNER_OS":"Linux","LINKEDIN_PERSONAL_SUB":"member1"},clear=True):
            with patch.object(personal,"api",return_value={"sub":"another_person"}):
                with self.assertRaisesRegex(personal.PersonalAuthRequired,"ACCOUNT_MISMATCH"):
                    personal.person_identity()

    def test_member_author_is_person_not_company(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                                   "RUNNER_OS":"Linux","LINKEDIN_PERSONAL_SUB":"member1"},clear=True):
            with patch.object(personal,"api",return_value={"sub":"member1"}):
                self.assertEqual(personal.person_identity(),"urn:li:person:member1")

    def test_no_credential_no_post(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                                   "RUNNER_OS":"Linux","LINKEDIN_PERSONAL_COMMIT":"0"},clear=True):
            with patch.object(personal,"api",side_effect=AssertionError("NETWORK")):
                self.assertEqual(personal.create_public_video({})["status"],"DRY_RUN")

    def test_only_own_master_mp4_allowed(self):
        for url in ("http://anthares.us/c.mp4","https://evil.example/c.mp4",
                    "https://anthares.us.evil.com/c.mp4","https://anthares.us/video.mov"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    personal.media_url(url)

    def test_verifies_identity_and_publication(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                                   "RUNNER_OS":"Linux","LINKEDIN_PERSONAL_COMMIT":"1"},clear=True):
            with patch.object(personal,"person_identity",return_value="urn:li:person:abc"):
                with patch.object(personal,"upload_video",return_value="urn:li:video:V123"):
                    request=[]
                    def call(method,url,body=None,**kw):
                        request.append((method,url,body))
                        if method=="POST":
                            return {},{"x-restli-id":"urn:li:ugcPost:12345"}
                        return {"id":"urn:li:ugcPost:12345","author":"urn:li:person:abc",
                                "visibility":"PUBLIC","lifecycleState":"PUBLISHED"}
                    with patch.object(personal,"api",side_effect=call):
                        result=personal.create_public_video({"target_key":"linkedin:personal",
                          "duration_seconds":46,"title":"Aristóteles e a ética",
                          "media_url":"https://anthares.us/c.mp4"})
        self.assertEqual(result["status"],"CONFIRMED")
        self.assertIn("#Filosofia",request[0][2]["commentary"])
        self.assertIn("www.anthares.us",request[0][2]["commentary"])
        self.assertEqual(request[0][2]["author"],"urn:li:person:abc")
        self.assertNotIn("organization",str(request[0][2]))

    def test_uncertain_video_not_claimed_published(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                                   "RUNNER_OS":"Linux","LINKEDIN_PERSONAL_COMMIT":"1"},clear=True):
            with patch.object(personal,"person_identity",return_value="urn:li:person:abc"),patch.object(personal,"upload_video",return_value="urn:li:video:V123"):
                def call(method,url,body=None,**kw):
                    if method=="POST":return {},{"x-restli-id":"urn:li:ugcPost:12345"}
                    return {"id":"urn:li:ugcPost:12345","author":"urn:li:person:abc","visibility":"PUBLIC","lifecycleState":"PROCESSING"}
                with patch.object(personal,"api",side_effect=call):
                    self.assertEqual(personal.create_public_video({"target_key":"linkedin:personal","duration_seconds":46,
                      "title":"Kafka","media_url":"https://anthares.us/c.mp4"})["status"],"UNCERTAIN")

if __name__=="__main__":
    unittest.main()
