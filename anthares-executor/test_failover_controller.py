import unittest
from failover_controller import FailoverController


class FakeClient:
    def __init__(self, healthy=True, identity=True, upload=True, heartbeat_ok=True):
        self.healthy = healthy
        self.identity = identity
        self.upload = upload
        self.heartbeat_ok = heartbeat_ok
        self.calls = []

    def health(self):
        self.calls.append("health")
        if not self.healthy:
            raise OSError("offline")
        return 200, {"ok": True, "chromium_ready": False, "encrypted_profile_store_configured": False}

    def accept_lease(self, *args):
        self.calls.append("lease")
        return 201, {"ok": True}

    def heartbeat(self, *args):
        self.calls.append("heartbeat")
        if self.heartbeat_ok:
            return 200, {"ok": True}
        return 409, {"error": "stale_lease"}

    def start_browser(self):
        self.calls.append("start")
        return 200, {"ok": True}

    def probe_kwai(self):
        self.calls.append("probe")
        return 200, {"ok": True, "identity_verified": self.identity, "upload_surface_verified": self.upload, "session_state": "authenticated_surface", "evidence": {"owner_edit": self.identity}}

    def stop_browser(self):
        self.calls.append("stop")
        return 200, {"ok": True}

    def complete(self, *args):
        self.calls.append("complete")
        return 200, {"ok": True}


class FailoverTests(unittest.TestCase):
    def test_selects_second_provider_when_first_is_offline(self):
        first, second = FakeClient(False), FakeClient(True)
        ctl = FailoverController([
            {"name": "primary", "priority": 1, "client": first},
            {"name": "reserve", "priority": 2, "client": second},
        ], cooldown=60)
        result = ctl.execute_readonly_kwai_probe("job", "z" * 32, 1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["executor"], "reserve")
        self.assertEqual(second.calls, ["health", "lease", "heartbeat", "start", "probe", "stop", "complete"])
        self.assertEqual(first.calls, ["health"])

    def test_probe_never_invokes_publication_method(self):
        client = FakeClient(True)
        ctl = FailoverController([{"name": "only", "priority": 1, "client": client}])
        result = ctl.execute_readonly_kwai_probe("job2", "y" * 32, 1)
        self.assertTrue(result["read_only"])
        self.assertNotIn("publish", client.calls)
        self.assertTrue(result["identity_verified"])
        self.assertTrue(result["upload_surface_verified"])

    def test_lost_heartbeat_fails_closed_before_browser_start(self):
        client = FakeClient(True, heartbeat_ok=False)
        ctl = FailoverController([{"name": "only", "priority": 1, "client": client}])
        result = ctl.execute_readonly_kwai_probe("job3", "x" * 32, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "lease_heartbeat_failed")
        self.assertNotIn("start", client.calls)
        self.assertIn("complete", client.calls)


if __name__ == "__main__":
    unittest.main()
