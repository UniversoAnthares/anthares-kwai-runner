import tempfile
import unittest
from pathlib import Path

from recovery import LeaseStore, acquire, choose_executor, retry_delay


class RecoveryTests(unittest.TestCase):
    def test_lease_heartbeat_takeover_and_store(self):
        lease = acquire(None, "runner-a", ttl_seconds=30, now=100)
        self.assertFalse(lease.expired(129))
        self.assertTrue(lease.expired(130))
        with self.assertRaises(RuntimeError):
            acquire(lease, "runner-b", ttl_seconds=30, now=120)
        takeover = acquire(lease, "runner-b", ttl_seconds=30, now=131)
        self.assertEqual(takeover.owner, "runner-b")
        self.assertEqual(takeover.generation, 2)
        with tempfile.TemporaryDirectory() as td:
            store = LeaseStore(Path(td) / "lease.json")
            store.write(takeover)
            self.assertEqual(store.read(), takeover)

    def test_retry_backoff_is_capped(self):
        self.assertEqual([retry_delay(i) for i in range(1, 5)], [5, 10, 20, 40])
        self.assertEqual(retry_delay(20), 300)

    def test_executor_failover_is_deterministic(self):
        candidates = [
            {"name": "primary", "priority": 10, "healthy": False},
            {"name": "secondary", "priority": 20, "healthy": True},
            {"name": "tertiary", "priority": 30, "healthy": True},
        ]
        self.assertEqual(choose_executor(candidates), "secondary")
        with self.assertRaises(RuntimeError):
            choose_executor([{"name": "dead", "healthy": False}])


if __name__ == "__main__":
    unittest.main()
