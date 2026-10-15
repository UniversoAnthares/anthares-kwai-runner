import tempfile
import unittest
from pathlib import Path

from anthares_publisher.media_model import (
    connect,register_source,register_clip,reserve_publication,start_publication,
    mark_pre_submit_failure,mark_uncertain,confirm_publication,
    mark_source_processing_complete,source_safe_to_delete,target_state,
)


class MediaModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=connect(str(Path(self.tmp.name)/"media.sqlite3"))
        register_source(self.db,"live-1","https://example.invalid/live-1","0"*64)

    def tearDown(self):
        self.db.close();self.tmp.cleanup()

    def short_clip(self,sha="1"*64,master=None):
        return register_clip(self.db,"live-1",0,60000,"short",sha,master_id=master)

    def long_clip(self,sha="2"*64,master=None):
        return register_clip(self.db,"live-1",0,600000,"long",sha,master_id=master)

    def test_duration_policy_is_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"30-90"):
            register_clip(self.db,"live-1",0,29000,"short","a"*64)
        with self.assertRaisesRegex(ValueError,"5-14"):
            register_clip(self.db,"live-1",0,299000,"long","b"*64)

    def test_one_master_is_reused_but_destinations_are_independent(self):
        clip=self.short_clip(master="short-master-A")
        kwai=reserve_publication(self.db,clip,"kwai","account-a")
        tiktok=reserve_publication(self.db,clip,"tiktok","account-a")
        kwai2=reserve_publication(self.db,clip,"kwai","account-b")
        self.assertNotEqual(kwai["id"],tiktok["id"])
        self.assertNotEqual(kwai["id"],kwai2["id"])
        self.assertEqual(reserve_publication(self.db,clip,"kwai","account-a")["id"],kwai["id"])

    def test_failure_on_one_target_never_mutates_another(self):
        clip=self.short_clip(master="short-master-B")
        a=reserve_publication(self.db,clip,"kwai","account-a")
        b=reserve_publication(self.db,clip,"tiktok","account-a")
        self.assertTrue(start_publication(self.db,a["id"]))
        self.assertTrue(mark_uncertain(self.db,a["id"],"submit outcome unknown"))
        self.assertEqual(target_state(self.db,"kwai","account-a")[0]["status"],"uncertain")
        self.assertEqual(target_state(self.db,"tiktok","account-a")[0]["status"],"queued")
        self.assertFalse(start_publication(self.db,a["id"]))
        self.assertTrue(start_publication(self.db,b["id"]))

    def test_pre_submit_failure_is_retryable_without_affecting_dedupe(self):
        clip=self.short_clip(master="short-master-C")
        p=reserve_publication(self.db,clip,"kwai","account-a")
        self.assertTrue(start_publication(self.db,p["id"]))
        self.assertTrue(mark_pre_submit_failure(self.db,p["id"],"no request sent"))
        self.assertTrue(start_publication(self.db,p["id"]))
        self.assertEqual(reserve_publication(self.db,clip,"kwai","account-a")["id"],p["id"])

    def test_platform_class_mismatch_is_rejected(self):
        short=self.short_clip(master="short-master-D")
        long=self.long_clip(master="long-master-D")
        with self.assertRaisesRegex(ValueError,"long-form"):
            reserve_publication(self.db,short,"youtube","channel-a")
        with self.assertRaisesRegex(ValueError,"short-form"):
            reserve_publication(self.db,long,"tiktok","account-a")

    def test_source_is_retained_until_every_planned_publication_is_confirmed(self):
        clip=self.short_clip(master="short-master-E")
        a=reserve_publication(self.db,clip,"kwai","account-a")
        b=reserve_publication(self.db,clip,"tiktok","account-a")
        self.assertTrue(mark_source_processing_complete(self.db,"live-1"))
        self.assertFalse(source_safe_to_delete(self.db,"live-1"))
        self.assertTrue(start_publication(self.db,a["id"]))
        self.assertTrue(confirm_publication(self.db,a["id"],"kwai-123","https://www.kwai.com/v/kwai-123"))
        self.assertFalse(source_safe_to_delete(self.db,"live-1"))
        self.assertTrue(start_publication(self.db,b["id"]))
        self.assertTrue(confirm_publication(self.db,b["id"],"tt-456","https://www.tiktok.com/@account-a/video/456"))
        self.assertTrue(source_safe_to_delete(self.db,"live-1"))

    def test_uncertain_publication_blocks_source_deletion(self):
        clip=self.short_clip(master="short-master-F")
        p=reserve_publication(self.db,clip,"kwai","account-a")
        mark_source_processing_complete(self.db,"live-1")
        start_publication(self.db,p["id"]);mark_uncertain(self.db,p["id"],"unknown")
        self.assertFalse(source_safe_to_delete(self.db,"live-1"))
        self.assertTrue(confirm_publication(self.db,p["id"],"kwai-789"))
        self.assertTrue(source_safe_to_delete(self.db,"live-1"))


if __name__=="__main__": unittest.main()
