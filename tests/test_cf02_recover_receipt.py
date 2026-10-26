"""Offline gates for historical CF02 receipt recovery. Never touches providers."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import unittest
import urllib.request

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "cf02_recover_receipt.py"
spec = importlib.util.spec_from_file_location("cf02_receipt_recovery", SCRIPT)
cf02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf02)


def fixture():
    run = {"id": cf02.SOURCE_RUN_ID, "head_sha": cf02.SOURCE_HEAD_SHA,
           "event": "workflow_dispatch", "status": "completed",
           "conclusion": "failure", "path": cf02.WORKFLOW_PATH,
           "updated_at": "2026-10-26T07:03:00Z"}
    success = [{"name": x, "conclusion": "success"} for x in cf02.REQUIRED_STEPS]
    job = {"id": 121441273566, "name": "deploy", "conclusion": "failure",
           "steps": success + [{"name": cf02.FAIL_RECEIPT_STEP, "conclusion": "failure"}]}
    logs = "\n".join("2026-10-26T07:02:41.000Z " + s for s in [
        "WRANGLER_DEPLOY_OK=1",
        "CORTES_LEGACY_CLEANUP_REMOVED=0",
        "CORTES_LEGACY_CLEANUP_PROTECTED=6",
        "CONTROL_HEALTH_OK=1"]) + "\n2026-10-26T07:02:43.000Z urllib.error.HTTPError: HTTP Error 409: Conflict"
    return run, [job], logs


class RecoveryEvidenceTests(unittest.TestCase):
    def test_original_run_is_a_real_successful_deploy_with_failed_receipt(self):
        run, jobs, logs = fixture()
        actual = cf02.verify_original(run, jobs, logs)
        self.assertEqual(actual["removed_count"], 0)
        self.assertEqual(actual["protected_count_at_source"], 6)
        self.assertEqual(actual["source_job_id"], 121441273566)

    def test_cannot_invent_deploy_on_failed_step(self):
        run, jobs, logs = fixture()
        jobs[0]["steps"][0]["conclusion"] = "failure"
        with self.assertRaisesRegex(RuntimeError, "original_step_unverified"):
            cf02.verify_original(run, jobs, logs)

    def test_cannot_count_echoed_script_as_real_log(self):
        run, jobs, logs = fixture()
        logs = logs.replace("T07:02:41.000Z WRANGLER_DEPLOY_OK=1",
                            "T07:02:41.000Z echo 'WRANGLER_DEPLOY_OK=1'")
        with self.assertRaisesRegex(RuntimeError, "original_log_marker_missing"):
            cf02.verify_original(run, jobs, logs)

    def test_cannot_use_wrong_source_sha(self):
        run, jobs, logs = fixture()
        run["head_sha"] = "0" * 40
        with self.assertRaisesRegex(RuntimeError, "unexpected_original_source_sha"):
            cf02.verify_original(run, jobs, logs)

    def test_controller_health_requires_prod_bindings(self):
        base = {"ok": True, "service": "anthares-control",
                "version": "2026-10-17-physical-android-v18",
                "persistent_state": True, "queue_bound": True,
                "pc_fallback": False}
        self.assertEqual(cf02.verify_live_health(base), base)
        for bad in ({"queue_bound": False}, {"persistent_state": False},
                    {"pc_fallback": True}, {"ok": False}):
            with self.assertRaises(RuntimeError):
                cf02.verify_live_health({**base, **bad})

    def test_prior_receipt_guard_disallows_newer_production_record(self):
        source = "2026-10-26T07:03:00Z"
        old = {"checked_at_utc": "2026-10-19T23:45:51.943051+00:00"}
        self.assertEqual(cf02.safe_prior_receipt(json.dumps(old), source), "older")
        newer = {"checked_at_utc": "2026-10-26T09:12:00+00:00"}
        with self.assertRaisesRegex(RuntimeError, "newer_production_receipt_exists"):
            cf02.safe_prior_receipt(json.dumps(newer), source)
        already = {"checked_at_utc": "2026-10-26T09:12:00+00:00",
                   "source_workflow_run_id": cf02.SOURCE_RUN_ID}
        self.assertEqual(cf02.safe_prior_receipt(json.dumps(already), source), "same_source")

    def test_github_token_never_forwards_to_signed_redirect_host(self):
        req = urllib.request.Request(
            "https://api.github.com/repos/org/repo/actions/jobs/123/logs",
            headers={"Authorization": "Bearer TEMP-TEST-TOKEN",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        cross = cf02.SafeRedirect().redirect_request(
            req, None, 302, "Found", {},
            "https://log-storage.example.net/container/log.txt?sig=SIGNED")
        self.assertIsNotNone(cross)
        self.assertIsNone(cross.get_header("Authorization"))
        self.assertIsNone(cross.get_header("X-GitHub-Api-Version"))
        self.assertNotIn("TEMP-TEST-TOKEN", repr(cross.headers))
        same = cf02.SafeRedirect().redirect_request(
            req, None, 302, "Found", {},
            "https://api.github.com/repos/org/repo/actions/jobs/123/logs-next")
        self.assertEqual(same.get_header("Authorization"), "Bearer TEMP-TEST-TOKEN")

    def test_receipt_run_is_pinned_and_contains_no_live_queue_mutation(self):
        text = SCRIPT.read_text("utf8")
        self.assertIn("SOURCE_RUN_ID = 40283336472", text)
        self.assertIn("cloudflare_deploy_in_recovery", text)
        self.assertIn("queue_mutation_in_recovery", text)
        self.assertNotIn("cleanup-legacy-kwai", text)
        self.assertNotIn("wrangler deploy", text)


if __name__ == "__main__":
    unittest.main()
