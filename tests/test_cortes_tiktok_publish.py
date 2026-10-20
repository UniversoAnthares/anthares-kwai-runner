"""Deterministic, offline safety gates for CORTES TikTok distribution."""
import unittest
from tools import cortes_tiktok_publish as p


def clip(sid, status="", duration=45):
    return {"type": "short", "stored": True, "segment_id": sid,
            "attachment_id": 15, "url": "https://anthares.us/media/short.mp4",
            "duration_seconds": duration, "planned_at": "2026-10-19T18:00:00-04:00",
            "networks": {"tiktok": {"status": status}}}


class Contract(unittest.TestCase):
    def test_ready(self):
        selected, unresolved = p.pick({"blocker": {"video_id": "test", "clips": [clip("g1:test:30:75")]}})
        self.assertEqual(len(selected[1]), 1)
        self.assertEqual(unresolved, [])

    def test_no_retry_after_started(self):
        state = {"blocker": {"video_id": "test", "clips": [
            clip("g1:test:30:75", "processing"), clip("g1:test:80:125")
        ]}}
        selected, unresolved = p.pick(state)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(len(selected[1]), 1)

    def test_no_reposts(self):
        for status in ("completed", "processing", "uncertain", "skipped", "error"):
            selected, unresolved = p.pick({"blocker": {"video_id": "test", "clips": [clip("s", status)]}})
            self.assertFalse(selected[1])

    def test_duration(self):
        for duration in (29, 91, 0):
            self.assertFalse(p.valid_clip(clip("x", duration=duration)))

    def test_marker_unique(self):
        a = p.marker("g1:source:5:50")
        b = p.marker("g1:source:6:51")
        self.assertNotEqual(a, b)
        self.assertRegex(a, r"^#anthares[0-9a-f]{10}$")

    def test_inventory_identity(self):
        mark = p.marker("x")
        doc = {"ok": True, "account": "universo.anthares",
               "items": [{"id": "1234", "text": "clip " + mark + " #literatura"}]}
        self.assertEqual(p.post_id_for_marker(doc, mark), "1234")
        with self.assertRaises(p.Blocked):
            p.post_id_for_marker({**doc, "account": "other"}, mark)

    def test_disabled_requires_explicit_enable(self):
        self.assertFalse(p.get_network_enabled({"networks": [{"key": "tiktok", "enabled": False, "types": ["short"]}]}))
        self.assertTrue(p.get_network_enabled({"networks": [{"key": "tiktok", "enabled": True, "types": ["short"]}]}))

if __name__ == "__main__":
    unittest.main()
