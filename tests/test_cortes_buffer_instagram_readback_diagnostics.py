"""AOI16: safe diagnostics for previously scheduled Instagram Buffer posts."""
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from social_adapters.buffer_three_channels import BufferBlocked
from tools import cortes_buffer_instagram_cloud as ig


def post(remote_id, state="scheduled", link=None, *, channel=None, scheduling="automatic"):
    return {"post": {
        "id": remote_id, "status": state, "externalLink": link,
        "channelId": channel or ig.INSTAGRAM_ID,
        "schedulingType": scheduling,
    }}


class InstagramBufferReadbackDiagnostics(unittest.TestCase):
    def test_allowlisted_pending_and_failed_states_never_confirm(self):
        states = ("scheduled", "pending", "queued", "failed", "error",
                  "rejected", "cancelled", "canceled", "draft")
        for state in states:
            with self.subTest(state=state), patch.object(ig, "api", return_value=post("buffer-one", state)):
                self.assertEqual(ig.inspect_buffer_post("buffer-one"), (state, None))

    def test_null_post_is_explicit_missing_without_reconciliation(self):
        with patch.object(ig, "api", return_value={"post": None}):
            self.assertEqual(ig.inspect_buffer_post("buffer-one"), ("missing", None))
            with self.assertRaisesRegex(RuntimeError, "IDENTITY_UNVERIFIED"):
                ig.verify_sent_post("buffer-one")

    def test_unrecognized_provider_text_is_sanitized(self):
        with patch.object(ig, "api", return_value=post("buffer-one", "leaked_secret=private")):
            self.assertEqual(ig.inspect_buffer_post("buffer-one"), ("other", None))

    def test_verified_sent_link_is_preserved(self):
        link = "https://www.instagram.com/reel/ABC123_-/"
        with patch.object(ig, "api", return_value=post("buffer-one", "sent", link)):
            self.assertEqual(ig.inspect_buffer_post("buffer-one"), ("sent", link))
            self.assertEqual(ig.verify_sent_post("buffer-one"), link)

    def test_identity_scheduling_and_link_guards_fail_closed(self):
        invalid = (
            post("another-id"),
            post("buffer-one", channel="wrong-channel"),
            post("buffer-one", scheduling="manual"),
            post("buffer-one", state="sent", link="https://evil.example/reel/ABC/"),
            post("buffer-one", state="sent", link="https://instagram.com/other/ABC/"),
        )
        for row in invalid:
            with self.subTest(row=row), patch.object(ig, "api", return_value=row):
                with self.assertRaises(RuntimeError):
                    ig.inspect_buffer_post("buffer-one")

    def test_three_pending_records_report_state_and_only_verified_sent_reconciles(self):
        jobs = [
            {"id": "cortes-fanout-instagram-000000000001", "remote_id": "buffer-1"},
            {"id": "cortes-fanout-instagram-000000000002", "remote_id": "buffer-2"},
            {"id": "cortes-fanout-instagram-000000000003", "remote_id": "buffer-3"},
        ]
        remote = {
            "buffer-1": post("buffer-1", "sent", "https://instagram.com/reel/abc123/"),
            "buffer-2": post("buffer-2", "scheduled"),
            "buffer-3": {"post": None},
        }
        queue_calls = []
        def queue(action, payload=None):
            queue_calls.append((action, payload))
            if action == "pending":
                return {"jobs": jobs}
            if action == "reconcile":
                return {"ok": True}
            raise AssertionError("unexpected queue action " + action)
        def api(query):
            return next(value for key, value in remote.items() if json.dumps(key) in query)
        out = io.StringIO()
        with (patch.object(ig, "queue", side_effect=queue),
              patch.object(ig, "api", side_effect=api),
              patch.object(ig, "publish_once") as publisher,
              patch.object(ig, "schedule") as schedule,
              redirect_stdout(out)):
            self.assertEqual(ig.reconcile(), 1)
        events = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([e["state"] for e in events], ["sent", "scheduled", "missing"])
        self.assertEqual([e["neon_confirmed"] for e in events], [True, False, False])
        self.assertEqual(len([action for action, _ in queue_calls if action == "reconcile"]), 1)
        self.assertEqual([action for action, _ in queue_calls], ["pending", "reconcile"])
        self.assertEqual({e["record_ref"] for e in events},
                         {"000000000001", "000000000002", "000000000003"})
        self.assertTrue(all(e["new_posts"] == 0 for e in events))
        self.assertNotIn("https://instagram.com", out.getvalue())
        self.assertNotIn("buffer-1", out.getvalue())
        schedule.assert_not_called()
        publisher.assert_not_called()

    def test_reconcile_only_main_cannot_publish_even_if_buffer_is_scheduled(self):
        actions = []
        def queue(action, payload=None):
            actions.append(action)
            if action == "cooldown-status": return {"active": False}
            if action == "pending":
                return {"jobs": [{"id": "cortes-000000000004", "remote_id": "buffer-4"}]}
            raise AssertionError("unexpected write action: " + action)
        out = io.StringIO()
        with (patch.dict(os.environ, {"CORTES_RECONCILE_ONLY": "1"}),
              patch.object(ig, "cloud_only"),
              patch.object(ig, "queue", side_effect=queue),
              patch.object(ig, "api", return_value=post("buffer-4", "scheduled")),
              patch.object(ig, "publish_once") as publisher,
              patch.object(ig, "schedule") as schedule,
              redirect_stdout(out)):
            self.assertEqual(ig.main(), 0)
        self.assertEqual(actions, ["cooldown-status", "pending"])
        self.assertIn('"new_posts": 0', out.getvalue())
        publisher.assert_not_called()
        schedule.assert_not_called()

    def test_workflow_is_paused_by_default_and_readback_cannot_create_posts(self):
        from pathlib import Path
        workflow=(Path(__file__).resolve().parents[1] /
                  ".github/workflows/cortes-buffer-instagram-cloud.yml").read_text()
        self.assertIn("vars.CORTES_INSTAGRAM_BUFFER_PAUSED == 'false'", workflow)
        self.assertIn("inputs.reconcile_only == true", workflow)
        self.assertIn("ANTHARES_SOCIAL_COMMIT: ${{ inputs.reconcile_only == true && '0' || '1' }}", workflow)
        self.assertIn("CORTES_RECONCILE_ONLY: ${{ inputs.reconcile_only && '1' || '0' }}", workflow)

    def test_buffer_error_message_is_classified_without_disclosing_text(self):
        message="It looks like Buffer has lost authorization to post to this account"
        row=post("buffer-1", "error")
        row["post"]["error"]={"message": message}
        with patch.object(ig, "api", return_value=row):
            self.assertEqual(ig.inspect_buffer_post("buffer-1"),
                             ("error", None))
            self.assertEqual(ig.inspect_buffer_post("buffer-1",include_error=True),
                             ("error", None, "ACCOUNT_AUTH_OR_PERMISSION"))
        self.assertEqual(ig.classify_buffer_publish_error("unknown private details"),
                         "OTHER_PROVIDER_ERROR")

    def test_reconcile_logs_cause_code_without_provider_message(self):
        message="Your media URL could not be downloaded: private-file.mp4"
        row=post("buffer-2", "error")
        row["post"]["error"]={"message": message}
        def queue(action, payload=None):
            if action=="pending":
                return {"jobs":[{"id":"cortes-fanout-instagram-123456789abc",
                                 "remote_id":"buffer-2"}]}
            raise AssertionError("unexpected queue mutation")
        out=io.StringIO()
        with (patch.object(ig,"queue",side_effect=queue),
              patch.object(ig,"api",return_value=row),
              redirect_stdout(out)):
            self.assertEqual(ig.reconcile(),0)
        self.assertIn('"error_category": "MEDIA_SOURCE_UNAVAILABLE"',out.getvalue())
        self.assertNotIn(message,out.getvalue())

    def test_regular_run_schedules_at_most_one_media_item(self):
        with (patch.dict(os.environ, {"CORTES_RECONCILE_ONLY": "0"}),
              patch.object(ig, "cloud_only"),
              patch.object(ig, "queue", side_effect=lambda action: (
                  {"active": False} if action == "cooldown-status"
                  else {"enabled": True, "remaining": 20} if action == "policy"
                  else (_ for _ in ()).throw(AssertionError(action)))),
              patch.object(ig, "reconcile", return_value=0),
              patch.object(ig, "publish_once", return_value="SCHEDULED_IN_BUFFER") as publisher,
              redirect_stdout(io.StringIO())):
            self.assertEqual(ig.main(), 0)
            publisher.assert_called_once()

    def test_only_schedule_and_manual_dispatch_trigger_instagram_workflow(self):
        from pathlib import Path
        workflow=(Path(__file__).resolve().parents[1] /
                  ".github/workflows/cortes-buffer-instagram-cloud.yml").read_text()
        self.assertNotIn("\\n  push:\\n", workflow)
        self.assertNotIn("AOI16_BUFFER_ERROR_CAUSE_ONCE", workflow)
        self.assertIn("cron: '8 */3 * * *'", workflow)
        self.assertIn("vars.CORTES_INSTAGRAM_BUFFER_PAUSED == 'false'", workflow)

    def test_uncertain_provider_response_stops_without_reconcile_write(self):
        actions = []
        def queue(action, payload=None):
            actions.append(action)
            if action == "pending":
                return {"jobs": [{"id": "cortes-000000000005", "remote_id": "buffer-5"}]}
            raise AssertionError("unexpected mutation")
        with (patch.object(ig, "queue", side_effect=queue),
              patch.object(ig, "api", side_effect=BufferBlocked("BUFFER_RESPONSE_UNCERTAIN"))):
            with self.assertRaises(BufferBlocked):
                ig.reconcile()
        self.assertEqual(actions, ["pending"])


if __name__ == "__main__":
    unittest.main()
