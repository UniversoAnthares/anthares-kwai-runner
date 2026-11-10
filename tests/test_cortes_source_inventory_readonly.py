import unittest
from tools.cortes_source_inventory_readonly import audit

class SourceInventoryAuditTests(unittest.TestCase):
    def state(self):
        return {"items":[
            {"video_id":"alpha","source_kind":"live","stage":"queued",
             "phases":{"short":{"analyzed":True}},"clips":[{"type":"short"}],
             "chronological_index":3},
            {"video_id":"beta","source_kind":"live","stage":"completed"},
            {"video_id":"gamma","source_kind":"live","legacy_completed":True},
            {"video_id":"regular","source_kind":"regular_video"}],
            "blocker":{"video_id":"alpha","stage":"publishing"}}

    def test_only_active_missing_reported(self):
        r=audit(self.state(),["beta","gamma"])
        self.assertEqual(r["active_missing_count"],1)
        self.assertEqual(r["active_missing"][0]["video_id"],"alpha")
        self.assertTrue(r["active_missing"][0]["short_analyzed"])
        self.assertEqual(r["writes"],0)

    def test_all_verified(self):
        r=audit(self.state(),["alpha","beta","gamma"])
        self.assertEqual(r["active_missing_count"],0)
        self.assertEqual(r["blocker_id"],"alpha")
        self.assertEqual(r["locked_source"]["video_id"],"alpha")
        self.assertEqual(r["locked_source"]["registry_stage"],"queued")
        self.assertEqual(r["locked_source"]["registry_clips"],1)

if __name__=="__main__":
    unittest.main()
