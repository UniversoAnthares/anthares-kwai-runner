import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from types import SimpleNamespace

from tools.x_publication_safety import confirmed_today, gate, validate_video, verified_post_url


class XPublicationSafetyTests(unittest.TestCase):
    DAY = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)

    def issue(self, number, state="closed", body=None, created="2026-10-21T11:00:00Z"):
        import json
        payload = body or {"platform": "x", "account": "lucasyahn", "source_id": "source-1"}
        return {"title": "[X-PUBLISH] sample", "number": number, "state": state,
                "body": "```json\n" + json.dumps(payload) + "\n```", "created_at": created}

    def test_closed_issue_does_not_count(self):
        i = self.issue(1)
        self.assertFalse(confirmed_today(i, [], self.DAY.date(), timezone.utc))
        self.assertTrue(gate([i], {}, self.DAY)["due"])

    def test_confirm_requires_video_url_and_date(self):
        i = self.issue(1)
        c = {"body": "CONFIRMED video https://x.com/lucasyahn/status/2109698725161631921",
             "created_at": "2026-10-21T12:00:00Z"}
        self.assertEqual(len(confirmed_today(i, [c], self.DAY.date(), timezone.utc)), 1)
        self.assertEqual(gate([i], {1: [c]}, self.DAY)["confirmed"], 1)
        self.assertFalse(confirmed_today(i, [{**c, "created_at": "2026-10-20T12:00:00Z"}], self.DAY.date(), timezone.utc))

    def test_reject_wrong_account_and_missing_video(self):
        self.assertIsNone(verified_post_url("https://x.com/other/status/2109698725161631921"))
        c = {"body": "CONFIRMED https://x.com/lucasyahn/status/2109698725161631921",
             "created_at": "2026-10-21T12:00:00Z"}
        self.assertEqual(confirmed_today(self.issue(1), [c], self.DAY.date(), timezone.utc), set())

    def test_legacy_fixture_is_excluded(self):
        i = self.issue(1, body={"platform": "x", "account": "lucasyahn", "test_fixture": True})
        self.assertEqual(gate([i], {}, self.DAY)["confirmed"], 0)

    def test_stale_issue_does_not_freeze_new_work(self):
        i = self.issue(2, "open", created="2026-10-20T01:00:00Z")
        result = gate([i], {}, self.DAY)
        self.assertTrue(result["due"])
        self.assertEqual(result["stale_issue_numbers"], [2])

    def test_recent_inflight_limited(self):
        issues = [self.issue(i, "open") for i in (1, 2)]
        self.assertFalse(gate(issues, {}, self.DAY)["due"])

    def test_same_livestream_has_distinct_windows(self):
        import json
        request = {
            "kind": "X_MICROCUT_REQUEST_V1",
            "account": "lucasyahn",
            "source": {"video_id": "live-123"},
            "scan_start": 600,
        }
        issue = {
            "title": "[X-MICROCUT] live-123-1",
            "number": 7,
            "state": "closed",
            "created_at": "2026-10-21T10:00:00Z",
            "body": "```json\n" + json.dumps(request) + "\n```",
        }
        result = gate([issue], {}, self.DAY)
        self.assertEqual(result["source_windows"], {"live-123": [600]})
        self.assertTrue(result["due"])

    @patch("tools.x_publication_safety.subprocess.run")
    def test_media_geometry_and_duration(self, run):
        import json
        run.return_value = SimpleNamespace(stdout=json.dumps({
            "streams": [{"codec_type": "video", "width": 1280, "height": 720}],
            "format": {"duration": "560.0"},
        }))
        self.assertEqual(validate_video("x.mp4")["duration"], 560.0)
        run.return_value = SimpleNamespace(stdout=json.dumps({
            "streams": [{"codec_type": "video", "width": 720, "height": 1280}],
            "format": {"duration": "560.0"},
        }))
        with self.assertRaisesRegex(ValueError, "16_9"):
            validate_video("x.mp4")


if __name__ == "__main__":
    unittest.main()
