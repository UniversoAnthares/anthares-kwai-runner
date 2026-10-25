"""ISO-02: actual disposable filesystem positive/negative network-path gate.

Runs against the code in PR #1332, not an imitation of its validator.
No real publisher, provider credentials, queue state or user files are used.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "control_plane"))
from persistent_publisher import PublishReceipt, write_receipt


def receipt(network):
    host = {"kwai":"kwai.com", "tiktok":"tiktok.com"}[network]
    return PublishReceipt.from_mapping({
        "platform":network,
        "provider":"iso02-test-only",
        "profile_id":"isolated-fixture",
        "account_handle":"@qa",
        "post_id":"isolated-receipt",
        "post_url":f"https://{host}/@qa/video/1234",
        "published_at":"2026-10-25T00:00:00Z",
        "content_sha256":"a" * 64,
        "identity_verified":True,
        "publication_verified":True,
    })


class RealNetworkPathGateQA(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="anthares-iso02-real-path-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.kwai=self.root/"kwai"
        self.tiktok=self.root/"tiktok"
        self.kwai.mkdir()
        self.tiktok.mkdir()

    def writes(self, network, target=None, actor=None, state_root=None):
        return write_receipt(
            receipt(network), target or self.root/network/"receipt.json",
            actor_network=actor or network, state_root=state_root or self.root)

    def test_authorized_own_network_real_write_and_readback(self):
        for network in ("kwai","tiktok"):
            with self.subTest(network=network):
                target=self.writes(network)
                self.assertTrue(target.is_file())
                payload=json.loads(target.read_text(encoding="utf-8"))
                self.assertEqual(payload["platform"],network)
                self.assertEqual(payload["receipt_id"],receipt(network).receipt_id)

    def test_foreign_network_target_denied_both_directions(self):
        for network,foreign in (("kwai","tiktok"),("tiktok","kwai")):
            with self.subTest(actor=network):
                path=self.root/foreign/"foreign.json"
                with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
                    self.writes(network,path)
                self.assertFalse(path.exists())

    def test_forged_actor_network_denied_both_directions(self):
        for owner,foreign in (("kwai","tiktok"),("tiktok","kwai")):
            with self.subTest(actor=foreign,receipt=owner):
                path=self.root/foreign/"foreign.json"
                with self.assertRaisesRegex(RuntimeError,"cross_network_write_denied"):
                    self.writes(owner,path,actor=foreign)
                self.assertFalse(path.exists())

    def test_move_name_cannot_retarget_followup_write_to_other_network(self):
        initial=self.writes("kwai")
        renamed=self.kwai/"renamed.json"
        initial.rename(renamed)
        self.assertTrue(renamed.exists())
        external=self.tiktok/"renamed.json"
        with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
            self.writes("kwai",external)
        self.assertFalse(external.exists())

    def test_directory_symlink_to_foreign_network_denied(self):
        alias=self.root/"kwai_alias"
        try:
            alias.symlink_to(self.tiktok,target_is_directory=True)
        except (OSError,NotImplementedError) as exc:
            self.skipTest(f"symlink unprivileged on this host: {type(exc).__name__}")
        target=alias/"foreign.json"
        with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
            self.writes("kwai",target)
        self.assertFalse((self.tiktok/"foreign.json").exists())

    def test_target_symlink_to_other_network_file_is_rejected(self):
        foreign=self.tiktok/"foreign.json"
        foreign.write_text("FOREIGN_UNCHANGED",encoding="utf-8")
        link=self.kwai/"receipt.json"
        try:
            link.symlink_to(foreign)
        except (OSError,NotImplementedError) as exc:
            self.skipTest(f"symlink unprivileged on this host: {type(exc).__name__}")
        with self.assertRaises(RuntimeError):
            self.writes("kwai",link)
        self.assertEqual(foreign.read_text(encoding="utf-8"),"FOREIGN_UNCHANGED")

    def test_root_symlink_denied_even_when_real_target_owned(self):
        alias=self.root.parent/(self.root.name+"-alias")
        try:
            alias.symlink_to(self.root,target_is_directory=True)
        except (OSError,NotImplementedError) as exc:
            self.skipTest(f"symlink unprivileged on this host: {type(exc).__name__}")
        self.addCleanup(alias.unlink)
        with self.assertRaisesRegex(RuntimeError,"state_root_invalid"):
            self.writes("kwai",self.kwai/"new.json",state_root=alias)
        self.assertFalse((self.kwai/"new.json").exists())

    def test_sibling_prefix_collision_is_denied(self):
        sibling=self.root/"kwai-old"
        sibling.mkdir()
        with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
            self.writes("kwai",sibling/"looks-owned.json")
        self.assertFalse((sibling/"looks-owned.json").exists())

    def test_non_json_extension_denied(self):
        with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
            self.writes("tiktok",self.tiktok/"receipt.txt")
        self.assertFalse((self.tiktok/"receipt.txt").exists())

    def test_legacy_unscoped_entrypoint_does_not_write(self):
        target=self.kwai/"unscoped.json"
        with self.assertRaises(TypeError):
            write_receipt(receipt("kwai"),target)
        self.assertFalse(target.exists())

    def test_traversal_path_rejected_before_creating_artifacts(self):
        escaped=self.kwai/".."/"tiktok"/"outside.json"
        with self.assertRaisesRegex(RuntimeError,"cross_network_path_denied"):
            self.writes("kwai",escaped)
        self.assertFalse((self.tiktok/"outside.json").exists())

    def test_existing_directory_as_target_denied(self):
        nested=self.kwai/"receipt.json"
        nested.mkdir()
        with self.assertRaisesRegex(RuntimeError,"state_target_invalid"):
            self.writes("kwai",nested)
        self.assertTrue(nested.is_dir())


if __name__=="__main__":
    unittest.main()
