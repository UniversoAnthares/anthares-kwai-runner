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
    def test_codeberg_priority_incidents_bridge_to_tiktok_with_stable_ids(self):
        rows=[
          {"number":13,"title":"[QA P0][lucasrosalem4][500ffd1fc0c93187] github_visibility_lost","state":"open"},
          {"number":12,"title":"[QA P0][universo.anthares][ed1d110d6c4a1a6c] github_visibility_lost","state":"open"},
          {"number":11,"title":"[QA P0][linkedin/personal-primary][f66cff08b1ca52a0] hosted_runner_stalled_over_23min","state":"open"},
        ]
        with patch.object(router,"http",return_value=rows) as api:
            items=router.codeberg_incidents()
        self.assertEqual(len(items),3)
        self.assertEqual([i["network"] for i in items],["tiktok","tiktok","linkedin"])
        self.assertTrue(items[0]["evidence"].endswith("/issues/13"))
        self.assertEqual(items[0]["id"],router.marker("codeberg-qa-p0",13,"500ffd1fc0c93187"))
        self.assertIn("state=open",api.call_args.args[0])

    def test_codeberg_bridge_rejects_untrusted_titles_and_closed_items(self):
        rows=[
          {"number":2,"title":"[QA P0][lucasrosalem4][0000000000000000] github_visibility_lost","state":"closed"},
          {"number":3,"title":"[QA P0][lucasrosalem4][BAD] python_exploit","state":"open"},
          {"number":"4","title":"[QA P0][lucasrosalem4][1111111111111111] github_visibility_lost","state":"open"},
          {"number":5,"title":"unrelated user content","state":"open"},
          {"number":6,"title":"[QA P0][lucasrosalem4][1111111111111111] github_visibility_lost","state":"open"},
        ]
        with patch.object(router,"http",return_value=rows):
            items=router.codeberg_incidents()
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]["network"],"tiktok")
        self.assertTrue(items[0]["evidence"].endswith("/issues/6"))

    def test_codeberg_bridge_fails_closed_on_invalid_api_body(self):
        with patch.object(router,"http",return_value={"issues":"invalid"}):
            with self.assertRaisesRegex(RuntimeError,"CODEBERG_P0_ISSUES_INVALID"):
                router.codeberg_incidents()

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
        self.assertEqual(len(incidents),2)  # one fingerprint per repository/day
        self.assertEqual(len({x["id"] for x in incidents}),2)
        self.assertTrue(all(x["network"]=="pinterest" for x in incidents))

    def test_inaccessible_secondary_repository_keeps_pinterest_alert(self):
        data={"workflow_runs":[{"name":"CORTES Pinterest - automatic Buffer cloud publisher",
             "conclusion":"failure","created_at":router.NOW.isoformat(),"id":39657013484}]}
        def read(url,*args,**kwargs):
            if "anthares-clipper" in url:
                raise router.urllib.error.HTTPError(url,403,"Forbidden",{},None)
            return data
        with patch.object(router,"http",side_effect=read):
            result=router.workflow_incidents()
        self.assertEqual(len([x for x in result if x["network"]=="pinterest"]),1)
        self.assertEqual(len([x for x in result if x["stage"]=="qa_visibility_lost_github_repo"]),1)

    def test_both_github_sources_inaccessible_raises_for_p0(self):
        def deny(url,*args,**kwargs):
            raise router.urllib.error.HTTPError(url,403,"Forbidden",{},None)
        with patch.object(router,"http",side_effect=deny):
            with self.assertRaisesRegex(RuntimeError,"ALL_REPOS_INACCESSIBLE"):
                router.workflow_incidents()

    def test_queued_older_than_twenty_minutes_is_urgent(self):
        created=(router.NOW-dt.timedelta(minutes=30)).isoformat()
        response={"workflow_runs":[{"name":"CORTES TikTok hosted canonical Neon publisher",
            "status":"queued","conclusion":None,"created_at":created,"id":123456789}]}
        with patch.object(router,"http",return_value=response):
            items=router.workflow_incidents()
        self.assertEqual(len(items),2)
        self.assertTrue(all(x["stage"]=="github_actions_queued_stale" for x in items))

    def test_queue_waiting_under_twenty_minutes_is_not_a_failure(self):
        response={"workflow_runs":[{"name":"CORTES TikTok hosted canonical Neon publisher",
            "status":"queued","conclusion":None,
            "created_at":router.NOW.isoformat(),"id":123456789}]}
        with patch.object(router,"http",return_value=response):
            self.assertEqual(router.workflow_incidents(),[])

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



    def test_wordpress_inaccessible_causes_nonzero_exit_and_one_deduped_alert(self):
        from contextlib import redirect_stdout
        import io
        sinks = {"count": 0, "created": []}
        def fake_wp():
            raise RuntimeError("WP_QA_AUTH_UNAVAILABLE")
        def fake_create(item):
            sinks["created"].append(item)
            return {"number": 1521}
        def fake_dispatch():
            sinks["count"] += 1
        output=io.StringIO()
        with patch.object(router,"TOKEN","fixture"), \
             patch.object(router,"workflow_incidents",return_value=[]), \
             patch.object(router,"codeberg_incidents",return_value=[]), \
             patch.object(router,"daily_round_incidents",return_value=[]), \
             patch.object(router,"wp_incidents",side_effect=fake_wp), \
             patch.object(router,"labels"), \
             patch.object(router,"known_markers",return_value=set()), \
             patch.object(router,"create_issue",side_effect=fake_create), \
             patch.object(router,"dispatch_controller",side_effect=fake_dispatch), \
             redirect_stdout(output):
            exit_code=router.main()
        self.assertEqual(exit_code,2)
        self.assertEqual(len(sinks["created"]),1)
        self.assertEqual(sinks["created"][0]["stage"],"qa_visibility_lost_wordpress")
        self.assertEqual(sinks["count"],1)
        self.assertIn("CORTES_QA_ROUTER_PARTIAL sources_failed=1",output.getvalue())
        self.assertNotIn("CORTES_QA_ROUTER_OK",output.getvalue())

    def test_every_source_available_returns_success_even_without_incidents(self):
        from contextlib import redirect_stdout
        import io
        output=io.StringIO()
        with patch.object(router,"TOKEN","fixture"), \
             patch.object(router,"workflow_incidents",return_value=[]), \
             patch.object(router,"codeberg_incidents",return_value=[]), \
             patch.object(router,"daily_round_incidents",return_value=[]), \
             patch.object(router,"wp_incidents",return_value=[]), \
             patch.object(router,"labels"), \
             patch.object(router,"known_markers",return_value=set()), \
             patch.object(router,"create_issue") as create_issue, \
             patch.object(router,"dispatch_controller") as dispatch, \
             redirect_stdout(output):
            exit_code=router.main()
        self.assertEqual(exit_code,0)
        create_issue.assert_not_called()
        dispatch.assert_not_called()
        self.assertIn("CORTES_QA_ROUTER_OK",output.getvalue())
        self.assertIn("sources_failed=0",output.getvalue())


    def test_wordpress_error_classes_are_sanitized(self):
        self.assertEqual(router.source_failure_code("wordpress",RuntimeError("WP_QA_AUTH_UNAVAILABLE")), "AUTH_MISSING")
        self.assertEqual(router.source_failure_code("wordpress",router.urllib.error.HTTPError(
            "https://anthares.us/wp-json/anthares/v1/cortes/state",401,"secret-hint",{},None)),"HTTP_401")
        self.assertEqual(router.source_failure_code("wordpress",router.urllib.error.HTTPError(
            "https://anthares.us/wp-json/anthares/v1/cortes/state",403,"secret-hint",{},None)),"HTTP_403")
        self.assertEqual(router.source_failure_code("wordpress",router.urllib.error.HTTPError(
            "https://anthares.us/wp-json/anthares/v1/cortes/state",404,"secret-hint",{},None)),"HTTP_404")
        self.assertEqual(router.source_failure_code("wordpress",router.urllib.error.URLError("secret-hint")),"NETWORK_UNAVAILABLE")
        self.assertEqual(router.source_failure_code("wordpress",ValueError("sensitive")),"INVALID_RESPONSE")
        self.assertEqual(router.source_failure_code("wordpress",RuntimeError("some password secret-hint")),"SOURCE_RUNTIME_FAILURE")

    def test_wordpress_http_401_emits_safe_reason_and_nonzero_exit(self):
        import io
        from contextlib import redirect_stdout
        failure=router.urllib.error.HTTPError("https://anthares.us/wp-json/anthares/v1/cortes/state",401,
                                              "do-not-print-secret",{},None)
        output=io.StringIO()
        with patch.object(router,"TOKEN","mock"), \
             patch.object(router,"workflow_incidents",return_value=[]), \
             patch.object(router,"codeberg_incidents",return_value=[]), \
             patch.object(router,"daily_round_incidents",return_value=[]), \
             patch.object(router,"wp_incidents",side_effect=failure), \
             patch.object(router,"labels"), \
             patch.object(router,"known_markers",return_value=set()), \
             patch.object(router,"create_issue",return_value={"number":42}), \
             patch.object(router,"dispatch_controller"), \
             redirect_stdout(output):
            status=router.main()
        self.assertEqual(status,2)
        self.assertIn("CORTES_QA_SCAN_FAILED source=wordpress code=HTTP_401",output.getvalue())
        self.assertNotIn("do-not-print-secret",output.getvalue())
        self.assertIn("CORTES_QA_ROUTER_PARTIAL",output.getvalue())

    def test_direct_dispatch_requires_confirmed_controller_ack(self):
        with patch.object(router,"http",return_value={"ok":True}) as api:
            self.assertTrue(router.dispatch_controller(528))
        url,method,body=api.call_args.args
        self.assertIn("cortes-qa-p0-controller.yml/dispatches",url)
        self.assertEqual(method,"POST")
        self.assertEqual(body["inputs"]["issue_number"],"528")

    def test_direct_dispatch_fails_closed_without_ack(self):
        with patch.object(router,"http",return_value={}):
            with self.assertRaisesRegex(RuntimeError,"NOT_ACKNOWLEDGED"):
                router.dispatch_controller(528)

    def test_issue_204_api_reply_is_success(self):
        from unittest.mock import MagicMock
        context=MagicMock()
        context.__enter__.return_value.status=204
        with patch.object(router.urllib.request,"urlopen",return_value=context):
            self.assertEqual(router.http("https://api.github.com/example","POST",{}),{"ok":True})


    def test_batch_controller_dispatch_is_single_and_has_no_issue_filter(self):
        with patch.object(router,"http",return_value={"ok":True}) as api:
            self.assertTrue(router.dispatch_controller())
        self.assertEqual(api.call_args.args[2],{"ref":"main","inputs":{}})

    def test_same_failing_workflow_produces_one_daily_fingerprint(self):
        now=router.NOW.isoformat()
        data={"workflow_runs":[
            {"name":"Kwai queue publisher","conclusion":"failure","created_at":now,"id":100},
            {"name":"Kwai queue publisher","conclusion":"failure","created_at":now,"id":101}
        ]}
        with patch.object(router,"http",return_value=data):
            issues=router.workflow_incidents()
        self.assertEqual(len(issues),2)
        self.assertEqual(len({i["id"] for i in issues}),2)

    def test_wordpress_missing_credentials_uses_only_authorized_runner_ssh(self):
        with patch.dict(router.os.environ,{
                "RUNNER_NAME":"Anthares-QA-P0-Windows-Independent",
                "WP_SITE_URL":"","WP_USERNAME":"","WP_APP_PASSWORD":""}), \
             patch.object(router,"wp_state_from_authorized_hosting",
                          return_value={"items":[],"blocker":None}) as source:
            self.assertEqual(router.wp_incidents(),[])
        source.assert_called_once_with()

    def test_wordpress_ssh_requires_exact_runner_identity(self):
        with patch.dict(router.os.environ,{"RUNNER_NAME":"some-other-runner"}):
            with self.assertRaisesRegex(RuntimeError,"WP_QA_AUTH_UNAVAILABLE"):
                router.wp_state_from_authorized_hosting()

    def test_wordpress_ssh_success_parses_data_without_payload_logging(self):
        import io
        from types import SimpleNamespace
        from contextlib import redirect_stdout
        result=SimpleNamespace(returncode=0,stdout=b'{"items":[],"blocker":null}')
        output=io.StringIO()
        with patch.dict(router.os.environ,{"RUNNER_NAME":"Anthares-QA-P0-Windows-Independent"}), \
             patch.object(router.subprocess,"run",return_value=result) as run, \
             redirect_stdout(output):
            self.assertEqual(router.wp_state_from_authorized_hosting()["items"],[])
        args=run.call_args.args[0]
        self.assertIn("StrictHostKeyChecking=yes",args)
        self.assertIn("wp eval",args[-1])
        self.assertIn("HOSTING_SSH_READONLY",output.getvalue())
        self.assertNotIn("blocker",output.getvalue())

    def test_wordpress_ssh_failure_never_calls_rest_or_retries(self):
        from types import SimpleNamespace
        result=SimpleNamespace(returncode=255,stdout=b'')
        with patch.dict(router.os.environ,{"RUNNER_NAME":"Anthares-QA-P0-Windows-Independent"}), \
             patch.object(router.subprocess,"run",return_value=result) as run:
            with self.assertRaisesRegex(RuntimeError,"WP_QA_SSH_UNAVAILABLE"):
                router.wp_state_from_authorized_hosting()
        self.assertEqual(run.call_count,1)

    def test_configured_wp_401_does_not_switch_to_ssh(self):
        denied=router.urllib.error.HTTPError("https://anthares.us/wp-json/anthares/v1/cortes/state",401,"Denied",{},None)
        with patch.dict(router.os.environ,{"WP_SITE_URL":"https://anthares.us",
             "WP_USERNAME":"qa","WP_APP_PASSWORD":"invalid"}), \
             patch.object(router,"http",side_effect=denied), \
             patch.object(router,"wp_state_from_authorized_hosting") as ssh:
            with self.assertRaises(router.urllib.error.HTTPError):
                router.wp_incidents()
        ssh.assert_not_called()

if __name__=="__main__":
    unittest.main()
