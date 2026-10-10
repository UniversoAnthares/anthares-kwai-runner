import tempfile
import unittest

from persistence_probe import observe_restart, profile_dir


class PersistenceProbeTests(unittest.TestCase):
    def test_first_observation_is_not_restart_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = observe_restart(
                "tiktok", root=tmp, boot_id="boot-a", observed_at="2026-10-10T20:00:00+00:00"
            )
            self.assertFalse(state["persistence_verified"])
            self.assertEqual(state["restart_count"], 0)

    def test_same_boot_does_not_claim_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            observe_restart("kwai", root=tmp, boot_id="boot-a")
            state = observe_restart("kwai", root=tmp, boot_id="boot-a")
            self.assertFalse(state["persistence_verified"])
            self.assertEqual(state["restart_count"], 0)

    def test_changed_boot_proves_persistent_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            observe_restart("tiktok", root=tmp, boot_id="boot-a")
            state = observe_restart("tiktok", root=tmp, boot_id="boot-b")
            self.assertTrue(state["persistence_verified"])
            self.assertEqual(state["restart_count"], 1)
            self.assertIn("browser-profiles", state["profile_dir"])

    def test_platform_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "platform_invalid"):
                profile_dir("other", tmp)


if __name__ == "__main__":
    unittest.main()
