"""Regression tests for the Pinterest browser pre-submit draft fence."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import cortes_pinterest_browser_local as pub


class PinterestDraftFenceTests(unittest.TestCase):
    def test_upload_guard_survives_restart_until_exact_confirm(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "pending.json"
            with patch.object(pub, "DRAFT_GUARD", marker), patch.object(pub, "log"), patch.object(pub, "qa_incident"):
                pub.draft_guard_mark(12, "job-a")
                data = json.loads(marker.read_text(encoding="utf-8"))
                self.assertEqual(data["baseline"], 12)
                self.assertNotIn("job-a", marker.read_text(encoding="utf-8"))
                self.assertTrue(pub.draft_guard_blocked(12))
                self.assertTrue(pub.draft_guard_blocked(0))
                with self.assertRaises(RuntimeError):
                    pub.draft_guard_clear_after_confirmation("job-b")
                pub.draft_guard_clear_after_confirmation("job-a")
                self.assertFalse(marker.exists())
                self.assertFalse(pub.draft_guard_blocked(50))

    def test_guard_is_atomic_and_cannot_be_overwritten_by_second_job(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "pending.json"
            with patch.object(pub, "DRAFT_GUARD", marker):
                pub.draft_guard_mark(0, "job-a")
                with self.assertRaises(FileExistsError):
                    pub.draft_guard_mark(0, "job-b")

    def test_corrupt_guard_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "pending.json"
            marker.write_text("{broken", encoding="utf-8")
            with patch.object(pub, "DRAFT_GUARD", marker), patch.object(pub, "qa_incident") as qa:
                self.assertTrue(pub.draft_guard_blocked(0))
                qa.assert_called_once_with("PINTEREST_DRAFT_GUARD_INVALID")

    def test_full_capacity_reports_nonzero_and_does_not_lease(self):
        with patch.dict(pub.os.environ, {
            "CORTES_PINTEREST_LOCAL_ENABLED": "1",
            "ANTHARES_SOCIAL_COMMIT": "1",
            "ANTHARES_DEVICE_TOKEN": "z" * 50
        }), patch("sys.argv", ["pinterest"]), patch.object(pub, "node_run",
            return_value={"status": "READY", "draft_count": 50}), patch.object(pub, "log"), patch.object(pub, "qa_incident") as qa, patch.object(pub, "call") as call:
            self.assertEqual(pub.main(), 6)
            call.assert_not_called()
            qa.assert_called_with("PINTEREST_DRAFT_CAPACITY_EXHAUSTED")

    def test_browser_notifies_before_autosaved_draft_can_exist(self):
        ui = (Path(pub.__file__).parent / "cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        self.assertLess(ui.index("emit({phase:'UPLOAD_ATTEMPTED'})"),
                        ui.index("await p.rpc('DOM.setFileInputFiles'"))


if __name__ == "__main__":
    unittest.main()
