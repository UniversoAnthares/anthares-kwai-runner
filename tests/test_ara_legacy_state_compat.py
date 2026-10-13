import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))

from ara_legacy_state_compat import DevicesProxy
from ara_state_store import MemoryStore


class Relay:
    def __init__(self):
        self.store = MemoryStore()

    def _store(self):
        return self.store

    def get_job(self, device, job_id):
        return self.store.get_job(device, job_id)

    def device_status(self, device, freshness_seconds=45):
        return self.store.status(device, freshness_seconds)


class CompatTests(unittest.TestCase):
    def test_legacy_job_assignment_is_durable_store_enqueue(self):
        relay = Relay()
        devices = DevicesProxy(relay)
        state = devices.setdefault("PC", {"heartbeat": None, "queue": [], "jobs": {}})
        job = {"id": "abc", "type": "ping", "args": {}, "timeout_seconds": 15, "status": "queued"}
        state["jobs"]["abc"] = job
        state["queue"].append("abc")
        stored = relay.store.get_job("PC", "abc")
        self.assertEqual(stored["id"], "abc")
        self.assertEqual(stored["type"], "ping")
        self.assertEqual(stored["status"], "queued")

    def test_legacy_job_read_comes_from_store(self):
        relay = Relay()
        devices = DevicesProxy(relay)
        relay.store.enqueue("PC", "ping", {}, 15, job_id="xyz")
        state = devices.setdefault("PC", {})
        self.assertEqual(state["jobs"].get("xyz")["id"], "xyz")

    def test_heartbeat_read_comes_from_store(self):
        relay = Relay()
        devices = DevicesProxy(relay)
        relay.store.heartbeat("PC", {"version": "0.3"})
        state = devices.setdefault("PC", {})
        self.assertEqual(state.get("heartbeat")["version"], "0.3")


if __name__ == "__main__":
    unittest.main()
