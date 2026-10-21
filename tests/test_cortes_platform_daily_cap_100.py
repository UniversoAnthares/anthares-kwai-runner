"""Contract checks for the global CORTES platform quota migration."""
from pathlib import Path
import unittest

MIGRATION = Path(__file__).resolve().parents[1] / "db" / "migrations" / "20261021_cortes_platform_daily_cap_100.sql"

class PlatformCapContract(unittest.TestCase):
    def test_atomic_ceiling(self):
        source = MIGRATION.read_text(encoding="utf-8")
        for token in (
            "cortes_platform_daily_cap_100",
            "CORTES_PLATFORM_DAILY_LIMIT_100",
            "WHERE public.cortes_daily_publication_budget.reserved<100",
            "BEFORE INSERT OR UPDATE OF status,publication_started_at",
            "cortes_tiktok_publications",
            "cortes_publications",
            "AT TIME ZONE 'America/Campo_Grande'",
            "DATE '2026-10-21',100",
            "ON CONFLICT",
            "OLD.publication_started_at IS NULL",
            "GREATEST(public.cortes_daily_publication_budget.reserved",
        ):
            self.assertIn(token,source)
    def test_non_destructive(self):
        source = MIGRATION.read_text(encoding="utf-8").upper()
        for forbidden in ("DROP TABLE","DELETE FROM","TRUNCATE","DROP TRIGGER","ALTER TABLE"):
            self.assertNotIn(forbidden,source)

if __name__ == "__main__":
    unittest.main()
