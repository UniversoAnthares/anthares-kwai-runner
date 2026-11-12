"""QA do gate somente de leitura para CORTES-ISO-07."""
import unittest
from qa.iso07.preflight import inspect, OWNERSHIP_GATES, ATTESTATION_GATES, REQUIRED_TABLES

CLOUD = """jobs:
  publisher:
    environment: cortes-tiktok-lucas4
    env:
      STATE: ${{ secrets.TIKTOK_LUCASROSALEM4_STORAGE_STATE }}
"""
FALLBACK = """jobs:
  windows_backup:
    environment: cortes-tiktok-lucas4
    env:
      STATE: ${{ secrets.TIKTOK_LUCASROSALEM4_STORAGE_STATE }}
"""


def approved():
    own = {"network": "tiktok", "account": "lucasrosalem4"}
    own.update({k: True for k in OWNERSHIP_GATES})
    database = {
        "production_principal_bypassrls": False,
        "tables": {t: {"rls_enabled": True, "force_rls": True, "policies": 1}
                   for t in REQUIRED_TABLES},
    }
    external = {k: True for k in ATTESTATION_GATES}
    return own, database, external


class AdmissionTest(unittest.TestCase):
    def test_empty_evidence_fails_closed(self):
        r = inspect("", "", {}, {}, {})
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r["authorized_to_publish"])
        self.assertGreaterEqual(len(r["blocked_gates"]), 12)

    def test_workflow_environment_required(self):
        own, db, ext = approved()
        report = inspect(CLOUD.replace("environment: cortes-tiktok-lucas4", ""), FALLBACK, own, db, ext)
        self.assertIn("cloud_environment_unbound", report["blocked_gates"])

    def test_cross_network_secret_reference_fails(self):
        own, db, ext = approved()
        r = inspect(CLOUD + "\n      KWAI_PASSWORD: something", FALLBACK, own, db, ext)
        self.assertTrue(any("foreign_secret_reference" in x for x in r["blocked_gates"]))

    def test_no_owner_identity_swap(self):
        own, db, ext = approved()
        own["network"] = "kwai"
        self.assertIn("owner_network_account_mismatch",
                      inspect(CLOUD, FALLBACK, own, db, ext)["blocked_gates"])

    def test_rls_disabled_is_blocking(self):
        own, db, ext = approved()
        db["tables"]["cortes_publications"]["rls_enabled"] = False
        self.assertIn("database_cortes_publications_rls_enabled_unverified",
                      inspect(CLOUD, FALLBACK, own, db, ext)["blocked_gates"])

    def test_owner_bypassrls_is_blocking(self):
        own, db, ext = approved()
        db["production_principal_bypassrls"] = True
        self.assertIn("database_production_principal_nobypassrls_unverified",
                      inspect(CLOUD, FALLBACK, own, db, ext)["blocked_gates"])

    def test_missing_negative_principals_is_blocking(self):
        own, db, ext = approved()
        ext["cross_network_denied_both_directions"] = False
        self.assertIn("external_cross_network_denied_both_directions_unverified",
                      inspect(CLOUD, FALLBACK, own, db, ext)["blocked_gates"])

    def test_all_claims_only_request_review_not_publish(self):
        own, db, ext = approved()
        r = inspect(CLOUD, FALLBACK, own, db, ext)
        self.assertEqual(r["status"], "REVIEW_REQUIRED")
        self.assertEqual(r["blocked_gates"], [])
        self.assertFalse(r["authorized_to_publish"])
        self.assertTrue(r["claims_are_untrusted"])

    def test_unexpected_json_types_fail_closed(self):
        r = inspect(CLOUD, FALLBACK, ["tiktok"], ["bad"], ["fake"])
        self.assertEqual(r["status"], "BLOCKED")

    def test_policy_count_boolean_does_not_pass(self):
        own, db, ext = approved()
        db["tables"]["cortes_publications"]["policies"] = True
        r = inspect(CLOUD, FALLBACK, own, db, ext)
        self.assertIn("database_cortes_publications_policy_missing", r["blocked_gates"])


if __name__ == "__main__":
    unittest.main()
