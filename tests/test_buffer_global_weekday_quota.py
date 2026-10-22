"""CORTES Buffer: 20 global allocations on five weekdays, independent of network."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class GlobalBufferPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        cls.migration=(ROOT/"db/migrations/20261022_cortes_buffer_global_weekday_slots.sql").read_text(encoding="utf-8")

    def test_exact_global_quota_and_weekday_schema(self):
        self.assertIn("BUFFER_GLOBAL_DAILY=20",self.js)
        self.assertIn("generate_series(1,20)",self.js)
        self.assertIn("cortes_buffer_slot_weekday_check",self.migration)
        self.assertIn("extract(isodow FROM local_day) BETWEEN 1 AND 5",self.migration)
        self.assertIn("PRIMARY KEY(local_day,slot)",self.migration)
        self.assertIn("CHECK(slot BETWEEN 1 AND 20)",self.migration)
        self.assertIn("America/Campo_Grande",self.js)

    def test_same_budget_for_all_channels(self):
        self.assertIn("const BUFFER_LOCAL_DAY=",self.js)
        self.assertIn("INSERT INTO cortes_buffer_daily_slots(local_day,slot,target_key,job_id)",self.js)
        self.assertIn("FROM picked p CROSS JOIN free_slot f",self.js)
        self.assertIn("ON CONFLICT DO NOTHING RETURNING job_id",self.js)
        self.assertIn("FROM reserved r WHERE p.id=r.job_id",self.js)
        self.assertIn("if(Number(weekday[0]?.n||0)>5)",self.js)
        for name in ("linkedin","instagram","pinterest"):
            code=(ROOT/f"tools/cortes_buffer_{name}_cloud.py").read_text(encoding="utf-8")
            self.assertIn('queue("policy")',code)
            self.assertIn("BUFFER_BUDGET_HANDOFF_OWN",code)

    def test_only_prestart_releases_reserved_slot(self):
        section=self.js.split("async function bufferAction(",1)[1]
        fail=section.split("if(verb==='fail'){",1)[1].split("if(verb==='media-missing')",1)[0]
        self.assertIn("if(rows[0]?.status==='queued')",fail)
        self.assertIn("DELETE FROM cortes_buffer_daily_slots",fail)
        missing=section.split("if(verb==='media-missing'){",1)[1].split("if(verb==='scheduled')",1)[0]
        self.assertIn("DELETE FROM cortes_buffer_daily_slots",missing)
        started=section.split("if(verb==='start'){",1)[1].split("if(verb==='fail')",1)[0]
        self.assertNotIn("DELETE FROM cortes_buffer_daily_slots",started)

    def test_old_linkedin_queue_not_stranded_at_midnight(self):
        self.assertIn("WHERE target_key=$1 AND status='queued' ORDER BY created_at,id FOR UPDATE SKIP LOCKED",self.js)
        self.assertIn("const cutoffForBuffer=\"'1970-01-01T00:00:00Z'::timestamptz\";",self.js)
        self.assertIn("ORDER BY created_at,id",self.js)


if __name__=="__main__":
    unittest.main()
