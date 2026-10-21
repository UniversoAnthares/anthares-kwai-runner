"""Tests for P0 publication incident router without network or issue writes."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

PATH=pathlib.Path(__file__).resolve().parents[1]/"tools"/"cortes_qa_p0_router.py"
SPEC=importlib.util.spec_from_file_location("router",PATH)
router=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router)


class P0RouterTests(unittest.TestCase):
    def test_same_event_has_same_dedupe_key(self):
        self.assertEqual(router.marker("gha","clipper","123"),router.marker("gha","clipper","123"))
        self.assertNotEqual(router.marker("gha","clipper","123"),router.marker("gha","clipper","124"))

    def test_action_failure_creates_incident_from_real_run_id(self):
        run={"workflow_runs":[{
            "name":"CORTES TikTok Neon Producer","conclusion":"failure",
            "created_at":router.NOW.isoformat(),"id":123456
        }]}
        with patch.object(router,"http",return_value=run):
            result=router.workflow_incidents()
        self.assertEqual(len(result),2)
        self.assertEqual(result[0]["network"],"tiktok")
        self.assertTrue(result[0]["evidence"].endswith("123456"))

    def test_pinterest_repeating_board_outage_is_one_p0_per_day(self):
        now=router.NOW.isoformat()
        runs={"workflow_runs":[
            {"name":"CORTES Pinterest - automatic Buffer cloud publisher",
             "conclusion":"failure","created_at":now,"id":39654653406},
            {"name":"CORTES Pinterest - automatic Buffer cloud publisher",
             "conclusion":"failure","created_at":now,"id":39654653407},
        ]}
        with patch.object(router,"http",return_value=runs):
            incidents=router.workflow_incidents()
        self.assertEqual(len(incidents),4)  # both repos scanned
        self.assertEqual(len({x["id"] for x in incidents}),2)
        self.assertTrue(all(x["network"]=="pinterest" for x in incidents))

    def test_action_success_never_creates_ticket(self):
        run={"workflow_runs":[{
            "name":"CORTES TikTok Neon Producer","conclusion":"success",
            "created_at":router.NOW.isoformat(),"id":123456
        }]}
        with patch.object(router,"http",return_value=run):
            self.assertEqual(router.workflow_incidents(),[])

    def test_wordpress_repeated_failing_clips_grouped_and_tokens_hidden(self):
        when=router.NOW.isoformat()
        state={"items":[{"clips":[
            {"networks":{"threads":{"status":"error","updated_at":when,"error":"secret123"}}},
            {"networks":{"threads":{"status":"error","updated_at":when,"error":"secret123"}}},
        ]}],"blocker":None}
        with patch.dict(router.os.environ,{"WP_SITE_URL":"https://anthares.us",
                                               "WP_USERNAME":"fixture",
                                               "WP_APP_PASSWORD":"mock"}), \
             patch.object(router,"http",return_value=state):
            result=router.wp_incidents()
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["network"],"threads")
        self.assertIn("2 affected",result[0]["description"])
        self.assertNotIn("secret123",str(result))

    def test_issue_body_requests_fix_and_no_blind_retries(self):
        events=[]
        def fake(url,method="GET",payload=None,headers=None):
            events.append(payload)
            return {"number":123}
        record={"id":router.marker("event"),"network":"pinterest",
                "stage":"uncertain","evidence":"https://github.com/a/b/actions/runs/3",
                "description":"redacted"}
        with patch.object(router,"http",side_effect=fake):
            router.create_issue(record)
        self.assertIn("P0",events[0]["title"])
        self.assertIn("reconciliar",events[0]["body"])
        self.assertIn("QA-P0-FINGERPRINT",events[0]["body"])


if __name__=="__main__":
    unittest.main()
