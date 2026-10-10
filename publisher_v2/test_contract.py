#!/usr/bin/env python3
import dataclasses,hashlib,time,unittest
from control import Evidence,Phase,transition,valid_identity,valid_publication

class ContractTests(unittest.TestCase):
 def setUp(self):
  self.now=1760000000
  self.e=Evidence("lucasrosalem",self.now,"authenticated_provider_profile",
   "https://www.kwai.com/@lucasrosalem","https://www.kwai.com/short-video/123",
   "lease-1",hashlib.sha256(b"unique-video").hexdigest())
 def test_01_unverified_blocks(self):self.assertEqual(transition(Phase.DISCOVER,"identity_observed"),Phase.AUTH_REQUIRED)
 def test_02_valid_identity(self):self.assertTrue(valid_identity(self.e,self.now))
 def test_03_wrong_account(self):self.assertFalse(valid_identity(dataclasses.replace(self.e,account="other"),self.now))
 def test_04_untrusted_source(self):self.assertFalse(valid_identity(dataclasses.replace(self.e,source="environment_variable"),self.now))
 def test_05_stale(self):self.assertFalse(valid_identity(self.e,self.now+301))
 def test_06_future(self):self.assertFalse(valid_identity(self.e,self.now-1))
 def test_07_missing_profile(self):self.assertFalse(valid_identity(dataclasses.replace(self.e,profile_url=""),self.now))
 def test_08_identity_transition(self):self.assertEqual(transition(Phase.DISCOVER,"identity_observed",self.e,self.now),Phase.AUTH_VERIFIED)
 def test_09_claim_before_identity(self):self.assertEqual(transition(Phase.AUTH_REQUIRED,"lease_claimed",self.e),Phase.BLOCKED)
 def test_10_claim_after_identity(self):self.assertEqual(transition(Phase.AUTH_VERIFIED,"lease_claimed",self.e),Phase.CLAIMED)
 def test_11_claim_without_lease(self):self.assertEqual(transition(Phase.AUTH_VERIFIED,"lease_claimed",dataclasses.replace(self.e,lease_id="")),Phase.BLOCKED)
 def test_12_publish_without_claim(self):self.assertEqual(transition(Phase.AUTH_VERIFIED,"provider_posted",self.e),Phase.BLOCKED)
 def test_13_publish_with_claim(self):self.assertEqual(transition(Phase.CLAIMED,"provider_posted",self.e),Phase.PUBLISHED)
 def test_14_verify_before_publish(self):self.assertEqual(transition(Phase.CLAIMED,"public_url_verified",self.e),Phase.BLOCKED)
 def test_15_verify_after_publish(self):self.assertEqual(transition(Phase.PUBLISHED,"public_url_verified",self.e),Phase.VERIFIED)
 def test_16_https_required(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,video_url="http://kwai.com/video")))
 def test_17_domain_required(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,video_url="https://evil.example/kwai.com/123")))
 def test_18_no_userinfo_bypass(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,video_url="https://kwai.com@evil.example/123")))
 def test_19_no_empty_path(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,video_url="https://kwai.com/")))
 def test_20_no_lease(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,lease_id="")))
 def test_21_no_digest(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,content_digest="")))
 def test_22_digest_length(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,content_digest="a"*63)))
 def test_23_digest_hex(self):self.assertFalse(valid_publication(dataclasses.replace(self.e,content_digest="g"*64)))
 def test_24_valid_publication(self):self.assertTrue(valid_publication(self.e))
 def test_25_missing_evidence(self):self.assertEqual(transition(Phase.CLAIMED,"provider_posted"),Phase.BLOCKED)
 def test_26_wrong_event(self):self.assertEqual(transition(Phase.DISCOVER,"unknown",self.e),Phase.BLOCKED)
 def test_27_double_claim(self):self.assertEqual(transition(Phase.CLAIMED,"lease_claimed",self.e),Phase.BLOCKED)
 def test_28_double_publish(self):self.assertEqual(transition(Phase.PUBLISHED,"provider_posted",self.e),Phase.BLOCKED)
 def test_29_verified_terminal(self):self.assertEqual(transition(Phase.VERIFIED,"provider_posted",self.e),Phase.BLOCKED)
 def test_30_no_claim_on_bad_identity(self):self.assertEqual(transition(Phase.AUTH_REQUIRED,"identity_observed",dataclasses.replace(self.e,account="other"),self.now),Phase.AUTH_REQUIRED)

if __name__=="__main__":unittest.main()
