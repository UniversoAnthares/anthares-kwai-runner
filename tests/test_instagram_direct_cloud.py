"""Unit contracts for Instagram Graph direct primary and Neon queue fencing."""
from __future__ import annotations
import os
import unittest
import urllib.error
from unittest.mock import patch
from tools import cortes_instagram_direct_cloud as direct

class DirectInstagramTests(unittest.TestCase):
    def test_404_isolated_only_after_confirmed_head_and_get(self):
        url="https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_example.mp4"
        def failed(*args,**kwargs):
            raise urllib.error.HTTPError(url,404,"missing",None,None)
        with patch.object(direct.urllib.request,"urlopen",side_effect=failed) as probe:
            self.assertTrue(direct.missing_media(url))
            self.assertEqual(probe.call_count,2)

    def test_non404_does_not_quarantine(self):
        url="https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_example.mp4"
        def rate_limited(*args,**kwargs):
            raise urllib.error.HTTPError(url,429,"quota",None,None)
        with patch.object(direct.urllib.request,"urlopen",side_effect=rate_limited):
            with self.assertRaises(urllib.error.HTTPError):
                direct.missing_media(url)

    def test_wrong_media_domain_fails_closed(self):
        with self.assertRaises(RuntimeError):
            direct.missing_media("https://evil.example/short_test.mp4")

    def test_local_execution_cannot_publish(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","INSTAGRAM_USER_ID":"123456789",
                                     "INSTAGRAM_ACCESS_TOKEN":"fake"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"HOSTED_WORKFLOW_ONLY"):
                direct.require_cloud()

    def test_official_meta_host_fallback_is_readonly_and_identity_fenced(self):
        class FakeClient:
            def __init__(self, user_id, access_token, api_version, graph_host):
                self.graph_host=graph_host
            def _request(self, method, path, query=None):
                self.assertions=(method,path,query)
                if self.graph_host=="graph.instagram.com":
                    raise RuntimeError("Instagram API HTTP 400: login type differs")
                return {"id":"123456789","username":"universoanthares"}
        env={
            "GITHUB_ACTIONS":"true", "RUNNER_ENVIRONMENT":"github-hosted",
            "RUNNER_OS":"Linux", "GITHUB_REPOSITORY":"UniversoAnthares/anthares-kwai-runner",
            "GITHUB_REF":"refs/heads/main",
            "GITHUB_WORKFLOW_REF":"UniversoAnthares/anthares-kwai-runner/.github/workflows/cortes-instagram-direct-cloud.yml@refs/heads/main",
            "ANTHARES_SOCIAL_COMMIT":"1",
            "ACTIONS_ID_TOKEN_REQUEST_URL":"https://example.invalid/oidc",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN":"test-oidc-token",
            "INSTAGRAM_USER_ID":"123456789","INSTAGRAM_ACCESS_TOKEN":"test-token",
            "INSTAGRAM_GRAPH_HOST":"graph.instagram.com",
        }
        with patch.dict(os.environ,env,clear=True), \
             patch.object(direct,"InstagramClient",FakeClient), \
             patch.object(direct,"neon") as queue:
            actual=direct.require_cloud()
            self.assertEqual(actual.graph_host,"graph.facebook.com")
            queue.assert_not_called()

    def test_queue_authority_is_not_called_before_cloud_identity(self):
        with patch.object(direct,"require_cloud",side_effect=RuntimeError("AUTH_UNAVAILABLE")):
            with patch.object(direct,"neon") as q:
                with self.assertRaises(RuntimeError):
                    direct.main()
                q.assert_not_called()

    def test_caption_has_exact_site_and_single_brand_suffix(self):
        payload = {
            "title": "Por que a construção das personagens exige uma decisão formal",
            "description": "Análise de um procedimento específico de escrita literária.",
        }
        result = direct.instagram_caption(payload)
        self.assertTrue(result.splitlines()[0].endswith(" ● Universo Anthares"))
        self.assertIn("www.anthares.us", result)
        self.assertEqual(result.count(" ● Universo Anthares"), 1)
        again = direct.instagram_caption({
            **payload, "title": result.splitlines()[0],
            "description": result.split("\n", 1)[1],
        })
        self.assertEqual(again, result)

    def test_caption_preserves_website_when_long(self):
        payload = {
            "title": "Narradores e os problemas de focalização no conto moderno",
            "description": ("A descrição explica o segmento selecionado. " * 100),
        }
        result = direct.instagram_caption(payload)
        self.assertLessEqual(len(result), 2200)
        self.assertIn("www.anthares.us", result)

    def test_durable_quota_gate_parses_existing_issue_state(self):
        body = 'Quota control.\n\n```json\n{"service":"instagram-direct-graph","cooldown_until_utc":"2099-11-13T06:00:00Z"}\n```'
        with patch.object(direct, "quota_issue", return_value={"body": body}):
            self.assertEqual(direct.quota_hold_until(), "2099-11-13T06:00:00Z")

    def test_wrong_quota_scope_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "SCOPE_INVALID"):
            direct.quota_record('```json\n{"service":"different-account"}\n```')

    def test_cooldown_blocks_all_claims_and_graph_posts(self):
        from types import SimpleNamespace
        client=SimpleNamespace(get_quota=lambda: SimpleNamespace(total=100,usage=100))
        with patch.object(direct, "require_cloud", return_value=client), \
             patch.object(direct, "quota_hold_until", return_value="2099-11-13T06:00:00Z"), \
             patch.object(direct, "publish_once") as once:
            self.assertEqual(direct.main(), 0)
            once.assert_not_called()

    def test_stale_24h_cooldown_yields_to_live_provider_quota(self):
        from types import SimpleNamespace
        client=SimpleNamespace(get_quota=lambda: SimpleNamespace(total=100,usage=44))
        with patch.object(direct, "require_cloud", return_value=client), \
             patch.object(direct, "daily_publication_window", return_value=True), \
             patch.object(direct, "quota_hold_until", return_value="2099-11-13T06:00:00Z"), \
             patch.object(direct, "publish_once", return_value=0) as once:
            self.assertEqual(direct.main(),0)
            once.assert_called_once_with(client)

    def test_unknown_provider_quota_does_not_bypass_hold(self):
        from types import SimpleNamespace
        client=SimpleNamespace(get_quota=lambda: SimpleNamespace(total=None,usage=None))
        with patch.object(direct, "require_cloud", return_value=client), \
             patch.object(direct, "daily_publication_window", return_value=True), \
             patch.object(direct, "quota_hold_until", return_value="2099-11-13T06:00:00Z"), \
             patch.object(direct, "publish_once") as once:
            self.assertEqual(direct.main(),0)
            once.assert_not_called()

    def test_quota_batch_terminal_does_not_submit_next_clip(self):
        with patch.object(direct, "require_cloud", return_value=object()), \
             patch.object(direct, "quota_hold_until", return_value=None), \
             patch.object(direct, "publish_once", side_effect=[5, 1]) as once, \
             patch.object(direct.time, "sleep") as sleeper:
            self.assertEqual(direct.main(), 0)
            self.assertEqual(once.call_count, 1)
            sleeper.assert_not_called()

    def test_tagged_captions_are_unique_per_clip_and_idempotent(self):
        payload = {"title": "A Poética de Aristóteles", "description": "Análise da tragédia."}
        one = "cortes-fanout-instagram-" + "a"*32
        two = "cortes-fanout-instagram-" + "b"*32
        c1 = direct.instagram_caption(payload, one)
        c2 = direct.instagram_caption(payload, two)
        self.assertNotEqual(c1, c2)
        self.assertIn("www.anthares.us", c1)
        self.assertEqual(c1.count("#antharescorte"), 1)
        self.assertTrue(c1.splitlines()[0].endswith(" ● Universo Anthares"))
        self.assertEqual(c1, direct.instagram_caption({
            "title": c1.splitlines()[0],
            "description": c1.split("\n",1)[1],
        }, one))

    def test_daily_window_is_local_six_to_midnight(self):
        from datetime import datetime, timezone
        self.assertFalse(direct.daily_publication_window(datetime(
            2026, 11, 12, 9, 30, tzinfo=timezone.utc)))
        self.assertTrue(direct.daily_publication_window(datetime(
            2026, 11, 12, 10, 30, tzinfo=timezone.utc)))
        self.assertFalse(direct.daily_publication_window(datetime(
            2026, 11, 13, 3, 30, tzinfo=timezone.utc)))
        self.assertFalse(direct.daily_publication_window(datetime(
            2026, 11, 13, 4, 30, tzinfo=timezone.utc)))

    def test_one_due_slot_submits_at_most_one_reel_per_run(self):
        with patch.object(direct, "require_cloud", return_value=object()), \
             patch.object(direct, "daily_publication_window", return_value=True), \
             patch.object(direct, "quota_hold_until", return_value=None), \
             patch.object(direct, "publish_once", side_effect=[1,1]) as once:
            self.assertEqual(direct.main(), 0)
            self.assertEqual(once.call_count, 1)

    def test_provider_room_is_taken_from_authenticated_account_api(self):
        from types import SimpleNamespace
        for total, used, expected in ((100,44,56),(100,100,0),
                                      (100,None,None),(101,0,None)):
            client=SimpleNamespace(get_quota=lambda t=total,u=used:
                                      SimpleNamespace(total=t,usage=u))
            self.assertEqual(direct.provider_room(client),expected)

    def test_no_lease_before_provider_quota_known(self):
        from types import SimpleNamespace
        client=SimpleNamespace(get_quota=lambda:SimpleNamespace(total=None,usage=None))
        with patch.object(direct, "neon") as q:
            self.assertEqual(direct.publish_once(client), 0)
            q.assert_not_called()

    def test_wait_slot_obeys_neon_due_without_claiming_or_sleeping(self):
        from types import SimpleNamespace
        client=SimpleNamespace(get_quota=lambda:SimpleNamespace(total=100,usage=44))
        plan={"status":"WAIT","next_due_at":"2026-11-12T19:12:00Z",
              "interval_seconds":572.0,"remaining_today":54}
        with patch.object(direct,"neon",return_value={"ok":True,"job":None,"pacing":plan}) as neon, \
             patch.object(direct.time,"sleep") as sleeper:
            self.assertEqual(direct.publish_once(client),0)
            neon.assert_called_once_with("lease", {"target_key":direct.TARGET,
                                         "owner":direct.OWNER,"quota_remaining":56})
            sleeper.assert_not_called()

    def test_start_recheck_blocks_media_without_mutating_terminal_state(self):
        from types import SimpleNamespace
        job={"id":"cortes-fanout-instagram-"+"a"*32,
             "lease_generation":2,"target_key":direct.TARGET,"duration_class":"short",
             "payload":{"platform":"instagram","account_id":"universoanthares",
                        "title":"Exemplo",
                        "media_url":"https://anthares.us/wp-content/uploads/anthares-clips/2026/11/test.mp4"}}
        client=SimpleNamespace(get_quota=lambda:SimpleNamespace(total=100,usage=44))
        def fake_neon(action, data):
            if action=="lease":return {"ok":True,"job":job}
            if action=="start":return {"ok":True,"job":None,"pacing":{"status":"WAIT"}}
            if action=="fail":return {"ok":True,"job":{"status":"queued"}}
            raise AssertionError(action)
        with patch.object(direct,"neon",side_effect=fake_neon) as q, \
             patch.object(direct,"missing_media",return_value=False), \
             patch.object(direct,"ensure_vertical_media",return_value=job["payload"]["media_url"]):
            self.assertEqual(direct.publish_once(client),0)
            self.assertEqual([c.args[0] for c in q.call_args_list],["lease","start","fail"])
            self.assertEqual(q.call_args_list[1].args[1]["quota_remaining"],56)

    def test_day_ends_at_2300_exactly(self):
        from datetime import datetime, timezone
        self.assertTrue(direct.daily_publication_window(datetime(
            2026,11,13,2,59,59,tzinfo=timezone.utc)))
        self.assertFalse(direct.daily_publication_window(datetime(
            2026,11,13,3,0,0,tzinfo=timezone.utc)))

if __name__=="__main__":
    unittest.main()
