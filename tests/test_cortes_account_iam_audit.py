import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "audit", ROOT / "ci-hub" / "cortes_account_iam_audit.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def manifest():
    return json.loads((ROOT / "ci-hub" / "cortes_tiktok_lucas4_ownership.json")
                      .read_text(encoding="utf-8"))

def workflow():
    return """permissions:
  contents: read
  id-token: write
concurrency:
  group: cortes-tiktok-lucasrosalem4-account
jobs:
  check:
    environment: cortes-tiktok-lucas4
    env:
      STATE: secrets.CORTES_TIKTOK_LUCAS4_STORAGE_STATE
"""

class TestAccountBoundary(unittest.TestCase):
    def test_allow_shadow_configuration_without_deploy(self):
        report = m.inspect_workflow(manifest(), workflow(), m.WORKFLOWS[0])
        self.assertEqual(report["status"], "SHADOW_CONTRACT_VALID")
        self.assertFalse(report["deploy_authorized"])

    def test_cross_network_actor_denied_both_directions(self):
        for network, account in (("kwai", "lucasrosalem4"), ("tiktok", "lucasrosalem")):
            with self.assertRaisesRegex(m.BoundaryDenied, "cross_network_identity_denied"):
                m.assert_actor(manifest(), network, account, m.WORKFLOWS[0])

    def test_unlisted_workflow_denied(self):
        with self.assertRaisesRegex(m.BoundaryDenied, "foreign_workflow_denied"):
            m.assert_actor(manifest(), "tiktok", "lucasrosalem4", "kwai-publish.yml")

    def test_kwai_secret_denied(self):
        bad = workflow() + "      KWAI: secrets.KWAI_PASSWORD\n"
        with self.assertRaisesRegex(m.BoundaryDenied, "foreign_or_missing_secret_denied"):
            m.inspect_workflow(manifest(), bad, m.WORKFLOWS[0])

    def test_shared_deploy_token_denied(self):
        bad = workflow() + "      SHARED: secrets.CODEBERG_PUSH_URL\n"
        with self.assertRaisesRegex(m.BoundaryDenied, "foreign_or_missing_secret_denied"):
            m.inspect_workflow(manifest(), bad, m.WORKFLOWS[0])

    def test_actions_write_denied(self):
        bad = workflow() + "  actions: write\n"
        with self.assertRaisesRegex(m.BoundaryDenied, "excessive_workflow_permission_denied"):
            m.inspect_workflow(manifest(), bad, m.WORKFLOWS[0])

    def test_missing_oidc_denied(self):
        with self.assertRaisesRegex(m.BoundaryDenied, "signed_oidc_capability_required"):
            m.inspect_workflow(manifest(), workflow().replace("id-token: write", "id-token: none"), m.WORKFLOWS[0])

    def test_missing_environment_blocks_without_promotion(self):
        check = m.inspect_workflow(manifest(), workflow().replace(
            "environment: cortes-tiktok-lucas4", ""), m.WORKFLOWS[0])
        self.assertEqual(check["status"], "BLOCKED_ACCOUNT_ENVIRONMENT_NOT_BOUND")

    def test_manifest_cannot_claim_iam_success(self):
        n = manifest()
        n["secret_scope_verified"] = True
        with self.assertRaisesRegex(m.BoundaryDenied, "self_attested_authority_denied"):
            m.validate_manifest(n)

    def test_queue_swap_denied(self):
        n = manifest()
        n["queue_table"] = "cortes_kwai"
        with self.assertRaisesRegex(m.BoundaryDenied, "account_binding_invalid"):
            m.validate_manifest(n)

    def test_legacy_repository_secret_denied(self):
        bad = workflow().replace("secrets.CORTES_TIKTOK_LUCAS4_STORAGE_STATE",
                                 "secrets.TIKTOK_LUCASROSALEM4_STORAGE_STATE")
        with self.assertRaisesRegex(m.BoundaryDenied, "foreign_or_missing_secret_denied"):
            m.inspect_workflow(manifest(), bad, m.WORKFLOWS[0])

    def test_runtime_alias_mismatch_denied(self):
        n = manifest()
        n["runtime_variable"] = "KWAI_STORAGE_STATE"
        with self.assertRaisesRegex(m.BoundaryDenied, "account_binding_invalid"):
            m.validate_manifest(n)

    def test_native_baseline_stays_shadow_without_provider_iam(self):
        report = m.audit(ROOT, manifest())
        self.assertEqual(report["status"], "SHADOW_CONTRACT_VALID")
        self.assertFalse(report["provider_iam_verified"])
        self.assertFalse(report["deploy_authorized"])

if __name__ == "__main__":
    unittest.main()
