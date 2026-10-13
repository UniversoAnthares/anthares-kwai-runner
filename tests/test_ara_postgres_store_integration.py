import os
import pathlib
import sys
import unittest
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))

from ara_state_store import PostgresStore


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "TEST_DATABASE_URL not configured")
class PostgresStoreIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ["TEST_DATABASE_URL"]
        cls.prefix = "ci-" + uuid.uuid4().hex[:10]

    @classmethod
    def tearDownClass(cls):
        import psycopg
        with psycopg.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM ara_jobs WHERE device_id LIKE %s", (cls.prefix + "%",))
            cur.execute("DELETE FROM ara_devices WHERE device_id LIKE %s", (cls.prefix + "%",))
            conn.commit()

    def device(self, suffix):
        return f"{self.prefix}-{suffix}"

    def expire_lease(self, job_id):
        import psycopg
        with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("UPDATE ara_jobs SET lease_until=now()-interval '1 second' WHERE id=%s", (job_id,))
            conn.commit()

    def test_heartbeat_survives_store_recreation(self):
        device = self.device("heartbeat")
        first = PostgresStore(self.dsn)
        first.heartbeat(device, {"version": "0.3"})
        second = PostgresStore(self.dsn)
        status = second.status(device)
        self.assertTrue(status["connected"])
        self.assertEqual(status["heartbeat"]["version"], "0.3")

    def test_queued_job_survives_store_recreation(self):
        device = self.device("queued")
        first = PostgresStore(self.dsn)
        job = first.enqueue(device, "ping", {}, 30, idempotency_key="same")
        second = PostgresStore(self.dsn)
        loaded = second.get_job(device, job["id"])
        self.assertEqual(loaded["status"], "queued")
        duplicate = second.enqueue(device, "ping", {}, 30, idempotency_key="same")
        self.assertEqual(duplicate["id"], job["id"])

    def test_safe_expired_lease_is_recovered_after_store_recreation(self):
        device = self.device("lease")
        first = PostgresStore(self.dsn)
        job = first.enqueue(device, "ping", {}, 60)
        leased = first.lease_next(device, lease_seconds=35)
        self.assertEqual(leased["id"], job["id"])
        self.assertEqual(leased["attempts"], 1)
        self.expire_lease(job["id"])
        second = PostgresStore(self.dsn)
        recovered = second.lease_next(device, lease_seconds=35)
        self.assertEqual(recovered["id"], job["id"])
        self.assertEqual(recovered["attempts"], 2)

    def test_side_effect_expired_lease_is_uncertain_not_replayed(self):
        device = self.device("side-effect")
        first = PostgresStore(self.dsn)
        job = first.enqueue(device, "shell", {"command": "example"}, 60)
        leased = first.lease_next(device, lease_seconds=35)
        self.assertEqual(leased["attempts"], 1)
        self.expire_lease(job["id"])
        second = PostgresStore(self.dsn)
        self.assertIsNone(second.lease_next(device, lease_seconds=35))
        loaded = second.get_job(device, job["id"])
        self.assertEqual(loaded["status"], "uncertain")
        self.assertEqual(loaded["attempts"], 1)
        self.assertEqual(second.status(device)["uncertain"], 1)

    def test_late_result_reconciles_uncertain_side_effect(self):
        device = self.device("late-result")
        first = PostgresStore(self.dsn)
        job = first.enqueue(device, "shell", {"command": "example"}, 60)
        first.lease_next(device, lease_seconds=35)
        self.expire_lease(job["id"])
        second = PostgresStore(self.dsn)
        self.assertEqual(second.get_job(device, job["id"])["status"], "uncertain")
        done = second.complete(device, job["id"], {"ok": True, "output": "finished"})
        self.assertEqual(done["status"], "done")
        self.assertEqual(done["result"]["output"], "finished")

    def test_result_survives_store_recreation(self):
        device = self.device("result")
        first = PostgresStore(self.dsn)
        job = first.enqueue(device, "ping", {}, 30)
        first.lease_next(device)
        first.complete(device, job["id"], {"ok": True, "output": "pong"})
        second = PostgresStore(self.dsn)
        loaded = second.get_job(device, job["id"])
        self.assertEqual(loaded["status"], "done")
        self.assertEqual(loaded["result"]["output"], "pong")


if __name__ == "__main__":
    unittest.main()
