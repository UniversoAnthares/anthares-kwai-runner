"""API contract tests: no real browser, network secrets or publication required."""
import importlib
import os
import tempfile
import time
import unittest

TOKEN = "test-only-token-0123456789abcdef"


class ExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["STATE_DB"] = cls.tmp.name + "/jobs.sqlite3"
        os.environ["CHROME_PROFILE_DIR"] = cls.tmp.name + "/profile"
        os.environ["ANTHARES_EXECUTOR_TOKEN"] = TOKEN
        os.environ["LEASE_TTL_SECONDS"] = "30"
        os.environ.pop("GITLAB_TOKEN", None)
        os.environ.pop("GITLAB_STATE_KEY", None)
        cls.module = importlib.import_module("executor")
        cls.module.db().close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.client = self.module.app.test_client()
        self.headers = {"Authorization": "Bearer " + TOKEN}
        with self.module.db() as conn:
            conn.execute("DELETE FROM jobs")

    def post(self, path, payload=None):
        return self.client.post(path, headers=self.headers, json=payload or {})

    def test_fail_closed_auth_and_public_health(self):
        self.assertEqual(self.client.post("/v1/jobs", json={}).status_code, 401)
        self.assertEqual(self.client.post("/v1/browser/start").status_code, 401)
        self.assertEqual(self.client.post("/v1/profile/restore").status_code, 401)
        self.assertEqual(self.client.post("/v1/kwai/probe").status_code, 401)
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertTrue(health.json["ok"])
        self.assertNotIn("token", health.get_data(as_text=True).lower())

    def test_lease_heartbeat_fencing_completion_and_recovery(self):
        lease = "a" * 32
        payload = {"id": "test-job", "lease": lease, "generation": 1}
        created = self.post("/v1/jobs", payload)
        self.assertEqual(created.status_code, 201)
        first_expiry = created.json["lease_expires"]

        again = self.post("/v1/jobs", payload)
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.json["idempotent"])

        beat = self.post("/v1/jobs/test-job/heartbeat", {"lease": lease, "generation": 1})
        self.assertEqual(beat.status_code, 200)
        self.assertGreaterEqual(beat.json["lease_expires"], first_expiry)

        other = {"id": "other-job", "lease": "b" * 32, "generation": 1}
        self.assertEqual(self.post("/v1/jobs", other).status_code, 409)
        wrong = {"lease": "b" * 32, "generation": 1, "result": {"ok": True}}
        self.assertEqual(self.post("/v1/jobs/test-job/complete", wrong).status_code, 409)
        good = {"lease": lease, "generation": 1, "result": {"ok": True}}
        self.assertEqual(self.post("/v1/jobs/test-job/complete", good).status_code, 200)
        self.assertEqual(self.client.get("/v1/jobs/test-job", headers=self.headers).json["result"], {"ok": True})
        self.assertEqual(self.post("/v1/jobs", other).status_code, 201)
        self.assertEqual(self.post("/v1/jobs", {**payload, "generation": 2}).status_code, 409)

    def test_expired_job_requires_higher_generation_and_can_be_reacquired(self):
        lease1 = "c" * 32
        lease2 = "d" * 32
        payload = {"id": "recoverable", "lease": lease1, "generation": 7}
        self.assertEqual(self.post("/v1/jobs", payload).status_code, 201)
        with self.module.db() as conn:
            conn.execute("UPDATE jobs SET lease_expires=? WHERE id=?", (time.time() - 1, "recoverable"))
        stale = self.post("/v1/jobs/recoverable/heartbeat", {"lease": lease1, "generation": 7})
        self.assertEqual(stale.status_code, 409)
        same_generation = self.post("/v1/jobs", {"id": "recoverable", "lease": lease2, "generation": 7})
        self.assertEqual(same_generation.status_code, 409)
        reacquired = self.post("/v1/jobs", {"id": "recoverable", "lease": lease2, "generation": 8})
        self.assertEqual(reacquired.status_code, 200)
        self.assertTrue(reacquired.json["reacquired"])

    def test_profile_store_fails_closed_when_not_configured(self):
        response = self.post("/v1/profile/restore")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["reason"], "not_configured")

    def test_kwai_probe_requires_running_browser(self):
        response = self.post("/v1/kwai/probe")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["error"], "browser_not_ready")


if __name__ == "__main__":
    unittest.main()
