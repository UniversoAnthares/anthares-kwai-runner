import base64
import json
import unittest
from datetime import datetime, timedelta, timezone

from unattended import readiness


def capsule(domain="kwai.com"):
    raw = {
        "domain": domain,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "storage_state": {"cookies": [], "origins": []},
    }
    return base64.b64encode(json.dumps(raw).encode("utf-8")).decode("ascii")


class UnattendedTests(unittest.TestCase):
    def test_missing_session_blocks(self):
        state = readiness(session_value=None, executors=[{"name": "gh", "priority": 1, "healthy": True}])
        self.assertFalse(state["ready"])
        self.assertIn("session_capsule_missing", state["blockers"])

    def test_valid_session_and_executor_are_ready(self):
        state = readiness(session_value=capsule(), executors=[{"name": "gh", "priority": 1, "healthy": True}])
        self.assertTrue(state["ready"])
        self.assertEqual(state["executor"], "gh")
        self.assertEqual(state["session_domain"], "kwai.com")

    def test_dead_executor_blocks(self):
        state = readiness(session_value=capsule(), executors=[{"name": "gh", "priority": 1, "healthy": False}])
        self.assertFalse(state["ready"])
        self.assertIn("no_healthy_executor", state["blockers"])


if __name__ == "__main__":
    unittest.main()
