import unittest

from anthares_publisher.media_model import Clip,Publication,Source,source_safe_to_delete

class MediaModelTests(unittest.TestCase):
    def test_source_and_clip_identity_are_stable(self):
        Source("live-1",source_sha256="0"*64)
        a=Clip("live-1",0,60000,"short","1"*64,master_id="short-master-A")
        b=Clip("live-1",0,60000,"short","1"*64,master_id="short-master-A")
        self.assertEqual(a.clip_id,b.clip_id)

    def test_duration_policy_is_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"30-90"):
            Clip("live-1",0,29000,"short","a"*64)
        with self.assertRaisesRegex(ValueError,"5-14"):
            Clip("live-1",0,299000,"long","b"*64)

    def test_destination_identity_is_platform_plus_account(self):
        clip=Clip("live-1",0,60000,"short","1"*64,master_id="short-master-B")
        a=Publication(clip,"kwai","@primary")
        b=Publication(clip,"kwai","secondary")
        c=Publication(clip,"tiktok","primary")
        self.assertNotEqual(a.publication_id,b.publication_id)
        self.assertNotEqual(a.publication_id,c.publication_id)
        self.assertEqual(a.target_key,"kwai:primary")
        self.assertEqual(a.daily_limit,100)

    def test_master_class_mismatch_is_rejected(self):
        short=Clip("live-1",0,60000,"short","1"*64)
        long=Clip("live-1",0,600000,"long","2"*64)
        with self.assertRaisesRegex(ValueError,"long-form"):
            Publication(short,"youtube","channel-a")
        with self.assertRaisesRegex(ValueError,"short-form"):
            Publication(long,"tiktok","account-a")

    def test_control_payload_carries_canonical_dedupe_and_target_fields(self):
        clip=Clip("live-1",1000,61000,"short","3"*64,master_id="master-C")
        p=Publication(clip,"kwai","primary")
        body=p.control_payload()
        self.assertEqual(body["id"],p.publication_id)
        self.assertEqual(body["account_id"],"primary")
        self.assertEqual(body["target_key"],"kwai:primary")
        self.assertEqual(body["dedupe_key"],p.dedupe_key)
        self.assertEqual((body["source_start"],body["source_end"]),(1000,61000))
        self.assertEqual(body["media_sha256"],"3"*64)

    def test_source_retention_requires_all_planned_publications_confirmed(self):
        self.assertFalse(source_safe_to_delete(False,["confirmed"]))
        self.assertFalse(source_safe_to_delete(True,[]))
        self.assertFalse(source_safe_to_delete(True,["confirmed","uncertain"]))
        self.assertTrue(source_safe_to_delete(True,["confirmed","confirmed"]))

if __name__=="__main__": unittest.main()
