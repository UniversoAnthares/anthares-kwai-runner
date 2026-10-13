"""API contract tests: no browser or remote credentials required."""
import importlib
import os
import tempfile
import unittest

class ExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["STATE_DB"] = cls.tmp.name + "/jobs.sqlite3"
        os.environ["ANTHARES_EXECUTOR_TOKEN"] = "test-only-token"
        cls.module = importlib.import_module("executor")
        cls.module.db().close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.client = self.module.app.test_client()
        self.headers = {"Authorization": "Bearer test-only-token"}
        with self.module.db() as c:
            c.execute("DELETE FROM jobs")

    def test_fail_closed_auth(self):
        self.assertEqual(self.client.post("/v1/jobs", json={}).status_code, 401)
        self.assertEqual(self.client.post("/v1/browser/start").status_code, 401)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_lease_idempotence_fencing_completion_and_recovery(self):
        lease = "a" * 32
        payload = {"id": "test-job", "lease": lease, "generation": 1}
        self.assertEqual(self.client.post("/v1/jobs", headers=self.headers, json=payload).status_code, 201)
        again = self.client.post("/v1/jobs", headers=self.headers, json=payload)
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.json["idempotent"])
        other = {"id": "other-job", "lease": "b" * 32, "generation": 1}
        self.assertEqual(self.client.post("/v1/jobs", headers=self.headers, json=other).status_code, 409)
        wrong = {"lease": "b" * 32, "generation": 1, "result": {"ok": True}}
        self.assertEqual(self.client.post("/v1/jobs/test-job/complete", headers=self.headers, json=wrong).status_code, 409)
        good = {"lease": lease, "generation": 1, "result": {"ok": True}}
        self.assertEqual(self.client.post("/v1/jobs/test-job/complete", headers=self.headers, json=good).status_code, 200)
        self.assertEqual(self.client.get("/v1/jobs/test-job", headers=self.headers).json["result"], {"ok": True})
        self.assertEqual(self.client.post("/v1/jobs", headers=self.headers, json=other).status_code, 201)
        self.assertEqual(self.client.post("/v1/jobs", headers=self.headers, json={**payload, "generation": 2}).status_code, 409)

if __name__ == "__main__":
    unittest.main()
