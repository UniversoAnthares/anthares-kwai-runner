import unittest
from infra.ara_state_store import MemoryStore

class Clock:
    def __init__(self, t=1000.0): self.t=t
    def now(self): return self.t
    def add(self, s): self.t += s

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock()
        self.s=MemoryStore(self.clock.now)

    def test_heartbeat_freshness(self):
        self.s.heartbeat("pc", {"pid": 7})
        self.assertTrue(self.s.status("pc", 45)["connected"])
        self.clock.add(46)
        self.assertFalse(self.s.status("pc", 45)["connected"])

    def test_idempotent_enqueue(self):
        a=self.s.enqueue("pc","ping",idempotency_key="same")
        b=self.s.enqueue("pc","ping",idempotency_key="same")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(self.s.status("pc")["queued"], 1)

    def test_safe_lease_recovery(self):
        job=self.s.enqueue("pc","ping",timeout_seconds=120)
        first=self.s.lease_next("pc", lease_seconds=10)
        self.assertEqual(first["id"], job["id"])
        self.clock.add(11)
        second=self.s.lease_next("pc", lease_seconds=10)
        self.assertEqual(second["id"], job["id"])
        self.assertEqual(second["attempts"], 2)

    def test_side_effect_lease_becomes_uncertain_not_replayed(self):
        job=self.s.enqueue("pc","shell",{"command":"example"},timeout_seconds=120)
        leased=self.s.lease_next("pc", lease_seconds=10)
        self.assertEqual(leased["id"], job["id"])
        self.clock.add(11)
        self.assertIsNone(self.s.lease_next("pc", lease_seconds=10))
        state=self.s.get_job("pc",job["id"])
        self.assertEqual(state["status"], "uncertain")
        self.assertEqual(state["attempts"], 1)
        self.assertEqual(self.s.status("pc")["uncertain"], 1)

    def test_late_result_reconciles_uncertain_side_effect(self):
        job=self.s.enqueue("pc","shell",{"command":"example"},timeout_seconds=120)
        self.s.lease_next("pc", lease_seconds=10)
        self.clock.add(11)
        self.assertEqual(self.s.get_job("pc",job["id"])["status"], "uncertain")
        done=self.s.complete("pc",job["id"],{"ok":True,"output":"finished"})
        self.assertEqual(done["status"], "done")
        self.assertEqual(done["result"]["output"], "finished")

    def test_expired_job_is_not_released(self):
        job=self.s.enqueue("pc","ping",timeout_seconds=1)
        self.clock.add(32)
        self.assertIsNone(self.s.lease_next("pc"))
        self.assertEqual(self.s.get_job("pc",job["id"])["status"], "expired")

    def test_duplicate_result_is_idempotent(self):
        job=self.s.enqueue("pc","ping")
        self.s.lease_next("pc")
        a=self.s.complete("pc",job["id"],{"ok":True,"output":"pong"})
        b=self.s.complete("pc",job["id"],{"ok":False,"error":"late"})
        self.assertEqual(a["status"], "done")
        self.assertEqual(b["status"], "done")
        self.assertEqual(b["result"]["output"], "pong")

    def test_concurrent_queue_order(self):
        ids=[self.s.enqueue("pc","ping")["id"] for _ in range(5)]
        leased=[self.s.lease_next("pc")["id"] for _ in range(5)]
        self.assertEqual(ids, leased)
        self.assertEqual(len(set(leased)), 5)

if __name__=="__main__":
    unittest.main()
