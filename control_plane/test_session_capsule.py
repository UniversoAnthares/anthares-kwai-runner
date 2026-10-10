import base64
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from session_capsule import decode_capsule, materialize_secret_capsule


def capsule(domain="tiktok.com", minutes=10):
    payload = {
        "domain": domain,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
        "storage_state": {"cookies": [], "origins": []},
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


class SessionCapsuleTests(unittest.TestCase):
    def test_valid_capsule(self):
        self.assertEqual(decode_capsule(capsule())["domain"], "tiktok.com")

    def test_rejects_wrong_domain(self):
        with self.assertRaises(RuntimeError):
            decode_capsule(capsule("example.com"))

    def test_rejects_expired(self):
        with self.assertRaises(RuntimeError):
            decode_capsule(capsule(minutes=-1))

    def test_materialize_then_remove(self):
        with materialize_secret_capsule(capsule()) as (path, meta):
            self.assertTrue(path.exists())
            self.assertEqual(meta["domain"], "tiktok.com")
            saved = path
        self.assertFalse(saved.exists())


if __name__ == "__main__":
    unittest.main()
