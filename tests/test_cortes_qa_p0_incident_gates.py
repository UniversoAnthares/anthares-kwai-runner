"""Regression contract for incident-specific P0 repair gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / ".github/workflows/cortes-qa-p0-executor.yml"
CONTROLLER = ROOT / ".github/workflows/cortes-qa-p0-controller.yml"

class PinterestP0GateTests(unittest.TestCase):
    def test_known_incidents_have_distinct_gates(self):
        workflow = EXECUTOR.read_text(encoding="utf-8")
        for issue, token, gate in (
            (460, "HTTP 404", "PINTEREST_MEDIA_404_SOURCE_REPAIR_REQUIRED"),
            (492, "PIN_PUBLISH_BUTTON_NOT_READY", "PINTEREST_PUBLISH_DISABLED_REMOTE_UI_DIAGNOSIS_REQUIRED"),
            (528, "PINTEREST_DRAFT_CAPACITY_EXHAUSTED", "PINTEREST_DRAFT_CAPACITY_RECONCILIATION_REQUIRED"),
        ):
            with self.subTest(issue=issue):
                self.assertIn(f"issue_number === {issue}", workflow)
                self.assertIn(token, workflow)
                self.assertIn(gate, workflow)

    def test_classification_must_not_override_ledger(self):
        workflow = EXECUTOR.read_text(encoding="utf-8")
        self.assertIn("Read-only classification", workflow)
        self.assertIn("QA_REPAIR_GATE", workflow)
        self.assertIn("QA_P0_REPAIR_GATE", workflow)
        self.assertIn("steps.preflight.outcome == 'success'", workflow)

    def test_event_dispatch_and_reconciliation_are_preserved(self):
        workflow = CONTROLLER.read_text(encoding="utf-8")
        self.assertIn("types: [opened, reopened, labeled]", workflow)
        self.assertIn("cron: '*/5 * * * *'", workflow)
        self.assertIn("new Set([460,492,528])", workflow)
        self.assertIn("maxAttemptsPerWindow = 3", workflow)

if __name__ == "__main__":
    unittest.main()
