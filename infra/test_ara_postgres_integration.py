import hashlib
import importlib
import os
import unittest

os.environ.setdefault("ARA_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ara_test")
os.environ.setdefault("ANTHARES_REMOTE_CONTROL_TOKEN", "control-test-token")
os.environ.setdefault("ARA_LEASE_SECONDS", "30")
DEVICE = "TEST-DEVICE"
DEVICE_TOKEN = "device-test-token"
os.environ.setdefault(
    "ARA_DEVICE_HASH_TEST_DEVICE", hashlib.sha256(DEVICE_TOKEN.encode()).hexdigest()
)

import ara_postgres_store as store
import ara_postgres_app as application


class AraPostgresIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        store.initialize()
        cls.client = application.app.test_client()

    def setUp(self):
        with store.connection() as conn:
            conn.execute("DELETE FROM ara_jobs WHERE device_id=%s", (DEVICE,))
            conn.execute("DELETE FROM ara_devices WHERE device_id=%s", (DEVICE,))

    def control_headers(self, extra=None):
        headers = {"Authorization": "Bearer control-test-token"}
        if extra:
            headers.update(extra)
        return headers

    def device_headers(self):
        return {
            "Authorization": f"Bearer {DEVICE_TOKEN}",
            "X-Anthares-Device": DEVICE,
        }

    def create_job(self, key="job-key-1"):
        response = self.client.post(
            "/v1/control/jobs",
            headers=self.control_headers({"Idempotency-Key": key}),
            json={"device_id": DEVICE, "type": "ping", "args": {}, "timeout_seconds": 30},
        )
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        return response.get_json()["job"]

    def test_full_persistent_contract(self):
        heartbeat = self.client.post(
            "/v1/device/heartbeat",
            headers=self.device_headers(),
            json={"version": "test"},
        )
        self.assertEqual(heartbeat.status_code, 200)

        created = self.create_job()
        duplicate_create = self.client.post(
            "/v1/control/jobs",
            headers=self.control_headers({"Idempotency-Key": "job-key-1"}),
            json={"device_id": DEVICE, "type": "ping", "args": {}, "timeout_seconds": 30},
        )
        self.assertEqual(duplicate_create.status_code, 200)
        self.assertFalse(duplicate_create.get_json()["created"])
        self.assertEqual(duplicate_create.get_json()["job"]["id"], created["id"])

        leased = self.client.get("/v1/device/jobs/next", headers=self.device_headers())
        self.assertEqual(leased.status_code, 200)
        self.assertEqual(leased.get_json()["job"]["id"], created["id"])
        self.assertEqual(leased.get_json()["job"]["status"], "leased")

        result = {"id": created["id"], "ok": True, "output": "pong"}
        stored = self.client.post(
            f"/v1/device/jobs/{created['id']}/result",
            headers=self.device_headers(),
            json=result,
        )
        self.assertEqual(stored.status_code, 200)
        self.assertFalse(stored.get_json()["duplicate"])

        duplicate_result = self.client.post(
            f"/v1/device/jobs/{created['id']}/result",
            headers=self.device_headers(),
            json=result,
        )
        self.assertEqual(duplicate_result.status_code, 200)
        self.assertTrue(duplicate_result.get_json()["duplicate"])

        conflicting_result = self.client.post(
            f"/v1/device/jobs/{created['id']}/result",
            headers=self.device_headers(),
            json={"id": created["id"], "ok": False, "error": "different"},
        )
        self.assertEqual(conflicting_result.status_code, 409)

        fetched = self.client.get(
            f"/v1/control/jobs/{created['id']}?device_id={DEVICE}",
            headers=self.control_headers(),
        )
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["job"]["status"], "done")
        self.assertEqual(fetched.get_json()["job"]["result"]["output"], "pong")

        importlib.reload(store)
        recovered_after_reload = store.get_job(DEVICE, created["id"])
        self.assertEqual(recovered_after_reload["status"], "done")
        self.assertEqual(recovered_after_reload["result"]["output"], "pong")

    def test_expired_lease_is_recovered(self):
        created = self.create_job("lease-recovery")
        leased = self.client.get("/v1/device/jobs/next", headers=self.device_headers())
        self.assertEqual(leased.status_code, 200)
        self.assertEqual(leased.get_json()["job"]["id"], created["id"])
        with store.connection() as conn:
            conn.execute(
                "UPDATE ara_jobs SET lease_until=now() - interval '1 second' WHERE id=%s",
                (created["id"],),
            )
        recovered = self.client.get("/v1/device/jobs/next", headers=self.device_headers())
        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.get_json()["job"]["id"], created["id"])
        self.assertEqual(recovered.get_json()["job"]["status"], "leased")

    def test_transactional_selftest_rolls_back(self):
        before = None
        with store.connection() as conn:
            before = conn.execute("SELECT count(*) AS n FROM ara_jobs").fetchone()["n"]
        result = store.transactional_selftest()
        self.assertTrue(result["ok"])
        self.assertTrue(all(result["checks"].values()))
        with store.connection() as conn:
            after = conn.execute("SELECT count(*) AS n FROM ara_jobs").fetchone()["n"]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
