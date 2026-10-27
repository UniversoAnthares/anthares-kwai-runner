"""Mocked provider adapter verification. No real remote cancellation."""
import unittest
from tools.ci_quota_provider_adapters import GitHubActionsRun,GitLabPipeline

class ProvidersTest(unittest.TestCase):
    def test_github_post_cancel_before_status(self):
        seen=[]
        def fake(method,url,headers):
            seen.append((method,url))
            if method=="POST":return 202,{}
            return 200,{"status":"completed","conclusion":"cancelled"}
        run=GitHubActionsRun("UniversoAnthares","anthares-kwai-runner",123,"fixture",fake)
        self.assertTrue(run.cancel("owned-123"))
        self.assertEqual("CANCELLED",run.status("owned-123"))
        self.assertEqual(["POST","GET"],[x[0] for x in seen])
        self.assertTrue(seen[0][1].endswith("/runs/123/cancel"))

    def test_github_already_failed_is_terminal(self):
        def fake(method,url,headers):
            return (409,{}) if method=="POST" else (200,{"status":"completed","conclusion":"failure"})
        run=GitHubActionsRun("a","b",55,"fixture",fake)
        self.assertTrue(run.cancel("owned-55"))
        self.assertEqual("FAILED",run.status("owned-55"))

    def test_gitlab_explicit_pipeline_cancel(self):
        seen=[]
        def fake(method,url,headers):
            seen.append((method,url))
            return (200,{"status":"canceled"}) if method=="GET" else (200,{"status":"canceling"})
        run=GitLabPipeline("UniversoAnthares/anthares-kwai-runner",123,"fixture",fake)
        self.assertTrue(run.cancel("owned-123"))
        self.assertEqual("CANCELLED",run.status("owned-123"))
        self.assertIn("UniversoAnthares%2Fanthares-kwai-runner",seen[0][1])
        self.assertEqual(["POST","GET"],[x[0] for x in seen])

    def test_gitlab_uncertain_cancellation_is_not_acknowledged(self):
        def fake(method,url,headers):
            return (503,{})
        run=GitLabPipeline("org/project",5,"fixture",fake)
        self.assertFalse(run.cancel("owned-5"))
        self.assertEqual("UNKNOWN",run.status("owned-5"))

if __name__=="__main__": unittest.main()
