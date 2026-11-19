"""Resend Broadcasts contract tests using simulated HTTP transport only."""
import hashlib
import os
import unittest
from unittest.mock import patch

from resend_marketing import (ResendMarketing, ResendBroadcastDraft, ensure_uuid,
                              UNSUBSCRIBE_TAG)

SEGMENT = "78261eea-8f8b-4381-83c6-79fa7120f1cf"
BROADCAST = "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
CONTACT_A = "e169aa45-1ecf-4183-9955-b1499d5701d3"
CONTACT_B = "e169aa45-1ecf-4183-9955-b1499d5701d4"


class FakeResend:
    def __init__(self):
        self.calls = []
        self.contacts = [
            {"id": CONTACT_A, "email": "ALLOW@example.org", "unsubscribed": False},
            {"id": CONTACT_B, "email": "retired@example.org", "unsubscribed": True},
        ]
        self.missing_state = False
        self.duplicate = False

    def __call__(self, method, route, body):
        self.calls.append((method, route, body))
        if method == "GET" and route.startswith("/segments?"):
            return {"object": "list", "has_more": False,
                    "data": [{"id": SEGMENT, "name": "Teste"}]}
        if method == "GET" and route.startswith("/broadcasts?"):
            return {"object": "list", "has_more": False, "data": []}
        if method == "GET" and route.startswith("/broadcasts/"):
            return {"object": "broadcast", "id": BROADCAST,
                    "segment_id": SEGMENT, "status": "draft",
                    "subject": "Informativo", "html": "<p>Conteudo</p>"}
        if method == "GET" and route.startswith("/segments/" + SEGMENT + "/contacts?"):
            if "after=" in route:
                row = self.contacts[1].copy()
                if self.duplicate:
                    row["id"] = CONTACT_A
                return {"object": "list", "has_more": False, "data": [row]}
            row = self.contacts[0].copy()
            if self.missing_state:
                row.pop("unsubscribed")
            return {"object": "list", "has_more": True, "data": [row]}
        if method == "POST" and route == "/broadcasts":
            assert "send" not in body and "scheduled_at" not in body
            return {"object": "broadcast", "id": BROADCAST}
        raise AssertionError("unexpected Resend route " + route)


class ResendTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeResend()
        self.client = ResendMarketing(transport=self.fake,
                                      suppression_lookup=lambda _: False)

    def _draft(self):
        return ResendBroadcastDraft(segment_id=SEGMENT,
                                    subject="Informativo",
                                    html="<html><p>Texto de teste</p><a href='" + UNSUBSCRIBE_TAG +
                                         "'>Descadastrar</a></html>")

    def test_read_only_endpoints(self):
        self.client.segments()
        self.client.broadcasts()
        self.client.broadcast(BROADCAST)
        self.assertTrue(all(call[0] == "GET" for call in self.fake.calls))

    def test_invalid_resource_id_fails_before_network(self):
        with self.assertRaises(ValueError):
            self.client.broadcast("../../etc/passwd")
        with self.assertRaises(ValueError):
            self.client.audience_snapshot("not-a-uuid")
        self.assertEqual(self.fake.calls, [])

    def test_draft_requires_unsubscribe_and_valid_sender(self):
        with self.assertRaises(ValueError):
            ResendBroadcastDraft(segment_id=SEGMENT, subject="Teste",
                                  html="<p>Falta descadastro</p>").payload()
        with self.assertRaises(PermissionError):
            ResendBroadcastDraft(segment_id=SEGMENT, subject="Teste",
                                  html=self._draft().html,
                                  from_address="Outro <sender@unauthorized.org>").payload()

    def test_draft_payload_does_not_enable_send(self):
        payload = self._draft().payload()
        self.assertEqual(payload["segment_id"], SEGMENT)
        self.assertEqual(payload["reply_to"], "contato@anthares.us")
        self.assertNotIn("send", payload)
        self.assertNotIn("scheduled_at", payload)

    def test_creation_refused_by_default(self):
        with patch.dict(os.environ, {"RESEND_DRAFT_WRITE_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.client.create_draft(self._draft())
        self.assertEqual(self.fake.calls, [])

    def test_creation_with_explicit_draft_gate_only(self):
        with patch.dict(os.environ, {"RESEND_DRAFT_WRITE_ENABLED": "1"}):
            cid = self.client.create_draft(self._draft())
        self.assertEqual(cid, BROADCAST)
        self.assertEqual(self.fake.calls[0][0], "POST")
        self.assertEqual(self.fake.calls[0][1], "/broadcasts")
        self.assertNotIn("send", self.fake.calls[0][2])

    def test_contact_pagination_and_suppression(self):
        audience = self.client.audience_snapshot(SEGMENT)
        self.assertEqual(audience["count"], 1)
        self.assertEqual(len(audience["digest"]), 64)
        self.assertEqual(sum("after=" in route for _, route, _ in self.fake.calls), 1)
        self.assertTrue(all(route.startswith("/segments/" + SEGMENT + "/contacts?")
                            for _, route, _ in self.fake.calls))

    def test_missing_unsubscribe_field_blocks_approval(self):
        self.fake.missing_state = True
        with self.assertRaises(RuntimeError):
            self.client.audience_snapshot(SEGMENT)

    def test_duplicate_contact_blocks_approval(self):
        self.fake.duplicate = True
        with self.assertRaises(RuntimeError):
            self.client.audience_snapshot(SEGMENT)

    def test_locally_suppressed_contact_blocks_approval(self):
        client = ResendMarketing(transport=self.fake,
                                 suppression_lookup=lambda email: email == "allow@example.org")
        with self.assertRaises(PermissionError):
            client.audience_snapshot(SEGMENT)

    def test_missing_global_lookup_blocks_approval(self):
        client = ResendMarketing(transport=self.fake)
        with self.assertRaises(PermissionError):
            client.audience_snapshot(SEGMENT)

    def test_live_send_always_blocked(self):
        with patch.dict(os.environ, {"RESEND_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.send_broadcast(BROADCAST)
        self.assertEqual(self.fake.calls, [])

    def test_empty_audience_blocks_approval(self):
        self.fake.contacts[0]["unsubscribed"] = True
        with self.assertRaises(PermissionError):
            self.client.audience_snapshot(SEGMENT)


if __name__ == "__main__":
    unittest.main()
