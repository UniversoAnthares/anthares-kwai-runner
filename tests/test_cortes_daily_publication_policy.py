"""CORTES max 100 per social network and local day; Buffer isn't a network."""
import pathlib
import unittest
from anthares_publisher.buffer_distribution import (
    CORTES_DAILY_PUBLICATION_LIMIT, BUFFER_LIMIT_PER_SOURCE, TARGETS,
)

ROOT=pathlib.Path(__file__).resolve().parents[1]
MIGRATION=ROOT/"db/migrations/20261021_cortes_daily_publication_limit_100.sql"


class DailyPolicyTests(unittest.TestCase):
    def test_cortes_100_is_per_network_not_per_buffer_channel(self):
        self.assertEqual(CORTES_DAILY_PUBLICATION_LIMIT,100)
        self.assertEqual(set(TARGETS),{"instagram","pinterest","linkedin"})
        self.assertEqual(len(set(TARGETS.values())),3)
        self.assertLess(BUFFER_LIMIT_PER_SOURCE,CORTES_DAILY_PUBLICATION_LIMIT)

    def test_atomic_quota_guard_is_not_a_fanout_cap(self):
        sql=MIGRATION.read_text(encoding="utf-8")
        self.assertIn("CHECK (reserved BETWEEN 0 AND 100)",sql)
        self.assertIn("ON CONFLICT(target_key,local_day)",sql)
        self.assertIn("WHERE public.cortes_daily_publication_budget.reserved<100",sql)
        self.assertIn("CORTES_DAILY_PUBLICATION_LIMIT_100",sql)
        self.assertIn("BEFORE UPDATE OF status",sql)
        self.assertIn("publication_started_at",sql)
        self.assertIn("America/Campo_Grande",sql)
        self.assertNotIn("DROP TABLE",sql)
        self.assertNotIn("DELETE FROM",sql)

    def test_each_network_has_separate_persistent_count(self):
        sql=MIGRATION.read_text(encoding="utf-8")
        for target in ("kwai:lucasrosalem","linkedin:primary","instagram:universoanthares","pinterest:lucasyahn"):
            self.assertIn(target,sql)
        self.assertIn("PRIMARY KEY (target_key, local_day)",sql)


if __name__=="__main__":
    unittest.main()
