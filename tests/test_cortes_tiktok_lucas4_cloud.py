import base64,importlib.util,json,os,sys,unittest,zlib
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
spec=importlib.util.spec_from_file_location("lucas4",ROOT/"tools"/"cortes_tiktok_lucasrosalem4_cloud_publish.py")
q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

class SecondaryCloudTests(unittest.TestCase):
    def test_isolates_identity_and_account(self):
        self.assertEqual(q.ACCOUNT,"lucasrosalem4")
        self.assertIn("cortestiktok4",q.QUEUE)
        self.assertEqual(q.AUDIENCE,"https://anthares-remote-primary.vercel.app/api/cortes-tiktok")
        self.assertTrue(q.SEGMENT.fullmatch("g1:fOmihuHUT1M:4512:4561"))
        self.assertFalse(q.SEGMENT.fullmatch("../unsafe"))
        self.assertTrue(q.VID.fullmatch("7699234172166081810"))

    def test_marker_is_deterministic_and_per_account(self):
        sid="g1:9CIk-I_3VhM:7216:7273"
        got=q.marker(sid)
        self.assertRegex(got,r"^#anthares[a-f0-9]{10}$")
        self.assertNotEqual(got,q.marker("g1:9CIk-I_3VhM:7273:7320"))

    def test_session_secret_is_compressed_and_never_raw(self):
        state={"cookies":[{"name":"sessionid","domain":".tiktok.com",
                           "value":"test-never-real","expires":-1}],"origins":[]}
        raw=base64.b64encode(zlib.compress(json.dumps(state).encode(),9)).decode()
        with patch.dict(os.environ,{"TIKTOK_LUCASROSALEM4_STORAGE_STATE":raw}):
            self.assertEqual(q.state_from_secret()["cookies"][0]["name"],"sessionid")
        with patch.dict(os.environ,{"TIKTOK_LUCASROSALEM4_STORAGE_STATE":json.dumps(state)}):
            with self.assertRaises(q.SafeStop):
                q.state_from_secret()

    def test_guard_unauthorized_without_oidc(self):
        with patch.dict(os.environ,{"ACTIONS_ID_TOKEN_REQUEST_URL":"",
                                    "ACTIONS_ID_TOKEN_REQUEST_TOKEN":""},clear=True):
            with self.assertRaises(q.SafeStop):
                q.oidc()

    def test_cloudflare_queue_ingress_is_independent_and_rejects_anonymous_mutation(self):
        self.assertEqual(q.BACKUP_QUEUE,"https://anthares-cortes-tiktok-lucas4-ha.anthares1.workers.dev/")
        edge=(ROOT/"infra"/"cloudflare-cortes-tiktok-lucas4-ha"/"src"/"index.js").read_text(encoding="utf-8")
        self.assertIn("cortestiktok4.compute",edge)
        self.assertIn("oidc_required",edge)
        self.assertIn("'mirror'",edge)
        self.assertNotIn("vercel.app",edge)

    def test_prestart_claim_recovers_via_same_neon_ledger_cloudflare(self):
        from urllib.error import HTTPError
        from unittest.mock import Mock
        failure=HTTPError(q.QUEUE,503,"Backend temporarily unavailable",{},None)
        backup=Mock()
        backup.__enter__=Mock(return_value=backup)
        backup.__exit__=Mock(return_value=False)
        with patch.object(q.urllib.request,"urlopen",side_effect=[failure,backup]) as mocked, \
             patch.object(q,"read_json",return_value={"ok":True,"job":None}):
            self.assertTrue(q.call("claim","fake-token",{})["ok"])
        self.assertEqual(mocked.call_count,2)
        self.assertIn("lucas4-ha",mocked.call_args.args[0].full_url)

    def test_claim_wait_budget_is_longer_than_neon_multistep_response(self):
        from unittest.mock import Mock
        response=Mock()
        response.__enter__=Mock(return_value=response)
        response.__exit__=Mock(return_value=False)
        with patch.object(q.urllib.request,"urlopen",return_value=response) as request, \\
             patch.object(q,"read_json",return_value={"ok":True,"mode":"idle","job":None}):
            self.assertEqual(q.call("claim","fake-token",{}).get("mode"),"idle")
        self.assertGreaterEqual(request.call_args.kwargs["timeout"],100)

    def test_irreversible_start_never_retries_after_http_error(self):
        from urllib.error import HTTPError
        failure=HTTPError(q.QUEUE,503,"unknown completion",{},None)
        with patch.object(q.urllib.request,"urlopen",side_effect=failure) as mocked:
            with self.assertRaisesRegex(q.SafeStop,"HTTP_503_ACTION_start"):
                q.call("start","fake-token",{"id":"anything"})
        self.assertEqual(mocked.call_count,1)

    def test_reconciliation_timeout_preserves_uncertain(self):
        from unittest.mock import MagicMock
        runtime=MagicMock()
        runner=MagicMock()
        runner.__enter__.return_value=runtime
        # Isolate the browser dependency: unit tests on Codeberg tiny run
        # without installing Playwright or launching any interactive Chromium.
        import sys
        import types
        shim=types.ModuleType("playwright")
        sync=types.ModuleType("playwright.sync_api")
        sync.sync_playwright=MagicMock()
        shim.sync_api=sync
        with patch.dict(sys.modules,{"playwright":shim,"playwright.sync_api":sync}):
            with patch("playwright.sync_api.sync_playwright",return_value=runner):
                with patch.object(q,"studio",side_effect=TimeoutError()):
                    with patch.object(q,"call") as api:
                        self.assertFalse(q.reconcile_uncertain(
                            {"status":"uncertain"},"token",{}))
                    api.assert_not_called()

    def test_uncertain_mode_never_reenters_upload_editor(self):
        job={"id":"tt-test","status":"uncertain",
             "segment_id":"g1:9CIk-I_3VhM:7216:7273","lease_generation":3}
        with patch.object(q,"reconcile_uncertain",return_value=False) as inspect, \
             patch.object(q,"publish_one") as publish:
            self.assertFalse(q.handle_claim({"mode":"reconcile","job":job},"token",{}))
        inspect.assert_called_once_with(job,"token",{})
        publish.assert_not_called()

    def test_uncertain_without_remote_marker_never_mutates_queue(self):
        job={"id":"tt-test","status":"uncertain",
             "segment_id":"g1:9CIk-I_3VhM:7216:7273","lease_generation":3}
        with patch.object(q,"call") as api:
            self.assertFalse(q.reconcile_exact_studio_match(
                job,"token",{"7699234172166081810":"other caption"}))
        api.assert_not_called()

    def test_existing_uncertain_marker_confirms_without_new_start(self):
        job={"id":"tt-test","status":"uncertain",
             "segment_id":"g1:9CIk-I_3VhM:7216:7273","lease_generation":3}
        rid="7699234172166081810"
        with patch.object(q,"call",return_value={"ok":True,
             "job":{"remote_id":rid,"status":"confirmed"}}) as api:
            self.assertTrue(q.reconcile_exact_studio_match(
                job,"token",{rid:"existing post "+q.marker(job["segment_id"])}))
        api.assert_called_once_with("confirm","token",
            {"id":"tt-test","lease_generation":3,"remote_id":rid})

    def test_ambiguous_marker_stops_without_creating_post(self):
        job={"id":"tt-test","status":"uncertain",
             "segment_id":"g1:9CIk-I_3VhM:7216:7273","lease_generation":3}
        content=q.marker(job["segment_id"])
        with patch.object(q,"call") as api:
            with self.assertRaisesRegex(q.SafeStop,"MULTIPLE_STUDIO_MATCHES"):
                q.reconcile_exact_studio_match(job,"token",
                   {"7699234172166081810":content,
                    "7699234172166081811":content})
        api.assert_not_called()

    def test_uncertain_reconciliation_rejects_leased_state(self):
        job={"id":"tt-test","status":"leased",
             "segment_id":"g1:9CIk-I_3VhM:7216:7273","lease_generation":3}
        with patch.object(q,"call") as api:
            with self.assertRaisesRegex(q.SafeStop,"FENCE_INVALID"):
                q.reconcile_exact_studio_match(job,"token",{})
        api.assert_not_called()

    def test_only_publish_mode_and_leased_job_can_upload(self):
        job={"id":"tt-test","status":"leased","lease_generation":1}
        with patch.object(q,"publish_one") as publish:
            self.assertTrue(q.handle_claim({"mode":"publish","job":job},"token",{}))
            with self.assertRaisesRegex(q.SafeStop,"MODE_OR_LEASE_INVALID"):
                q.handle_claim({"mode":"publish",
                                 "job":dict(job,status="uncertain")},"token",{})
        publish.assert_called_once_with(job,"token",{})

    def test_prestart_publish_failure_sends_fenced_cooldown(self):
        job={"id":"tt-test","status":"leased","lease_generation":3}
        with patch.object(q,"publish_one",side_effect=q.SafeStop("preflight")) as publish, \
             patch.object(q,"call",return_value={"ok":True}) as api:
            with self.assertRaisesRegex(q.SafeStop,"preflight"):
                q.handle_claim({"mode":"publish","job":job},"token",{})
        publish.assert_called_once()
        api.assert_called_once_with("fail","token",
            {"id":"tt-test","lease_generation":3,
             "error":"secondary_cloud_requires_reconciliation"})

    def test_studio_retries_empty_html_until_exact_account(self):
        from unittest.mock import Mock
        page=Mock()
        page.url="https://www.tiktok.com/tiktokstudio/content"
        page.goto.return_value=Mock(status=200)
        password=Mock()
        password.count.return_value=0
        listing=Mock()
        listing.evaluate_all.side_effect=[[],[
            {"href":"https://www.tiktok.com/@lucasrosalem4/video/7699234172166081810",
             "text":"existing video"}]]
        page.locator.side_effect=lambda selector: password if "password" in selector else listing
        self.assertEqual(len(q.studio(page)),1)
        self.assertEqual(page.goto.call_count,2)

    def test_studio_rejects_foreign_identity_without_post(self):
        from unittest.mock import Mock
        page=Mock()
        page.url="https://www.tiktok.com/tiktokstudio/content"
        page.goto.return_value=Mock(status=200)
        password=Mock()
        password.count.return_value=0
        listing=Mock()
        listing.evaluate_all.return_value=[
            {"href":"https://www.tiktok.com/@foreign/video/7699234172166081810",
             "text":"foreign video"}]
        page.locator.side_effect=lambda selector: password if "password" in selector else listing
        with self.assertRaisesRegex(q.SafeStop,"IDENTITY_NOT_EXACT"):
            q.studio(page)
        self.assertEqual(page.goto.call_count,1)

    def test_studio_empty_after_three_attempts_is_safe_stop(self):
        from unittest.mock import Mock
        page=Mock()
        page.url="https://www.tiktok.com/tiktokstudio/content"
        page.goto.return_value=Mock(status=200)
        password=Mock()
        password.count.return_value=0
        listing=Mock()
        listing.evaluate_all.return_value=[]
        page.locator.side_effect=lambda selector: password if "password" in selector else listing
        with self.assertRaisesRegex(q.SafeStop,"NO_OWNED_LINKS"):
            q.studio(page)
        self.assertEqual(page.goto.call_count,3)

    def test_cloud_starts_are_budgeted_by_second_account(self):
        source=(ROOT/"infra"/"neon-cortes-lucasrosalem4"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn("const TARGET='tiktok:lucasrosalem4'",source)
        self.assertIn("cortes_tiktok_lucasrosalem4_publications",source)
        self.assertIn("action==='mirror'",source)
        self.assertIn("cortes_tiktok_publications",source)
        self.assertNotIn("if(claims.repository===CLIPPER){role='producer'",source)

if __name__=="__main__":
    unittest.main()
