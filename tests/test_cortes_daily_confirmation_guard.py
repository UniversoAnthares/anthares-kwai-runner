import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SQL=ROOT/"db/migrations/20261021_cortes_confirmed_daily_quota_guard.sql"


class ConfirmedQuotaTests(unittest.TestCase):
    def test_no_direct_confirmation_bypass(self):
        text=SQL.read_text(encoding="utf-8")
        for needle in ("BEFORE INSERT ON public.cortes_publications",
                       "BEFORE UPDATE OF status ON public.cortes_publications",
                       "NEW.status='confirmed'",
                       "publication_started_at IS NOT NULL",
                       "CORTES_DAILY_PUBLICATION_LIMIT_100",
                       "WHERE public.cortes_daily_publication_budget.reserved<100"):
            self.assertIn(needle,text)
        self.assertNotIn("DROP TABLE",text)
        self.assertNotIn("DELETE FROM",text)

    def test_quota_per_account_and_local_day(self):
        text=SQL.read_text(encoding="utf-8")
        self.assertIn("ON CONFLICT(target_key,local_day)",text)
        self.assertIn("America/Campo_Grande",text)
        for network in ("kwai:lucasrosalem","linkedin:primary",
                        "instagram:universoanthares","pinterest:lucasyahn"):
            self.assertIn(network,text)


if __name__=="__main__":
    unittest.main()
