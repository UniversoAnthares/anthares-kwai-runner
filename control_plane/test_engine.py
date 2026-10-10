import unittest
from engine import evaluate

class ControlPlaneTests(unittest.TestCase):
    def test_empty_is_pending_or_blocked(self):
        s = evaluate([])
        self.assertEqual(s["remote_identity"]["status"], "pending")
        self.assertEqual(s["persistent_session"]["status"], "blocked")
    def test_unverified_dependency_cannot_be_bypassed(self):
        s = evaluate([{"task":"publish_proof","status":"verified",
          "source":"test","detail":"fake","observed_at":"2026-10-10T00:00:00Z"}])
        self.assertEqual(s["publish_proof"]["status"], "blocked")
    def test_complete_chain(self):
        rows = [{"task":task,"status":"verified","source":"test",
                 "detail":"validated","observed_at":"2026-10-10T00:00:00Z"}
                for task in ("remote_identity","persistent_session",
                             "publish_proof","unattended_runner")]
        self.assertTrue(all(v["status"] == "verified" for v in evaluate(rows).values()))
    def test_invalid_evidence(self):
        with self.assertRaises(ValueError):
            evaluate([{"task":"other","status":"verified","source":"x",
                       "observed_at":"2026-10-10T00:00:00Z"}])

if __name__ == "__main__":
    unittest.main()
