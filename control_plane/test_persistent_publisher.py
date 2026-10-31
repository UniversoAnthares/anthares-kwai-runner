import json
import tempfile
import unittest
from pathlib import Path

from persistent_publisher import (
    ManagedProfileProof,
    PublishReceipt,
    decode_managed_profiles,
    receipt_evidence,
    require_platforms,
    write_receipt,
)


def profile(platform, profile_id="prof_123"):
    return {
        "provider": "codespaces",
        "profile_id": profile_id,
        "platform": platform,
        "account_handle": "@anthares",
        "checked_at": "2026-10-10T20:00:00Z",
        "authenticated": True,
        "persistence_verified": True,
    }


class PersistentPublisherTests(unittest.TestCase):
    def test_managed_profiles_require_both_platforms(self):
        proofs = decode_managed_profiles(json.dumps({"profiles": [profile("tiktok"), profile("kwai", "prof_456")]}))
        selected = require_platforms(proofs, ("tiktok", "kwai"))
        self.assertEqual(set(selected), {"tiktok", "kwai"})

    def test_secret_fields_are_rejected(self):
        row = profile("tiktok")
        row["cookies"] = [{"name": "session"}]
        with self.assertRaisesRegex(RuntimeError, "sensitive_field_rejected"):
            ManagedProfileProof.from_mapping(row)

    def test_receipt_requires_real_verification_flags(self):
        with self.assertRaisesRegex(RuntimeError, "receipt_publication_unverified"):
            PublishReceipt.from_mapping({
                "platform": "tiktok",
                "provider": "codespaces",
                "profile_id": "prof_123",
                "account_handle": "@universo.anthares",
                "post_id": "123",
                "post_url": "https://www.tiktok.com/@universo.anthares/video/123",
                "published_at": "2026-10-10T20:00:00Z",
                "content_sha256": "a" * 64,
                "identity_verified": True,
                "publication_verified": False,
            })

    def test_receipt_is_public_metadata_and_becomes_platform_evidence(self):
        receipt = PublishReceipt.from_mapping({
            "platform": "kwai",
            "provider": "codespaces",
            "profile_id": "profile-kwai",
            "account_handle": "@lucasrosalem",
            "post_id": "kwai-1",
            "post_url": "https://www.kwai.com/@lucasrosalem/video/kwai-1",
            "published_at": "2026-10-10T20:00:00Z",
            "content_sha256": "b" * 64,
            "identity_verified": True,
            "publication_verified": True,
        })
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "kwai").mkdir()
            path = write_receipt(receipt, Path(tmp) / "kwai" / "receipt.json", actor_network="kwai", state_root=tmp)
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["receipt_id"], receipt.receipt_id)
        self.assertNotIn("cookies", saved)
        evidence = receipt_evidence(receipt)
        self.assertEqual(evidence["task"], "kwai_publish_proof")
        self.assertEqual(evidence["source"], receipt.post_url)


    def test_cross_network_paths_denied_for_both_networks(self):
        for owner, foreign in (("kwai", "tiktok"), ("tiktok", "kwai")):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / owner).mkdir()
                (root / foreign).mkdir()
                dest = root / foreign / "foreign.json"
                with self.assertRaisesRegex(RuntimeError, "cross_network_path_denied"):
                    write_receipt(self._receipt(owner), dest,
                                  actor_network=owner, state_root=root)
                self.assertFalse(dest.exists())

    def test_cross_network_receipt_identity_denied_in_both_directions(self):
        for actor, foreign in (("kwai", "tiktok"), ("tiktok", "kwai")):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / actor).mkdir()
                with self.assertRaisesRegex(RuntimeError, "cross_network_write_denied"):
                    write_receipt(self._receipt(foreign), root / actor / "foreign.json",
                                  actor_network=actor, state_root=root)

    def test_missing_explicit_scope_blocks_legacy_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "legacy.json"
            with self.assertRaises(TypeError):
                write_receipt(self._receipt("kwai"), target)
            self.assertFalse(target.exists())

    def test_traversal_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "kwai").mkdir()
            (root / "tiktok").mkdir()
            with self.assertRaisesRegex(RuntimeError, "cross_network_path_denied"):
                write_receipt(self._receipt("kwai"), root / "kwai" / ".." / "tiktok" / "x.json",
                              actor_network="kwai", state_root=root)
            self.assertFalse((root / "tiktok" / "x.json").exists())

    def test_network_directory_never_created_by_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(RuntimeError, "network_state_directory_missing"):
                write_receipt(self._receipt("kwai"), root / "kwai" / "x.json",
                              actor_network="kwai", state_root=root)
            self.assertFalse((root / "kwai").exists())

    def test_own_network_writes_succeed_for_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for network in ("kwai", "tiktok"):
                (root / network).mkdir()
                path = write_receipt(self._receipt(network), root / network / "receipt.json",
                                     actor_network=network, state_root=root)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["platform"], network)

    @staticmethod
    def _receipt(network):
        return PublishReceipt.from_mapping({
            "platform": network, "provider": "fixture", "profile_id": "owned",
            "account_handle": "@owner", "post_id": "synthetic-1",
            "post_url": "https://" + ("kwai.com" if network == "kwai" else "tiktok.com") + "/@owner/video/1",
            "published_at": "2026-10-24T00:00:00Z",
            "content_sha256": "a" * 64,
            "identity_verified": True, "publication_verified": True,
        })


if __name__ == "__main__":
    unittest.main()
