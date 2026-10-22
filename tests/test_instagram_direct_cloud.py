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

if __name__=="__main__":
    unittest.main()
