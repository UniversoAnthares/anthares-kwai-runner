"""Offline checks for Brevo contact suppressions and private operator commands."""
from __future__ import annotations

import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from brevo_marketing import BrevoMarketing
from brevo_operations import (
    SuppressionLedger, pull_brevo_suppressions, safe_campaign_report,
    safe_status, main,
)


class FakeBrevo:
    def __init__(self):
        self.calls = []
        self.contacts = [
            {"email": "bad@example.org", "emailBlacklisted": True,
             "listUnsubscribed": [], "listIds": [2]},
            {"email": "out@example.org", "emailBlacklisted": False,
             "listUnsubscribed": [2], "listIds": [2]},
            {"email": "good@example.org", "emailBlacklisted": False,
             "listUnsubscribed": [], "listIds": [2]},
        ]
        self.malformed = False

    def __call__(self, method, path, body):
        self.calls.append((method, path))
        if method != "GET":
            raise AssertionError("operator used mutating HTTP verb")
        if path.startswith("/contacts?"):
            offset = int(path.split("offset=")[1])
            rows = self.contacts[offset:offset + 500]
            if self.malformed and rows:
                rows = [{**rows[0], "emailBlacklisted": "false"}] + rows[1:]
            return {"count": len(self.contacts), "contacts": rows}
        if path == "/account":
            return {"email": "secret@example.org"}
        if path.startswith("/contacts/lists"):
            return {"count": 1, "lists": [{"id": 2, "totalSubscribers": 3}]}
        if path.startswith("/emailCampaigns?"):
            return {"count": 0, "campaigns": []}
        if path.startswith("/emailCampaigns/"):
            return {"id": 123, "status": "sent", "htmlContent": "<b>private</b>",
                    "sender": {"email": "private@example.org"},
                    "testSent": True,
                    "statistics": {"globalStats": {"sent": 10, "delivered": 9,
                                                  "unsubscriptions": 1,
                                                  "private": "never-export"}}}
        raise AssertionError("unexpected path " + path)


class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.temp.name, "suppressions.sqlite3")
        self.ledger = SuppressionLedger(self.db)
        self.transport = FakeBrevo()
        self.client = BrevoMarketing(transport=self.transport)

    def tearDown(self):
        self.temp.cleanup()

    def test_live_lookup_requires_fresh_complete_sync(self):
        with self.assertRaises(PermissionError):
            self.ledger.fresh_lookup()
        pull_brevo_suppressions(self.client, self.ledger)
        check = self.ledger.fresh_lookup()
        self.assertTrue(check("bad@example.org"))
        self.assertFalse(check("good@example.org"))
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE brevo_sync_runs SET checked_at='2020-01-01T00:00:00+00:00'")
        with self.assertRaises(PermissionError):
            self.ledger.fresh_lookup()

    def test_unavailable_unsubscribe_metadata_prevents_live_lookup(self):
        self.transport.contacts[0].pop("listUnsubscribed")
        pull_brevo_suppressions(self.client, self.ledger)
        with self.assertRaises(PermissionError):
            self.ledger.fresh_lookup()

    def test_pull_records_blacklists_and_unsubscribes(self):
        result = pull_brevo_suppressions(self.client, self.ledger)
        self.assertEqual(result["contacts_checked"], 3)
        self.assertEqual(result["suppressed_seen"], 2)
        self.assertEqual(result["missing_list_status"], 0)
        self.assertTrue(self.ledger.is_suppressed("BAD@example.org"))
        self.assertTrue(self.ledger.is_suppressed("out@example.org"))
        self.assertFalse(self.ledger.is_suppressed("good@example.org"))
        self.assertTrue(all(method == "GET" for method, _ in self.transport.calls))
        self.assertEqual(oct(os.stat(self.db).st_mode & 0o777), "0o600")

    def test_suppression_is_sticky_when_remote_changes(self):
        pull_brevo_suppressions(self.client, self.ledger)
        self.transport.contacts = []
        pull_brevo_suppressions(self.client, self.ledger)
        self.assertEqual(self.ledger.count(), 2)

    def test_failed_pagination_never_partially_updates(self):
        self.transport.malformed = True
        with self.assertRaises(RuntimeError):
            pull_brevo_suppressions(self.client, self.ledger)
        self.assertEqual(self.ledger.count(), 0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM brevo_sync_runs").fetchone()[0], 0)

    def test_optional_unsubscribe_field_reported(self):
        self.transport.contacts[2].pop("listUnsubscribed")
        result = pull_brevo_suppressions(self.client, self.ledger)
        self.assertEqual(result["missing_list_status"], 1)

    def test_report_has_aggregates_only(self):
        result = safe_campaign_report(self.client, 123)
        self.assertEqual(result["statistics"]["delivered"], 9)
        self.assertTrue(result["test_sent"])
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("secret@example.org", json.dumps(result))

    def test_status_summarizes_without_contacts(self):
        result = safe_status(self.client, self.ledger)
        self.assertEqual(result["lists"][0]["id"], 2)
        self.assertEqual(result["mailing"], "approval_required")
        self.assertFalse(result["sending_enabled"])
        self.assertNotIn("secret@example.org", json.dumps(result))

    def test_cli_rejects_all_write_switches(self):
        with tempfile.NamedTemporaryFile(mode="w", dir=self.temp.name) as key:
            key.write("xkeysib-" + "1" * 60)
            key.flush()
            os.chmod(key.name, 0o600)
            buf = io.StringIO()
            with patch.dict(os.environ, {"BREVO_TEST_SEND_ENABLED": "1"}):
                with redirect_stdout(buf):
                    result = main(["--key-file", key.name, "--db", self.db, "status"])
        self.assertEqual(result, 3)
        self.assertIn("write_gate_enabled", buf.getvalue())

    def test_empty_account_is_valid(self):
        self.transport.contacts = []
        result = pull_brevo_suppressions(self.client, self.ledger)
        self.assertEqual(result["contacts_checked"], 0)
        self.assertEqual(result["sticky_suppressions"], 0)


if __name__ == "__main__":
    unittest.main()
