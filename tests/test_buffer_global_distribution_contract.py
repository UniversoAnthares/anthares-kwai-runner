"""Source candidate windows cannot be mistaken for actual Buffer allocations."""
import unittest
from anthares_publisher.buffer_distribution import (
    BUFFER_GLOBAL_DAILY_LIMIT, BUFFER_GLOBAL_WEEKLY_LIMIT,
    BUFFER_ACTIVE_WEEKDAYS, distribution_per_source
)

class GlobalDistributionContract(unittest.TestCase):
    def test_weekly_capacity_and_weekday_gating(self):
        self.assertEqual(BUFFER_GLOBAL_DAILY_LIMIT,20)
        self.assertEqual(BUFFER_GLOBAL_WEEKLY_LIMIT,100)
        self.assertEqual(BUFFER_ACTIVE_WEEKDAYS,frozenset(range(5)))
        self.assertNotIn(5,BUFFER_ACTIVE_WEEKDAYS)
        self.assertNotIn(6,BUFFER_ACTIVE_WEEKDAYS)

    def test_source_candidates_do_not_reserve_buffer(self):
        d=distribution_per_source("source",[
            {"segment_id":"x:y:10:50"},
            {"segment_id":"x:y:50:90"}
        ])
        self.assertTrue(d["buffer_preference_only"])
        self.assertEqual(d["provider_allocation_authority"],"neon:cortes_buffer_daily_slots")
        self.assertEqual(d["global_buffer_daily_max"],20)
        self.assertEqual(len(d["buffer"]),3)
        self.assertEqual(len(d["buffer"]["linkedin"]),2)

if __name__=="__main__":
    unittest.main()
