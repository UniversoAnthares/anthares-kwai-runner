"""No-network Sender marketing adapter and durable ledger contract tests."""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch

from sender_marketing import SenderMarketing, SenderDraft
from sender_campaign_ledger import SenderCampaignLedger


def example_draft(**changes):
    fields = dict(
        local_id="anthares-test-2026", name="Teste de marketing",
        subject="Material de estudo", sender_name="Universo Anthares",
        reply_to="contato@anthares.us", group_id="grp123",
        html='<html><body><p>Comunicado de teste.</p><a href="{$unsubscribe_link}">Sair</a></body></html>',
    )
    fields.update(changes)
    return SenderDraft(**fields)


class FakeSender:
    def __init__(self):
        self.calls = []
        spec = example_draft()
        self.campaign = {
            "id": "camp123", "status": "DRAFT", "subject": spec.subject,
            "from": spec.sender_name, "reply_to": spec.reply_to,
            "campaign_groups": ["grp123"], "segments": [],
            "send_to_all": 0, "auto_followup_active": False,
            "html": {"html_content": spec.html},
        }
        self.contacts = [
            {"email": "alfa@example.org", "status": {"email": "active"},
             "unsubscribed_at": None, "bounced_at": None},
            {"email": "beta@example.org", "status": {"email": "unsubscribed"},
             "unsubscribed_at": "2026-11-18", "bounced_at": None},
        ]
        self.error_post = False

    def __call__(self, method, path, body):
        self.calls.append((method, path, body))
        if method == "GET" and path.startswith("/groups/grp123/subscribers?page="):
            return {"data": self.contacts, "meta": {"total": len(self.contacts), "current_page": 1},
                    "links": {"next": None}}
        if method == "GET" and path == "/groups":
            return {"data": [{"id": "grp123", "name": "Teste"}]}
        if method == "GET" and path.startswith("/campaigns?"):
            return {"data": [], "meta": {"total": 0}}
        if method == "GET" and path == "/campaigns/camp123":
            return {"data": self.campaign}
        if method == "POST" and self.error_post:
            raise ConnectionError("simulated provider request/response lost")
        if method == "POST" and path == "/campaigns":
            return {"success": True, "data": {"id": "camp123", "status": "DRAFT"}}
        if method == "POST" and path == "/campaigns/camp123/send":
            return {"success": True, "message": "Campaign started to send"}
        raise RuntimeError("unexpected API operation: " + path)


class SenderMarketingTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSender()
        self.client = SenderMarketing(transport=self.fake, suppression_lookup=lambda email: False)

    def test_payload_follows_official_sender_campaign_v2(self):
        payload = example_draft().payload()
        self.assertEqual(payload["groups"], ["grp123"])
        self.assertEqual(payload["segments"], [])
        self.assertEqual(payload["content_type"], "html")
        self.assertFalse(payload["auto_followup_active"])
        self.assertEqual(payload["reply_to"], "contato@anthares.us")
        self.assertIn("{$unsubscribe_link}", payload["content"])

    def test_reject_missing_unsubscribe_and_unsafe_group(self):
        for change in [
            {"html": "<p>Conteudo promocional sem descadastro</p>"},
            {"group_id": "../../secrets"},
            {"local_id": "x"},
            {"reply_to": "wrong-email"},
            {"subject": "  "},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                example_draft(**change).payload()

    def test_campaign_and_groups_read_only(self):
        self.client.groups()
        self.client.campaigns()
        self.client.campaign("camp123")
        self.assertTrue(all(method == "GET" for method, _, _ in self.fake.calls))
        self.assertEqual(self.fake.calls[1][1], "/campaigns?limit=20&status=DRAFT")
        with self.assertRaises(ValueError):
            self.client.campaigns("DELETE")

    def test_audience_excludes_unsubscribed(self):
        snap = self.client.audience_snapshot("grp123")
        self.assertEqual(snap["count"], 1)
        self.assertEqual(len(snap["digest"]), 64)
        self.assertEqual(snap["group_id"], "grp123")

    def test_audience_changes_invalidate_digest(self):
        first = self.client.audience_snapshot("grp123")
        self.fake.contacts[1] = {
            "email": "gamma@example.org", "status": {"email": "active"},
            "unsubscribed_at": None, "bounced_at": None,
        }
        self.assertNotEqual(first["digest"], self.client.audience_snapshot("grp123")["digest"])

    def test_missing_status_blocks_approval(self):
        self.fake.contacts[0].pop("status")
        with self.assertRaises(RuntimeError):
            self.client.audience_snapshot("grp123")

    def test_global_suppression_blocks_active_recipient(self):
        client = SenderMarketing(transport=self.fake,
                                 suppression_lookup=lambda x: x == "alfa@example.org")
        with self.assertRaises(PermissionError):
            client.audience_snapshot("grp123")

    def test_draft_creation_requires_switch(self):
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.client.create_draft(example_draft())
        self.assertEqual(self.fake.calls, [])
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "1"}):
            self.assertEqual(self.client.create_draft(example_draft()), "camp123")
        self.assertEqual(self.fake.calls[-1][1], "/campaigns")

    def test_send_gate_blocks_without_provider_call(self):
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.client.send_approved("camp123", approved_subject=example_draft().subject,
                    approved_remote_content_hash="0" * 64, approved_group_id="grp123",
                    approved_audience_digest="0" * 64,
                    content_approval="content-ref", audience_approval="audience-ref")
        self.assertEqual(self.fake.calls, [])

    def test_send_requires_global_suppression_source(self):
        client = SenderMarketing(transport=self.fake)
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                client.send_approved("camp123", approved_subject=example_draft().subject,
                    approved_remote_content_hash="0" * 64, approved_group_id="grp123",
                    approved_audience_digest="0" * 64,
                    content_approval="content-ref", audience_approval="audience-ref")
        self.assertEqual(self.fake.calls, [])

    def _approvals(self):
        return dict(
            approved_subject=example_draft().subject,
            approved_remote_content_hash=hashlib.sha256(
                example_draft().html.encode("utf-8")).hexdigest(),
            approved_group_id="grp123",
            approved_audience_digest=self.client.audience_snapshot("grp123")["digest"],
            content_approval="content-owner-approved",
            audience_approval="recipients-owner-approved",
        )

    def test_send_rejects_modified_remote_content(self):
        kwargs = self._approvals()
        self.fake.campaign["html"]["html_content"] = "<p>Alterado</p>"
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.send_approved("camp123", **kwargs)
        self.assertFalse(any(path.endswith("/send") for _, path, _ in self.fake.calls))

    def test_send_rejects_changed_group(self):
        kwargs = self._approvals()
        self.fake.campaign["campaign_groups"] = ["grp999"]
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.send_approved("camp123", **kwargs)

    def test_send_once_when_all_gates_approved_in_simulation(self):
        kwargs = self._approvals()
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            self.client.send_approved("camp123", **kwargs)
        self.assertEqual(sum(path.endswith("/send") for _, path, _ in self.fake.calls), 1)


class SenderLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = SenderCampaignLedger(os.path.join(self.temp.name, "sender.sqlite3"))
        self.fake = FakeSender()
        self.client = SenderMarketing(transport=self.fake, suppression_lookup=lambda _: False)

    def tearDown(self):
        self.temp.cleanup()

    def _draft(self):
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "1"}):
            return self.ledger.create_remote_draft(example_draft(), self.client)

    def test_staging_persists_and_is_immutable(self):
        self.ledger.stage(example_draft())
        self.assertEqual(SenderCampaignLedger(self.ledger.db_path).get(
            "anthares-test-2026")["state"], "STAGED")
        with self.assertRaises(ValueError):
            self.ledger.stage(example_draft(subject="Modified"))

    def test_no_remote_write_without_gate(self):
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.ledger.create_remote_draft(example_draft(), self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "STAGED")
        self.assertEqual(self.fake.calls, [])

    def test_draft_created_once(self):
        self.assertEqual(self._draft(), "camp123")
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "REMOTE_DRAFT")
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "1"}):
            with self.assertRaises(RuntimeError):
                self.ledger.create_remote_draft(example_draft(), self.client)
        self.assertEqual(len([x for x in self.fake.calls if x[0] == "POST"]), 1)

    def test_ambiguous_draft_response_never_replayed(self):
        self.fake.error_post = True
        with patch.dict(os.environ, {"SENDER_DRAFT_WRITE_ENABLED": "1"}):
            with self.assertRaises(ConnectionError):
                self.ledger.create_remote_draft(example_draft(), self.client)
            with self.assertRaises(RuntimeError):
                self.ledger.create_remote_draft(example_draft(), self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "RECONCILE_REQUIRED")
        self.assertEqual(sum(x[0] == "POST" for x in self.fake.calls), 1)

    def test_dispatch_requires_two_approvals(self):
        self._draft()
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.ledger.dispatch("anthares-test-2026", self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "REMOTE_DRAFT")

    def test_no_dispatch_if_gate_disabled_after_approvals(self):
        self._draft()
        self.ledger.record_content_approval("anthares-test-2026", "owner-confirmed", self.client)
        self.ledger.record_recipient_approval("anthares-test-2026", "owner-audience", self.client)
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.ledger.dispatch("anthares-test-2026", self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "REMOTE_DRAFT")

    def test_simulated_dispatch_once(self):
        self._draft()
        self.ledger.record_content_approval("anthares-test-2026", "owner-confirmed", self.client)
        self.ledger.record_recipient_approval("anthares-test-2026", "owner-audience", self.client)
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            self.ledger.dispatch("anthares-test-2026", self.client)
            with self.assertRaises(PermissionError):
                self.ledger.dispatch("anthares-test-2026", self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "SENT_PENDING_REPORT")
        self.assertEqual(sum(path.endswith("/send") for _, path, _ in self.fake.calls), 1)

    def test_simulated_dispatch_uncertain_stops_retry(self):
        self._draft()
        self.ledger.record_content_approval("anthares-test-2026", "owner-confirmed", self.client)
        self.ledger.record_recipient_approval("anthares-test-2026", "owner-audience", self.client)
        self.fake.error_post = True
        with patch.dict(os.environ, {"SENDER_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(ConnectionError):
                self.ledger.dispatch("anthares-test-2026", self.client)
            with self.assertRaises(PermissionError):
                self.ledger.dispatch("anthares-test-2026", self.client)
        self.assertEqual(self.ledger.get("anthares-test-2026")["state"], "RECONCILE_REQUIRED")
        self.assertEqual(sum(path.endswith("/send") for _, path, _ in self.fake.calls), 1)


if __name__ == "__main__":
    unittest.main()
