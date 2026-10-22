import json
import tempfile
import unittest
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch

from tools import x_long_schedule as schedule
from tools import x_local_longform_producer as origin
from tools import x_cloud_qa_watchdog as qa

class XFixedLongSlotsAndQaTests(unittest.TestCase):
    def test_same_fixed_youtube_clocks_in_campo_grande(self):
        slots=schedule.slots(date(2026,10,22))
        self.assertEqual([x.strftime("%H:%M") for x in slots],
                         ["05:30","14:00","19:00","22:00"])
        self.assertEqual([x.tzinfo for x in slots],[schedule.TZ]*4)

    def test_not_due_video_does_not_publish_early(self):
        d=date(2026,10,22)
        noon=datetime(2026,10,22,12,tzinfo=schedule.TZ)
        self.assertTrue(schedule.eligible_time(schedule.planned_for(d,0).isoformat(),noon))
        self.assertFalse(schedule.eligible_time(schedule.planned_for(d,1).isoformat(),noon))
        self.assertFalse(schedule.eligible_time(""))
        self.assertFalse(schedule.eligible_time("not-a-timestamp"))
        self.assertFalse(schedule.eligible_time("2026-10-22T05:30:00"))

    def test_strict_four_masters_per_day(self):
        with self.assertRaises(ValueError):
            schedule.planned_for(date(2026,10,22),4)

    def test_live_lock_from_last_queued_source(self):
        from datetime import datetime
        today=date(2026,10,22)
        prefix=chr(96)*3+"json\n"
        suffix="\n"+chr(96)*3
        row={"number":522,"created_at":"2026-10-22T10:30:00Z",
             "body":prefix+json.dumps({"source_id":"a4w8KAOxANc"})+suffix}
        env,held=origin.source_cursor([row],today=today)
        self.assertEqual(env,{"X_DAILY_LIVE_LOCK":"a4w8KAOxANc"})
        self.assertEqual(held,"a4w8KAOxANc")
        next_env,_=origin.source_cursor([row],today=date(2026,10,23))
        self.assertEqual(next_env,{"X_LIVE_CURSOR_AFTER":"a4w8KAOxANc"})

    def test_qa_incident_survives_network_outage_and_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as td,patch.object(qa,"OUTBOX",Path(td)):
            first=qa.persist("X_CLOUD_RUN_FAIL","codeberg","run-1")
            second=qa.persist("X_CLOUD_RUN_FAIL","codeberg","run-1")
            self.assertIsNotNone(first)
            self.assertIsNone(second)
            self.assertFalse(json.loads(first.read_text())["reconciled"])
            with patch.object(qa,"shell",side_effect=[RuntimeError("offline")]):
                qa.flush()
            self.assertFalse(json.loads(first.read_text())["reconciled"])
            with patch.object(qa,"shell",return_value="") as remote:
                qa.flush()
            self.assertTrue(json.loads(first.read_text())["reconciled"])
            self.assertGreaterEqual(remote.call_count,1)

    def test_northflank_health_missing_ledger_field_is_not_db_failure(self):
        with tempfile.TemporaryDirectory() as td,patch.object(qa,"OUTBOX",Path(td)):
            with patch.object(qa,"http",return_value={
                "ok":True,"backend":"local_playwright_vault",
                "browser_ready":False,"vault_ready":True}):
                qa.check_cloud_service()
            files=list(Path(td).glob("*.json"))
            self.assertEqual(len(files),1)
            self.assertEqual(json.loads(files[0].read_text())["code"],
                             "X_NORTHFLANK_BROWSER_NOT_READY")

    def test_codeberg_and_github_failure_reports_to_outbox(self):
        with tempfile.TemporaryDirectory() as td,patch.object(qa,"OUTBOX",Path(td)):
            with patch.object(qa,"http",return_value={"workflow_runs":[
                 {"workflow_id":"x-codeberg-primary.yml","status":"failure",
                  "id":123,"event":"schedule"}]}):
                qa.check_codeberg()
            self.assertEqual(len(list(Path(td).glob("*.json"))),1)
            self.assertIn("X_CODEBERG_PUBLISHER_FAILED",
                          list(Path(td).glob("*.json"))[0].read_text())

if __name__=="__main__":
    unittest.main()
