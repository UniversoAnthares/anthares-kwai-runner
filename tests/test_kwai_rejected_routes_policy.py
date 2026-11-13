"""Protect the Anthares Kwai no-Oracle, no-CutMotions owner decision.

These are contract tests only; they never log into Kwai or execute a publisher.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING = ROOT / "ci-hub" / "executor-routing.json"
PLAN = ROOT / "docs" / "KWAI-PLANO-SEM-ORACLE-20261113.md"
DECISION = ROOT / "test-hub" / "findings" / "20261005-1741-architecture-decisoes-aceitacao.md"
OCI_WORKFLOWS = (
    ROOT / ".github" / "workflows" / "oci-a1-android-cloud-watch.yml",
    ROOT / ".github" / "workflows" / "oci-a1-readonly-smoke-once.yml",
)


class KwaiRoutePolicyTests(unittest.TestCase):
    def test_all_historical_exclusions_remain_pinned(self):
        cfg = json.loads(ROUTING.read_text(encoding="utf-8"))
        actual = set(cfg["android_execution"]["retired_publication_paths"])
        required = {
            "oracle_a1", "cutmotions", "cp_kwai_legacy",
            "kuaishou_open_for_brazil", "kwai_studio_for_regular_videos",
            "github_android_experimental_as_production",
            "pc_as_final_executor", "memu_as_final_executor",
        }
        self.assertTrue(required.issubset(actual))
        self.assertIn("Owner explicit new direction",
                      cfg["android_execution"]["reentry_policy"])
        self.assertEqual(cfg["android_execution"]["github_actions"],
                         "experimental_only")
        self.assertFalse(cfg["android_execution"]["cloud_cutover"]["enabled"])

    def test_strict_zero_cost_and_no_paid_recommendations(self):
        cfg = json.loads(ROUTING.read_text(encoding="utf-8"))
        finance = cfg["android_execution"]["financial_policy"]
        self.assertEqual(finance["max_incremental_recurring_brl"], 0)
        for prop in ("paid_providers_forbidden",
                     "billing_or_card_trials_forbidden",
                     "paid_exception_suggestions_forbidden",
                     "approval_waitlists_out_of_scope",
                     "only_existing_authorized_zero_cost_resources"):
            self.assertIs(finance[prop], True, prop)
        self.assertIs(finance["recommend_paid_plans"], False)
        plan = PLAN.read_text(encoding="utf-8")
        self.assertNotIn("autorizar um servidor pago", plan)
        self.assertIn("NENHUMA PROPOSTA DE PLANO PAGO", plan)

    def test_oracle_workflows_are_inert_and_unscheduled(self):
        for path in OCI_WORKFLOWS:
            with self.subTest(path=str(path)):
                src = path.read_text(encoding="utf-8")
                self.assertNotIn("schedule:", src)
                self.assertNotIn("cron:", src)
                self.assertNotIn("OCI_A1_WATCH_AUTH_JSON", src)
                self.assertNotIn("python tools/oci_a1_capacity_watch.py", src)
                self.assertNotIn("OCI_A1_AUTO_PROVISION", src)
                self.assertNotIn("launch_instance", src)
                self.assertIn("OCI_A1_MONITOR=DISABLED_BY_OWNER", src)

    def test_cutmotions_is_documented_as_rejected_not_candidate(self):
        plan = PLAN.read_text(encoding="utf-8")
        evidence = DECISION.read_text(encoding="utf-8")
        self.assertIn("CutMotions", evidence)
        self.assertIn("CutMotions", plan)
        self.assertIn("Registration failed", plan)
        self.assertIn("PR #2576", plan)
        self.assertIn("revogado", plan)
        self.assertIn("Kuaishou", plan)
        self.assertIn("GitHub Actions", plan)
        self.assertIn("BLOQUEADO_POR_RECURSO_REAL", plan)
        self.assertIn("patrocínio", plan)

    def test_other_exclusions_remain_without_new_oracle_monitor(self):
        preflight = ROOT / "docs" / "REDROID-FREE-VPS-QUALIFICATION.md"
        contract = ROOT / "docs" / "KWAI-CLOUD-CUTOVER-CONTRACT.md"
        for path in (preflight, contract):
            with self.subTest(path=str(path)):
                src = path.read_text(encoding="utf-8")
                self.assertIn("PR #2575", src)
                self.assertNotIn("Oracle A1 continua em tentativa automática", src)


if __name__ == "__main__":
    unittest.main()
