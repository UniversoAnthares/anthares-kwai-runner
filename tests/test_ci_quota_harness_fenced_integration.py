"""Deterministic end-to-end contract tests: genuine SQL CAS adapter, fake DB, no network."""
import unittest

from tools.ci_quota_neon_ledger import SharedQuotaLedger, StaleQuotaLease
from tools.ci_quota_provider_adapters import HarnessPipelineRun, cancel_harness_quota_fenced
from tests.test_ci_quota_neon_ledger import Database

ACCOUNT = "xAEBvmMUTjql7g2Exxmp-g"
PIPELINE = "pipeline_UniversoAnthares_anthares_kwai_runner_build_9a3d"
EXECUTION = "executionowned123"


def response(state, execution=EXECUTION, pipeline=PIPELINE):
    return {"data": {"planExecution": {
        "uuid": execution, "pipelineIdentifier": pipeline, "status": state
    }}}


class HarnessNeonContractTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.first = SharedQuotaLedger(
            self.db.connect, owner_token="11111111-1111-4111-8111-111111111111")
        self.second = SharedQuotaLedger(
            self.db.connect, owner_token="22222222-2222-4222-8222-222222222222")

    def test_complete_cancel_first_order_and_exclusive_claim(self):
        calls = []
        def fake(method, url, headers):
            calls.append(method)
            self.assertIn("x-api-key", headers)
            if method == "PUT":
                self.assertIn("interruptType=AbortAll", url)
                return 200, {"status": "SUCCESS"}
            self.assertEqual(method, "GET")
            return 200, response("Running" if len(calls) == 1 else "Aborted")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", request=fake)
        reconciled = []
        result = cancel_harness_quota_fenced(
            ledger=self.first, api=api, task_id="job-1",
            attempt_id=EXECUTION, quota_code="quota_exceeded",
            owned_execution_proven=True,
            reconcile=lambda _: (reconciled.append("reconciled") or "NOT_APPLIED"))
        self.assertEqual("CANCELLED_NO_INDEPENDENT_RESERVE", result["state"])
        self.assertEqual(["GET", "PUT", "GET"], calls)
        self.assertEqual(["reconciled"], reconciled)
        row = self.db.rows["harness:" + EXECUTION]
        self.assertEqual(row["state"], "CANCELLED_NO_INDEPENDENT_RESERVE")
        self.assertGreaterEqual(row["generation"], 3)
        def other_request(method, url, headers):
            calls.append("other:" + method)
            if method == "PUT":
                raise AssertionError("DUPLICATE_ABORT_FORBIDDEN")
            return 200, response("Running")
        other = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                   PIPELINE, EXECUTION, "fixture", request=other_request)
        repeat = cancel_harness_quota_fenced(
            ledger=self.second, api=other, task_id="job-1",
            attempt_id=EXECUTION, quota_code="quota_exceeded",
            owned_execution_proven=True)
        self.assertEqual("CANCELLED_NO_INDEPENDENT_RESERVE", repeat["state"])
        self.assertEqual(1, calls.count("PUT"))
        self.assertEqual(["other:GET"], [c for c in calls if c.startswith("other:")])

    def test_wrong_provider_execution_preflight_never_claims_or_aborts(self):
        calls = []
        def request(method, *_):
            calls.append(method)
            if method == "PUT":
                raise AssertionError("FOREIGN_EXECUTION_ABORT_FORBIDDEN")
            return 200, response("Running", execution="foreign")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", request)
        result = cancel_harness_quota_fenced(
            ledger=self.first, api=api, task_id="job",
            attempt_id=EXECUTION, quota_code="quota_exceeded",
            owned_execution_proven=True)
        self.assertEqual("HARNESS_PREFLIGHT_NOT_RUNNING_OR_UNVERIFIED", result["state"])
        self.assertEqual(["GET"], calls)
        self.assertEqual({}, self.db.rows)

    def test_uncertain_cancel_or_side_effects_never_dispatch_successor(self):
        counter = {"get": 0}
        def request(method, *_):
            if method == "PUT":
                return 503, {"status": "ERROR"}
            counter["get"] += 1
            return 200, response("Running")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", request)
        result = cancel_harness_quota_fenced(
            ledger=self.first, api=api, task_id="job",
            attempt_id=EXECUTION, quota_code="quota_exceeded",
            owned_execution_proven=True)
        self.assertEqual("CANCEL_UNCONFIRMED", result["state"])
        self.assertEqual("CANCEL_UNCONFIRMED", self.db.rows["harness:"+EXECUTION]["state"])
        self.assertEqual(1, counter["get"])

    def test_terminal_but_side_effects_unknown_blocks_fallback(self):
        calls = []
        def request(method, *_):
            calls.append(method)
            if method == "PUT":
                return 200, {"status": "SUCCESS"}
            return 200, response("Running" if len(calls) == 1 else "Aborted")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", request)
        result = cancel_harness_quota_fenced(
            ledger=self.first, api=api, task_id="job",
            attempt_id=EXECUTION, quota_code="quota_exceeded",
            owned_execution_proven=True)
        self.assertEqual("RECONCILE_REQUIRED", result["state"])
        self.assertIsNone(result["successor"])

    def test_lease_expiry_during_cancel_does_not_dispatch(self):
        calls = []
        def request(method, *_):
            calls.append(method)
            if method == "PUT":
                self.db.expired = True
                return 200, {"status": "SUCCESS"}
            return 200, response("Running" if len(calls) == 1 else "Aborted")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", request)
        with self.assertRaises(StaleQuotaLease):
            cancel_harness_quota_fenced(
                ledger=self.first, api=api, task_id="job",
                attempt_id=EXECUTION, quota_code="quota_exceeded",
                owned_execution_proven=True, reconcile=lambda _: "NOT_APPLIED")
        self.assertEqual(["GET", "PUT", "GET"], calls)
        self.assertEqual("CANCEL_REQUESTED",
                         self.db.rows["harness:"+EXECUTION]["state"])

    def test_permissions_even_with_quota_phrase_never_cancel(self):
        def forbidden(*args):
            raise AssertionError("NO_NETWORK_ALLOWED")
        api = HarnessPipelineRun(ACCOUNT, "default", "default_project",
                                 PIPELINE, EXECUTION, "fixture", forbidden)
        for code in ("quota_exceeded", "forbidden"):
            result = cancel_harness_quota_fenced(
                ledger=self.first, api=api, task_id="job",
                attempt_id=EXECUTION, quota_code=code,
                http_status=403, error_message="quota exceeded",
                owned_execution_proven=True)
            self.assertEqual("NOT_QUOTA", result["state"])
        self.assertEqual({}, self.db.rows)


if __name__ == "__main__":
    unittest.main()
