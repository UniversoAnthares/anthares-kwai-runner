"""Mocked provider adapter verification. No real remote cancellation."""
import unittest
from tools.ci_quota_provider_adapters import GitHubActionsRun,GitLabPipeline,HarnessPipelineRun,cancel_harness_quota_fenced

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


    def test_harness_aborts_only_exact_owned_execution(self):
        seen=[]
        def fake(method,url,headers):
            seen.append((method,url))
            if method=="PUT":
                return 200, {"status":"SUCCESS"}
            return 200, {"data":{"planExecution":{
                "uuid":"owned123","pipelineIdentifier":"pipe123",
                "status":"Aborted"}}}
        run=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",fake)
        self.assertTrue(run.cancel("owned123"))
        self.assertEqual("CANCELLED",run.status("owned123"))
        self.assertEqual(["PUT","GET"],[m for m,_ in seen])
        self.assertIn("interruptType=AbortAll",seen[0][1])
        self.assertIn("x-api-key",run.headers)
        with self.assertRaises(ValueError):
            run.cancel("different")
        self.assertEqual(2,len(seen))

    def test_harness_fails_closed_on_foreign_or_unknown_status(self):
        def fake(method,url,headers):
            return 200,{"data":{"planExecution":{"uuid":"another",
                          "pipelineIdentifier":"pipe123","status":"Aborted"}}}
        run=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",fake)
        self.assertEqual("UNKNOWN",run.status("owned123"))
        bad=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",
                               lambda *_:(403,{"status":"FAILURE"}))
        self.assertFalse(bad.cancel("owned123"))
        self.assertEqual("UNKNOWN",bad.status("owned123"))

    def test_harness_application_failure_and_no_token(self):
        with self.assertRaises(ValueError):
            HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","")
        run=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",
                               lambda *_:(200,{"status":"FAILURE"}))
        self.assertFalse(run.cancel("owned123"))


    def test_harness_fenced_cancellation_rejects_local_ledger(self):
        from tools.ci_quota_cancel_first import LocalLedger
        import tempfile
        from pathlib import Path
        run=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",
                               lambda *_: (_ for _ in ()).throw(
                                   AssertionError("NETWORK_NOT_ALLOWED")))
        with tempfile.TemporaryDirectory() as d:
            ledger=LocalLedger(Path(d)/"local.sqlite")
            try:
                with self.assertRaisesRegex(ValueError, "SHARED_NEON_LEDGER_REQUIRED"):
                    cancel_harness_quota_fenced(
                        ledger=ledger,api=run,task_id="task1",
                        attempt_id="owned123",quota_code="quota_exceeded",
                        owned_execution_proven=True)
            finally:
                ledger.close()

    def test_harness_fenced_cancellation_rejects_unowned(self):
        from tools.ci_quota_neon_ledger import SharedQuotaLedger
        def forbidden():
            raise AssertionError("NO_DATABASE_CONNECTION_ALLOWED")
        ledger=SharedQuotaLedger(forbidden)
        run=HarnessPipelineRun("acct123","default","project1",
                               "pipe123","owned123","fixture",
                               lambda *_: (_ for _ in ()).throw(
                                   AssertionError("NO_NETWORK_ALLOWED")))
        with self.assertRaisesRegex(ValueError,"HARNESS_OWNERSHIP_PROOF_REQUIRED"):
            cancel_harness_quota_fenced(
                ledger=ledger,api=run,task_id="task1",
                attempt_id="other123",quota_code="quota_exceeded",
                owned_execution_proven=True)
        with self.assertRaisesRegex(ValueError,"HARNESS_OWNERSHIP_PROOF_REQUIRED"):
            cancel_harness_quota_fenced(
                ledger=ledger,api=run,task_id="task1",
                attempt_id="owned123",quota_code="quota_exceeded",
                owned_execution_proven=False)
        result=cancel_harness_quota_fenced(
            ledger=ledger,api=run,task_id="task1",
            attempt_id="owned123",quota_code="permission_denied",
            owned_execution_proven=True)
        self.assertEqual({"state":"NOT_QUOTA"},result)

if __name__=="__main__": unittest.main()
