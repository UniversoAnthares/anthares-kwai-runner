"""Routing contract regression: prevents quota failover without cancel."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class QuotaManifestTests(unittest.TestCase):
    def test_cancel_first_normative_rule(self):
        routing=json.loads((ROOT/"ci-hub/executor-routing.json").read_text(encoding="utf-8"))
        q=routing["ci_execution"]["quota_cancel_first"]
        self.assertEqual("CANCELAR_IMEDIATAMENTE_POR_COTA_V1",q["policy_id"])
        self.assertTrue(q["terminal_confirmation_required"])
        self.assertTrue(q["independent_quota_scope_required"])
        self.assertEqual("NOT_APPLIED_before_successor_dispatch",q["side_effect_result_requirement"])
        self.assertEqual("CANCEL_REQUESTED" in q["immediate_action"],False)
        self.assertEqual(routing["ci_execution"]["priority"][-2:],["appveyor","gitlab_ci"])
        self.assertEqual(q["integration_state"],"CORE_TESTED_PROVIDER_CALLBACKS_NOT_YET_WIRED")

    def test_provider_status_requires_cancel_before_migration(self):
        state=json.loads((ROOT/"ci-hub/provider-status.json").read_text(encoding="utf-8"))
        self.assertEqual(state["rules"]["quota_cancel_contract"],"CANCELAR_IMEDIATAMENTE_POR_COTA_V1")
        self.assertTrue(state["rules"]["quota_failure_action"].startswith("cancel_owned_attempt_immediately"))
        self.assertIn("NOT_YET_CONNECTED",state["rules"]["quota_cancel_adapter_state"])

if __name__=="__main__":unittest.main()
