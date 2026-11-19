"""Offline contracts for pastoral queue; absolutely no network/send."""
import csv
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from pastor_mailing_queue import PastoralQueue, given_name


class PastorMailingTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.dir.name, "private", "queue.sqlite3")
        self.q = PastoralQueue(self.db)

    def tearDown(self):
        self.dir.cleanup()

    def test_initial_state_disarmed(self):
        state = self.q.status()
        self.assertEqual(state["contacts"], 0)
        self.assertIn("DISABLED", state["live_sending"])

    def test_directory_import_does_not_infer_consent(self):
        r=self.q.import_directory([
            ("Rev. João Silva", "Joao@example.org"),
            ("Pastor Ana Souza", "Ana@example.org"),
            ("Rev. João Silva", "JOAO@example.org"),
            ("Invalido", "not-an-email"),
            ("Sem Email", ""),
        ], "anuario-pastoral")
        self.assertEqual(r["created"], 2)
        self.assertEqual(r["repeated_in_import"], 1)
        self.assertEqual(r["invalid"], 2)
        self.assertEqual(self.q.status()["consented"], 0)
        self.assertEqual(self.q.plan("mailing_2026",100,3000)["dispatch_cap"],0)
        with self.q.connect() as c:
            name=c.execute("SELECT first_name FROM contacts WHERE email=?",
                           ("joao@example.org",)).fetchone()[0]
        self.assertEqual(name,"João")

    def test_names_extracted_only_first(self):
        self.assertEqual(given_name("Pr. José Fernandes"),"José")
        self.assertEqual(given_name("Rev. Carlos Batista"),"Carlos")
        self.assertEqual(given_name("Pastora Maria Isabel"),"Maria")

    def test_import_preserves_optin(self):
        self.q.import_directory([("Marina Silva","marina@example.org")],"directory")
        stamp=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
        self.q.add_consent("marina@example.org","double_opt_in","verified-web-token-123",stamp)
        self.q.import_directory([("Marina Nova","marina@example.org")],"directory")
        self.assertEqual(self.q.status()["consented"],1)
        self.assertEqual(self.q.plan("campaign-a", 100,3000)["dispatch_cap"],1)

    def test_consent_requires_evidence(self):
        self.q.import_directory([("Marco", "marco@example.org")],"directory")
        t=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.q.add_consent("marco@example.org","manual","yes",t)
        with self.assertRaises(ValueError):
            self.q.add_consent("marco@example.org","documented_prior_permission","",t)
        self.assertEqual(self.q.status()["consented"],0)

    def test_hard_bounce_and_unsubscribe_suppress(self):
        self.q.import_directory([("José","jose@example.org")],"directory")
        t=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        self.q.add_consent("jose@example.org","double_opt_in","verified-web-token-123",t)
        self.assertTrue(self.q.suppress("jose@example.org","hard_bounce","resend-event-100"))
        self.assertFalse(self.q.suppress("jose@example.org","hard_bounce","resend-event-100"))
        self.assertEqual(self.q.plan("campaign-a",100,3000)["dispatch_cap"],0)
        with self.assertRaises(PermissionError):
            self.q.record_attempt("jose@example.org","campaign-a",None,
                                  "ATTEMPTED_UNKNOWN","test-1000")
        with self.assertRaises(PermissionError):
            self.q.add_consent("jose@example.org","double_opt_in","verified-web-token-999",t)

    def test_soft_bounce_never_permanently_suppressed(self):
        with self.assertRaises(ValueError):
            self.q.suppress("jose@example.org","soft_bounce","smtp-451")

    def test_idempotent_inbound_uid(self):
        self.assertTrue(self.q.record_inbox_event("contato@anthares.us","512",
            "reply","pastor@example.org","RESPOSTA","2026-11-19T12:00:00Z"))
        self.assertFalse(self.q.record_inbox_event("contato@anthares.us","512",
            "reply","pastor@example.org","RESPOSTA","2026-11-19T12:00:00Z"))
        self.assertEqual(self.q.status()["inbox_processed"],1)

    def test_daily_quota_limit(self):
        self.q.import_directory([("Maria","maria@example.org")],"directory")
        t=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        self.q.add_consent("maria@example.org","documented_prior_permission",
                           "signed-archive-proof-444",t)
        self.assertEqual(self.q.plan("campaign-b",0,3000)["dispatch_cap"],0)
        self.assertEqual(self.q.plan("campaign-b",100,0)["dispatch_cap"],0)
        self.assertEqual(self.q.plan("campaign-b",99,2900)["dispatch_cap"],1)

    def test_prior_attempt_fences_campaign(self):
        self.q.import_directory([("Maria","maria@example.org")],"directory")
        t=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        self.q.add_consent("maria@example.org","documented_prior_permission",
                           "signed-archive-proof-444",t)
        self.q.record_attempt("maria@example.org","campaign-b",None,
                              "ATTEMPTED_UNKNOWN","campaign-b-maria")
        self.assertEqual(self.q.plan("campaign-b",100,3000)["dispatch_cap"],0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.q.record_attempt("maria@example.org","campaign-b",None,
                                  "ACCEPTED","campaign-b-maria")

    def test_eligible_count_disarmed(self):
        self.q.import_directory([("Maria","maria@example.org")],"directory")
        t=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        self.q.add_consent("maria@example.org","documented_prior_permission",
                           "signed-archive-proof-444",t)
        p=self.q.plan("campaign-b",100,3000)
        self.assertFalse(p["dispatch_enabled"])
        self.assertEqual(p["eligible"],1)
        self.assertEqual(p["dispatch_cap"],1)


if __name__ == "__main__":
    unittest.main()
