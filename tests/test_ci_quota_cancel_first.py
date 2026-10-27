"""Quota cancellation invariants: no real provider side effects."""
import tempfile
import unittest
from pathlib import Path
from tools.ci_quota_cancel_first import LocalLedger, Route, cancel_first, is_quota

class QuotaTest(unittest.TestCase):
    def test_cancel_first_and_deduplication(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=LocalLedger(Path(directory)/"state.sqlite")
            events=[]
            primary=Route("gitlab","scope-a",True,True,True)
            reserve=Route("github","scope-b",True,True,True)
            def run():
                return cancel_first(
                    ledger=ledger,task_id="task",attempt_id="attempt",current=primary,
                    candidates=[reserve],http_status=None,provider_code="ci_quota_exceeded",
                    error_message="",cancel=lambda x:(events.append("cancel") or True),
                    status=lambda x:(events.append("status") or "CANCELED"),
                    enqueue=lambda r,t,i:(events.append("enqueue") or "external-id"),
                    side_effects_possible=False)
            self.assertEqual(run()["state"],"FALLBACK_QUEUED")
            self.assertEqual(run()["state"],"FALLBACK_QUEUED")
            self.assertEqual(events,["cancel","status","enqueue"])
            ledger.close()

    def test_uncertain_cancel_never_fails_over(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=LocalLedger(Path(directory)/"state.sqlite")
            primary=Route("a","scope-a",True,True,True)
            reserve=Route("b","scope-b",True,True,True)
            calls=[]
            out=cancel_first(
                ledger=ledger,task_id="task",attempt_id="attempt",current=primary,
                candidates=[reserve],http_status=429,provider_code="",error_message="",
                cancel=lambda x:True,status=lambda x:"RUNNING",
                enqueue=lambda r,t,i:(calls.append("enqueue") or "external"),
                side_effects_possible=False)
            self.assertEqual(out["state"],"CANCEL_UNCONFIRMED")
            self.assertFalse(calls)
            ledger.close()

    def test_permission_is_not_quota(self):
        self.assertFalse(is_quota(http_status=401,code="quota_exceeded"))
        self.assertFalse(is_quota(http_status=403,code="forbidden",message="unauthorized"))


class HarnessAdapterTest(unittest.TestCase):
    def _execution(self):
        from tools.ci_quota_cancel_first import HarnessExecution
        return HarnessExecution("account123", "default", "default_project",
                                "pipeline_test", "ABCdef_123")

    def _fake_http(self, statuses):
        import io
        import json
        self.calls = []
        execution = self._execution()
        class Response:
            def __init__(self, body):
                self.body = json.dumps(body).encode()
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return self.body
        def http(req, timeout):
            self.assertEqual(timeout, 12)
            self.calls.append((req.get_method(), req.full_url))
            if req.get_method() == "PUT":
                return Response({"status": "SUCCESS"})
            state = next(statuses)
            return Response({"data": {
                "planExecutionId": execution.plan_execution_id,
                "pipelineIdentifier": execution.pipeline,
                "accountIdentifier": execution.account,
                "orgIdentifier": execution.org,
                "projectIdentifier": execution.project,
                "status": state,
            }})
        return http

    def test_cancel_exact_id_then_confirm_aborted_with_neon_like_ledger(self):
        from tools.ci_quota_cancel_first import HarnessCancelAdapter, Route, cancel_harness_quota
        from tools.ci_quota_cancel_first import LocalLedger
        import types
        with tempfile.TemporaryDirectory() as d:
            # Simulates SharedQuotaLedger's ownership interface; this test
            # never connects to production Neon or Harness.
            ledger = LocalLedger(Path(d)/"ledger.sqlite")
            ledger._owned = {}
            adapter = HarnessCancelAdapter(self._execution(), "test-placeholder",
                                           transport=self._fake_http(iter(["Running", "Aborted"])))
            self.assertTrue(adapter.request_cancel())
            self.assertEqual(adapter.get_owned_status(), "ABORTED")
            self.assertEqual([method for method, _ in self.calls], ["GET", "PUT", "GET"])
            self.assertTrue(all("ABCdef_123" in url for _, url in self.calls))
            ledger.close()

    def test_missing_identity_fails_closed_before_interrupt(self):
        from tools.ci_quota_cancel_first import HarnessCancelAdapter
        import io, json
        calls = []
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"data":{"status":"Running"}}).encode()
        def http(req, timeout):
            calls.append(req.get_method())
            return Response()
        adapter = HarnessCancelAdapter(self._execution(), "test-placeholder",
                                       transport=http)
        with self.assertRaisesRegex(ValueError, "HARNESS_REMOTE_IDENTITY_UNCONFIRMED"):
            adapter.request_cancel()
        self.assertEqual(calls, ["GET"])

    def test_invalid_identity_or_wrong_origin_blocked(self):
        from tools.ci_quota_cancel_first import HarnessExecution, HarnessCancelAdapter
        with self.assertRaises(ValueError):
            HarnessExecution("abc", "default", "x", "pipeline", "../../foreign")
        with self.assertRaises(ValueError):
            HarnessCancelAdapter(self._execution(), "")
        with self.assertRaises(ValueError):
            HarnessCancelAdapter(self._execution(), "test", origin="https://evil.example")

    def test_missing_shared_fencing_prevents_requests(self):
        from tools.ci_quota_cancel_first import cancel_harness_quota
        calls = []
        result = cancel_harness_quota(
            ledger=object(), execution=self._execution(), api_key="test",
            task_id="task", attempt_id="ABCdef_123", http_status=429,
            provider_code="", error_message="",
            transport=lambda *a, **k: calls.append(1))
        self.assertEqual(result["state"], "BLOCKED_SHARED_FENCING_UNAVAILABLE")
        self.assertFalse(calls)

    def test_permission_403_not_quota(self):
        from tools.ci_quota_cancel_first import cancel_harness_quota
        result = cancel_harness_quota(
            ledger=object(), execution=self._execution(), api_key="",
            task_id="task", attempt_id="ABCdef_123", http_status=403,
            provider_code="UNAUTHORIZED", error_message="")
        self.assertEqual(result["state"], "NOT_QUOTA")

if __name__=="__main__":
    unittest.main()
