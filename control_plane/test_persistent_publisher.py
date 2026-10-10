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
            path = write_receipt(receipt, Path(tmp) / "receipt.json")
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["receipt_id"], receipt.receipt_id)
        self.assertNotIn("cookies", saved)
        evidence = receipt_evidence(receipt)
        self.assertEqual(evidence["task"], "kwai_publish_proof")
        self.assertEqual(evidence["source"], receipt.post_url)


if __name__ == "__main__":
    unittest.main()
