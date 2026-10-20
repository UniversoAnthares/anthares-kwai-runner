"""Offline tests for irreversible boundary, TikTok identity and callback fencing."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cortes_tiktok_queue_consumer as c


def job():
    return {
        "id": "tt-123", "lease_generation": 2, "status": "leased",
        "source_id": "a4w8KAOxANc", "segment_id": "g1:a4w8KAOxANc:30:80",
        "duration_seconds": 50, "attachment_id": 57,
        "media_url": "https://anthares.us/wp-content/uploads/cortes/clip.mp4",
        "callback_url": c.CALLBACK, "callback_token": "A" * 48,
        "title": "O personagem e suas escolhas",
    }


class TikTokQueueContract(unittest.TestCase):
    def test_valid_job(self):
        self.assertEqual(c.validate_job(job()), ("g1:a4w8KAOxANc:30:80", 2))

    def test_reject_external_media(self):
        j = job()
        j["media_url"] = "https://evil.invalid/x.mp4"
        with self.assertRaises(c.SafeStop):
            c.validate_job(j)

    def test_reject_callback_other_host(self):
        j = job()
        j["callback_url"] = "https://evil.invalid/callback"
        with self.assertRaises(c.SafeStop):
            c.validate_job(j)

    def test_missing_callback_token(self):
        j = job()
        j["callback_token"] = ""
        with self.assertRaises(c.SafeStop):
            c.validate_job(j)

    def test_invalid_duration(self):
        for duration in (0, 29, 91, -1):
            j = job()
            j["duration_seconds"] = duration
            with self.assertRaises(c.SafeStop):
                c.validate_job(j)

    def test_generation_is_mandatory(self):
        j = job()
        j["lease_generation"] = 0
        with self.assertRaises(c.SafeStop):
            c.validate_job(j)

    def test_same_marker_stable(self):
        sid = job()["segment_id"]
        self.assertEqual(c.marker(sid), c.marker(sid))
        self.assertNotEqual(c.marker(sid), c.marker("g1:a4w8KAOxANc:31:81"))
        self.assertRegex(c.marker(sid), r"^#anthares[0-9a-f]{10}$")

    def test_contextual_title_retains_marker(self):
        title = c.caption(job())
        self.assertIn(c.marker(job()["segment_id"]), title)
        self.assertLessEqual(len(title), 100)

    def test_inventory_post_id_requires_correct_account(self):
        sid = job()["segment_id"]
        i = {"ok": True, "account": c.ACCOUNT,
             "items": [{"id": "7577123938226406401", "text": "Short " + c.marker(sid)}]}
        self.assertEqual(c.found(i, sid), "7577123938226406401")
        with self.assertRaises(c.SafeStop):
            c.found(dict(i, account="unrelated"), sid)

    def test_duplicate_marker_fails_closed(self):
        sid = job()["segment_id"]
        i = {"ok": True, "account": c.ACCOUNT,
             "items": [{"id": "7577123938226406401", "text": c.marker(sid)},
                       {"id": "7577123938226406402", "text": c.marker(sid)}]}
        with self.assertRaises(c.SafeStop):
            c.found(i, sid)

    def test_callback_precedes_queue_completion(self):
        j = job()
        sequence = []
        orig_callback, orig_qcall = c.callback, c.qcall
        try:
            c.callback = lambda job, rid: sequence.append("wp")
            def fake_queue(action, creds, body):
                sequence.append(action)
                return {"ok": True, "job": {"status": "confirmed"}}
            c.qcall = fake_queue
            c.finish(j, 2, "7577123938226406401", {"Authorization": "Bearer test"})
            self.assertEqual(sequence, ["wp", "confirm"])
        finally:
            c.callback, c.qcall = orig_callback, orig_qcall

    def test_worker_uses_short_lived_oidc(self):
        from unittest.mock import patch
        with patch.object(c, "oidc", return_value={"Authorization": "Bearer scoped"}) as mint:
            self.assertEqual(c.worker_auth()["Authorization"], "Bearer scoped")
            mint.assert_called_once_with("anthares-render-worker")

    def test_invalid_remote_id_blocks_callback(self):
        orig_callback = c.callback
        try:
            c.callback = lambda *args: self.fail("callback must not execute")
            with self.assertRaises(c.SafeStop):
                c.finish(job(), 2, "not_a_tiktok_id", {})
        finally:
            c.callback = orig_callback


if __name__ == "__main__":
    unittest.main()
