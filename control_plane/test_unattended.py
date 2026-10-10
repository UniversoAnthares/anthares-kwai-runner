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


def profiles():
    return json.dumps({"profiles": [
        {
            "provider": "codespaces",
            "profile_id": "tiktok-profile",
            "platform": "tiktok",
            "account_handle": "@universo.anthares",
            "checked_at": "2026-10-10T20:00:00Z",
            "authenticated": True,
            "persistence_verified": True,
        },
        {
            "provider": "codespaces",
            "profile_id": "kwai-profile",
            "platform": "kwai",
            "account_handle": "@lucasrosalem",
            "checked_at": "2026-10-10T20:00:00Z",
            "authenticated": True,
            "persistence_verified": True,
        },
    ]})


class UnattendedTests(unittest.TestCase):
    def test_missing_authentication_blocks(self):
        state = readiness(executors=[{"name": "gh", "priority": 1, "healthy": True}])
        self.assertFalse(state["ready"])
        self.assertIn("authentication_proof_missing", state["blockers"])

    def test_managed_profiles_are_primary_and_ready(self):
        state = readiness(
            managed_profiles_value=profiles(),
            session_value=capsule(),
            executors=[{"name": "codespace", "priority": 1, "healthy": True}],
        )
        self.assertTrue(state["ready"])
        self.assertEqual(state["executor"], "codespace")
        self.assertEqual(state["auth_mode"], "managed_profiles")
        self.assertEqual(state["authenticated_platforms"], ["kwai", "tiktok"])

    def test_single_platform_capsule_is_valid_fallback_for_single_target(self):
        state = readiness(
            session_value=capsule(),
            executors=[{"name": "gh", "priority": 1, "healthy": True}],
            required_platforms=("kwai",),
        )
        self.assertTrue(state["ready"])
        self.assertEqual(state["auth_mode"], "session_capsule")
        self.assertEqual(state["session_domain"], "kwai.com")

    def test_single_capsule_cannot_claim_two_platforms(self):
        state = readiness(
            session_value=capsule(),
            executors=[{"name": "gh", "priority": 1, "healthy": True}],
        )
        self.assertFalse(state["ready"])
        self.assertIn("session_capsule_missing_platforms:tiktok", state["blockers"])

    def test_dead_executor_blocks(self):
        state = readiness(
            managed_profiles_value=profiles(),
            executors=[{"name": "codespace", "priority": 1, "healthy": False}],
        )
        self.assertFalse(state["ready"])
        self.assertIn("no_healthy_executor", state["blockers"])


if __name__ == "__main__":
    unittest.main()
