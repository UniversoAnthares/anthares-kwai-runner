"""Contract tests for exact public-profile/Graph matching and safe non-coverage."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from tools import cortes_instagram_public_reconcile as r


class PublicProfileReconciliationTests(unittest.TestCase):
    def setUp(self):
        # Simulate a mature tagged cohort without waiting 36 hours in CI.
        cutover = patch.object(r,"TAG_CUTOVER",datetime(2026,1,1,tzinfo=timezone.utc))
        cutover.start()
        self.addCleanup(cutover.stop)
        self.started = datetime.now(timezone.utc) - timedelta(days=2)
        self.id = "cortes-fanout-instagram-" + "a" * 32
        self.tag = r.tag_for(self.id)
        self.url = "https://www.instagram.com/reel/Abc123XYZ/"
        def item(ts, caption="", url=None):
            return {"timestamp": ts.isoformat(), "caption": caption,
                    "permalink": url or self.url}
        self.public = {
            "complete": True,
            "count": 3,
            "oldest_at": (self.started - timedelta(hours=2)).isoformat(),
            "newest_at": (self.started + timedelta(hours=2)).isoformat(),
            "items": [item(self.started + timedelta(hours=2)),
                      item(self.started, self.tag + " texto"),
                      item(self.started - timedelta(hours=2))],
        }
        self.graph = {
            "complete": True, "count": 3,
            "oldest_at": self.public["oldest_at"],
            "items": [{**item(self.started + timedelta(hours=2)), "id":"1234567890"},
                      {**item(self.started, self.tag + " texto"), "id":"1234567891"},
                      {**item(self.started - timedelta(hours=2)), "id":"1234567892"}],
        }
        self.job = {"id": self.id, "publication_started_at":self.started.isoformat()}

    def test_confirm_only_same_public_permalink_and_graph_id(self):
        a=r.decide(self.job,self.public,self.graph)
        self.assertEqual(a["decision"],"visible")
        self.assertEqual(a["media_id"],"1234567891")
        self.assertEqual(a["proof"]["matched_permalink"],self.url)
        self.assertEqual(a["proof"]["scanned_count"],3)

    def test_absent_only_after_both_complete_windows(self):
        for x in self.public["items"]:
            x["caption"]="outro corte"
        for x in self.graph["items"]:
            x["caption"]="outro corte"
        a=r.decide(self.job,self.public,self.graph)
        self.assertEqual(a["decision"],"absent")
        self.assertFalse(a["proof"]["matching_caption_tag"])
        self.graph["complete"]=False
        self.assertIsNone(r.decide(self.job,self.public,self.graph))

    def test_login_wall_cannot_assert_failure(self):
        self.public["complete"]=False
        self.public["reason"]="PUBLIC_PROFILE_ACCESS_GATE"
        self.assertIsNone(r.decide(self.job,self.public,self.graph))

    def test_untagged_historical_clips_are_not_replayed_or_failed(self):
        old=dict(self.job,publication_started_at="2026-10-29T12:00:00+00:00")
        with patch.object(r,"TAG_CUTOVER",datetime(2026,11,12,13,tzinfo=timezone.utc)):
            self.assertIsNone(r.decide(old,self.public,self.graph))

    def test_conflicting_graph_match_blocks_result(self):
        self.graph["items"][1]["permalink"]="https://www.instagram.com/reel/Other/"
        self.assertIsNone(r.decide(self.job,self.public,self.graph))

    def test_uncovered_older_window_rejects_coverage(self):
        self.public["items"]=self.public["items"][:2]
        result=r.cover(self.started,self.public["items"])
        self.assertFalse(result[0])

    def test_reject_invalid_shortcode_or_job_tag(self):
        self.assertIsNone(r.clean_permalink("https://evil.example/reel/X/"))
        with self.assertRaises(ValueError):
            r.tag_for("an-untrusted-job")


if __name__ == "__main__":
    unittest.main()
