#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "instagram_autopublish.py"
spec = importlib.util.spec_from_file_location("instagram_autopublish", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(MODULE_PATH.parent))
spec.loader.exec_module(mod)


class InstagramAutopublishTests(unittest.TestCase):
    def row(self, media_id="11", url="https://anthares.us/wp-content/uploads/anthares-clips/2026/10/live_X_01_titulo-microcut.mp4", title="live_X_01_titulo-microcut"):
        return {"id": media_id, "source_url": url, "title": {"rendered": title}}

    def test_requires_microcut_marker_by_default(self):
        legacy = self.row(url="https://anthares.us/wp-content/uploads/anthares-clips/2026/10/live_X_01_titulo.mp4")
        self.assertFalse(mod.is_eligible(legacy))
        self.assertTrue(mod.is_eligible(legacy, allow_legacy=True))

    def test_rejects_non_anthares_media(self):
        row = self.row(url="https://example.test/video-microcut.mp4")
        self.assertFalse(mod.is_eligible(row))

    def test_select_next_skips_published_attachment_and_url(self):
        a = self.row("11")
        b = self.row("12", "https://anthares.us/wp-content/uploads/anthares-clips/2026/10/live_X_02_b-microcut.mp4")
        ledger = {"published": {"11": {"source_url": a["source_url"]}}}
        self.assertEqual(mod.select_next([a, b], ledger)["id"], "12")
        ledger = {"published": {"old": {"source_url": b["source_url"]}, "11": {"source_url": a["source_url"]}}}
        self.assertIsNone(mod.select_next([a, b], ledger))

    def test_caption_is_clean_and_tagged(self):
        caption = mod.clean_caption(self.row(title="live_HtRVqkQ5Opo_02_as-raizes-ocultas-microcut"))
        self.assertIn("As raizes ocultas", caption)
        self.assertIn("#UniversoAnthares", caption)
        self.assertNotIn("microcut", caption.lower())

    def test_ledger_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"
            mod.save_ledger({"version": 1, "published": {"11": {"instagram_media_id": "99"}}}, path)
            data = mod.load_ledger(path)
            self.assertEqual(data["published"]["11"]["instagram_media_id"], "99")


if __name__ == "__main__":
    unittest.main()
