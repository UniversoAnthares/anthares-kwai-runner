"""Offline synthetic tests: never use Kwai credentials, cookies, or Android."""
import json
import tempfile
import unittest
from pathlib import Path

import kwai_chrome_session_probe as probe


class ChromeSessionSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = (probe.CACHE, probe.ENC, probe.STATE, probe.SECRET)
        probe.CACHE = Path(self.tmp.name)
        probe.ENC = probe.CACHE / "kwai-session.enc"
        probe.STATE = probe.CACHE / "storage-state.json"
        probe.SECRET = "synthetic-test-key-only-" + "A" * 48
        self.state = {
            "cookies": [{"name": "synthetic_only", "value": "not_a_real_cookie", "domain": "example.org", "path": "/"}],
            "origins": [{"origin": "https://example.org", "localStorage": [{"name": "test", "value": "synthetic"}]}],
        }

    def tearDown(self):
        probe.CACHE, probe.ENC, probe.STATE, probe.SECRET = self.original
        self.tmp.cleanup()

    def test_round_trip_without_plaintext_file(self):
        output = {}
        probe.persist_state(output, self.state)
        self.assertTrue(output["encrypted_session_written"])
        self.assertTrue(probe.ENC.is_file())
        self.assertFalse(probe.STATE.exists())
        self.assertNotIn(b"not_a_real_cookie", probe.ENC.read_bytes())
        restored = {}
        self.assertEqual(probe.restore_state(restored), self.state)
        self.assertTrue(restored["session_restored"])
        self.assertFalse(probe.STATE.exists())

    def test_tampering_rejected_closed(self):
        probe.persist_state({}, self.state)
        ciphertext = bytearray(probe.ENC.read_bytes())
        ciphertext[len(ciphertext) // 2] ^= 1
        probe.ENC.write_bytes(ciphertext)
        result = {}
        self.assertIsNone(probe.restore_state(result))
        self.assertFalse(result["session_restored"])
        self.assertEqual(result["session_restore_error"], "InvalidToken")
        self.assertFalse(probe.STATE.exists())

    def test_wrong_key_rejected_closed(self):
        probe.persist_state({}, self.state)
        probe.SECRET = "different-synthetic-key-" + "B" * 48
        result = {}
        self.assertIsNone(probe.restore_state(result))
        self.assertFalse(result["session_restored"])
        self.assertEqual(result["session_restore_error"], "InvalidToken")

    def test_missing_key_cannot_persist(self):
        probe.SECRET = ""
        result = {}
        probe.persist_state(result, self.state)
        self.assertFalse(probe.ENC.exists())
        self.assertFalse(result.get("encrypted_session_written", False))
        self.assertIsNone(probe.restore_state(result))
        self.assertFalse(result["session_key_present"])

    def test_invalid_state_refused(self):
        with self.assertRaises(ValueError):
            probe.persist_state({}, {"cookies": "not-a-list", "origins": []})
        self.assertFalse(probe.ENC.exists())

    def test_legacy_plaintext_deleted(self):
        probe.STATE.write_text(json.dumps(self.state))
        self.assertTrue(probe.STATE.exists())
        probe.restore_state({})
        self.assertFalse(probe.STATE.exists())

    def test_workflow_caches_ciphertext_file_only(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/kwai-chrome-session-probe.yml").read_text()
        self.assertEqual(workflow.count("path: .kwai-session-cache/kwai-session.enc"), 2)
        self.assertNotIn("path: .kwai-session-cache\\n", workflow)
        self.assertIn("kwai-encrypted-session-v2-${{ github.run_id }}", workflow)
        self.assertIn("kwai-encrypted-session-v2-", workflow)
        self.assertNotIn("key: kwai-session-", workflow)


if __name__ == "__main__":
    unittest.main()
