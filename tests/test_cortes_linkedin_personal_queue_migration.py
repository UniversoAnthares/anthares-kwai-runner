import unittest
from pathlib import Path

class LinkedInPersonalQueueMigrationTests(unittest.TestCase):
    def test_personal_and_company_have_disjoint_queue_identifiers(self):
        sql=(Path(__file__).resolve().parents[1]/
             "db/migrations/20261021_cortes_linkedin_personal_queue_staged.sql").read_text()
        self.assertIn("('linkedin'::text,'linkedin:primary'::text,'primary'::text)",sql)
        self.assertIn("('linkedin'::text,'linkedin:personal'::text,'personal'::text)",sql)
        self.assertIn("destination.target_key","\n"+sql)
        self.assertIn("ON CONFLICT DO NOTHING",sql)
        self.assertIn("EXCEPTION WHEN OTHERS",sql)
        self.assertNotIn("DELETE FROM public.cortes_publications",sql)
        self.assertNotIn("TRUNCATE",sql)

if __name__=="__main__":
    unittest.main()
