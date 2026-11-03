import tempfile
import unittest
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import connect, reserve
from social_adapters.bilibili_browser import canonical_video_url, external_id_from_url, canonical_space_url, publish

class BilibiliBrowserTests(unittest.TestCase):
    def test_video_url(self):
        url=canonical_video_url("https://www.bilibili.com/video/BV1abc234567/?spm_id_from=test")
        self.assertEqual(url,"https://www.bilibili.com/video/BV1abc234567")
        self.assertEqual(external_id_from_url(url),"BV1abc234567")
    def test_reject_foreign_host_and_non_video(self):
        self.assertEqual(canonical_video_url("https://evil.example/video/BV123"),"")
        self.assertEqual(canonical_video_url("https://www.bilibili.com/read/cv123"),"")
    def test_numeric_creator_uid_required(self):
        self.assertEqual(canonical_space_url("12345"),"https://space.bilibili.com/12345/video")
        with self.assertRaises(ValueError): canonical_space_url("some-name")
    def test_contract(self):
        validate_evidence(PublicationEvidence("bilibili","123","BV1abc234567","https://www.bilibili.com/video/BV1abc234567"),"bilibili","123")
        with self.assertRaises(ValueError):
            validate_evidence(PublicationEvidence("bilibili","123","BV1abc234567","https://evil.example/video/BV1abc234567"),"bilibili","123")
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as temp:
            video=Path(temp)/"video.mp4";video.write_bytes(b"synthetic")
            out=publish("bilibili",str(video),"Anthares","12345",str(Path(temp)/"profile"))
            self.assertEqual(out["status"],"DRY_RUN")
            self.assertEqual(out["title"],"Anthares")
    def test_ledger_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            db=connect(str(Path(temp)/"ledger.sqlite3"))
            sha="a"*64
            first=reserve(db,"source",0,1000,"bilibili","123",sha)
            self.assertFalse(first["already_published"])
            with self.assertRaises(ValueError):
                reserve(db,"source",500,1500,"bilibili","123","b"*64)

if __name__=="__main__":unittest.main()
