"""Independent Codeberg P0 monitor detects real Neon zero-master and GitHub stalls."""
import datetime as dt
import unittest
from unittest.mock import patch
from tools import cortes_codeberg_round_qa as m

NOW=dt.datetime(2026,10,22,13,0,tzinfo=dt.timezone.utc)

class RoundAndPublisher(unittest.TestCase):
    def test_zero_masters_trigger_p0_independent_from_github_actions(self):
        def fake(url,*args,**kwargs):
            if "round-health" in url:
                return {"ok":True,"round_timezone":"America/Campo_Grande","today_master_count":0}
            return {"workflow_runs":[{"conclusion":"success","created_at":NOW.isoformat()}]}
        events=m.scan(NOW,fake)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["stage"],"producer_zero_masters_urgent")

    def test_neon_generated_and_runners_healthy(self):
        def fake(url,*args,**kwargs):
            if "round-health" in url:
                return {"ok":True,"round_timezone":"America/Campo_Grande","today_master_count":10}
            return {"workflow_runs":[{"conclusion":"success","created_at":NOW.isoformat()}]}
        self.assertEqual(m.scan(NOW,fake),[])

    def test_stalled_cloud_and_health_failure_reported(self):
        old=(NOW-dt.timedelta(minutes=48)).isoformat()
        def fake(url,*args,**kwargs):
            if "round-health" in url:raise OSError("offline")
            return {"workflow_runs":[{"status":"queued","created_at":old}]}
        alerts=m.scan(NOW,fake)
        stages={x["stage"] for x in alerts}
        self.assertIn("producer_neon_health_unavailable",stages)
        self.assertIn("hosted_runner_stalled_over_23min",stages)
        self.assertIn("cloud_primary_heartbeat_lost",stages)

    def test_no_false_pre_morning_p0(self):
        midnight=dt.datetime(2026,10,22,7,0,tzinfo=dt.timezone.utc)
        def fail(url,*args,**kwargs):raise AssertionError("should never run")
        self.assertEqual(m.scan(midnight,fail),[])

    def test_issue_report_has_qa_procedure_and_no_credential(self):
        item=m.incident("linkedin/personal-primary","hosted_runner_stalled_over_23min","https://github.com/a/b")
        writes=[]
        def fake(url,token=None,method="GET",payload=None):
            if method=="GET":return []
            writes.append(payload)
            return {"number":765}
        with patch.dict(m.os.environ,{"FORGEJO_TOKEN":"mock","FORGEJO_REPOSITORY":m.REPO}),patch.object(m,"fetch",side_effect=fake):
            self.assertEqual(m.report_events([item]),1)
        self.assertIn("issues/645",writes[0]["body"])
        self.assertIn("never resend uncertain videos",writes[0]["body"])
        self.assertNotIn("mock",str(writes))

if __name__=="__main__":unittest.main()
