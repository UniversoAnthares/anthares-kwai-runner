"""No-network contract tests for the Brevo marketing integration."""
import os
import tempfile
import unittest
from unittest.mock import patch

from brevo_marketing import BrevoMarketing, MarketingDraft
from brevo_campaign_ledger import CampaignLedger


class FakeBrevo:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail
        self.audience = [
            {"email": "p1@example.org", "emailBlacklisted": False, "listIds": [15], "listUnsubscribed": []},
            {"email": "p2@example.org", "emailBlacklisted": True, "listIds": [15], "listUnsubscribed": []},
        ]
        self.remote = {"status": "draft", "subject": "Material de estudo", "recipients": {"lists": [{"listId": 15}]},
                       "htmlContent": "<p>Mensagem {{ unsubscribe }}</p>"}

    def __call__(self, method, path, data):
        self.calls.append((method, path, data))
        if self.fail and method == "POST":
            raise ConnectionError("simulated lost provider reply")
        if method == "POST" and path == "/emailCampaigns":
            return {"id": 123}
        if method == "POST" and path == "/contacts":
            return {"id": 42}
        if method == "GET" and path.startswith("/emailCampaigns/"):
            return self.remote
        if method == "GET" and path == "/account":
            return {"email": "sender@example.org"}
        if method == "GET" and "/contacts?" in path and path.startswith("/contacts/lists/"):
            return {"contacts": self.audience}
        if method == "GET" and path.startswith("/contacts/lists"):
            return {"lists": []}
        return {}


def spec(**overrides):
    values = dict(
        local_id="pastors-2027-test", name="Planejamento EBD",
        subject="Material de estudo", html="<p>Mensagem {{ unsubscribe }}</p>",
        sender_email="contato@anthares.us", sender_name="Editora",
        list_id=15, reply_to="contato@anthares.us")
    values.update(overrides)
    return MarketingDraft(**values)


class MarketingContractTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeBrevo()
        self.client = BrevoMarketing(transport=self.fake, suppression_lookup=lambda email: False)

    def test_readonly_readiness_exposes_no_secrets(self):
        with patch.dict(os.environ, {
            "BREVO_DRAFT_WRITE_ENABLED": "0",
            "BREVO_LIVE_SEND_ENABLED": "0",
        }):
            report = self.client.readiness()
        self.assertTrue(report["api_authenticated"])
        self.assertTrue(report["lists_endpoint_accessible"])
        self.assertFalse(report["live_send_enabled"])
        self.assertNotIn("api_key", report)
        self.assertTrue(all(method == "GET" for method, _, _ in self.fake.calls))

    def test_readonly_campaign_queries_validate_filters(self):
        self.client.campaigns("draft", 10, 0)
        self.assertEqual(self.fake.calls[-1][1],
                         "/emailCampaigns?status=draft&limit=10&offset=0")
        with self.assertRaises(ValueError):
            self.client.campaigns("sendNow")
        with self.assertRaises(ValueError):
            self.client.campaigns("draft", limit=1000)

    def test_local_global_suppression_fails_closed(self):
        client = BrevoMarketing(transport=self.fake,
                                suppression_lookup=lambda email: email == "p1@example.org")
        with self.assertRaises(PermissionError):
            client.audience_snapshot(15)

    def test_live_dispatch_without_suppression_source_fails(self):
        client = BrevoMarketing(transport=self.fake)
        import hashlib
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="owner-approved",
                    recipient_approval_ref="audience-approved",
                    expected_subject=spec().subject,
                    expected_html_sha256=hashlib.sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest="0" * 64)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                client.send_now(123, **args)
        self.assertFalse(any("/sendNow" in p for _, p, _ in self.fake.calls))

    def test_audience_fingerprint_is_stable_and_excludes_blocked(self):
        approved = self.client.audience_snapshot(15)
        self.assertEqual(approved["count"], 1)
        self.fake.audience.append({"email": "new@example.org", "emailBlacklisted": False, "listIds": [15], "listUnsubscribed": []})
        modified = self.client.audience_snapshot(15)
        self.assertEqual(modified["count"], 2)
        self.assertNotEqual(approved["digest"], modified["digest"])

    def test_audience_changes_block_dispatch_even_with_same_list_id(self):
        approved = self.client.audience_snapshot(15)
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="owner-1",
                    recipient_approval_ref="owner-2",
                    expected_subject=spec().subject,
                    expected_html_sha256=__import__("hashlib").sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest=approved["digest"])
        self.fake.audience = [{"email": "replacement@example.org", "emailBlacklisted": False, "listIds": [15], "listUnsubscribed": []}]
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.send_now(123, **args)
        self.assertFalse(any("sendNow" in path for _, path, _ in self.fake.calls))

    def test_per_list_unsubscribe_is_excluded(self):
        original = self.client.audience_snapshot(15)
        self.fake.audience.append({
            "email": "unsubscribed@example.org", "emailBlacklisted": False,
            "listIds": [15], "listUnsubscribed": [15]})
        after = self.client.audience_snapshot(15)
        self.assertEqual(after, original)

    def test_missing_suppression_metadata_fails_closed(self):
        self.fake.audience = [{"email": "unknown@example.org", "emailBlacklisted": False,
                               "listIds": [15]}]
        with self.assertRaises(RuntimeError):
            self.client.audience_snapshot(15)

    def test_recipient_segments_are_rejected(self):
        import hashlib
        approved = self.client.audience_snapshot(15)
        self.fake.remote["recipients"]["segments"] = [300]
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="approval-campaign",
                    recipient_approval_ref="approval-recipients",
                    expected_subject=spec().subject,
                    expected_html_sha256=hashlib.sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest=approved["digest"])
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.send_now(123, **args)
        self.assertFalse(any("sendNow" in path for _, path, _ in self.fake.calls))

    def test_campaign_payload_is_marketing_not_smtp(self):
        p = spec().payload()
        self.assertEqual(p["recipients"], {"listIds": [15]})
        self.assertIn("unsubscribe", p["htmlContent"])
        self.assertEqual(p["replyTo"], "contato@anthares.us")

    def test_content_validation_and_sender(self):
        for data in [
            {"html": "<p>sem descadastro</p>"},
            {"sender_email": "sem-email"},
            {"list_id": 0},
            {"local_id": "../../unsafe"},
            {"html": "<p>" + "x" * 1_000_000 + "{{ unsubscribe }}" + "</p>"},
        ]:
            with self.subTest(data=str(data)[:50]), self.assertRaises(ValueError):
                spec(**data).payload()

    def test_no_remote_draft_without_switch(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.client.create_draft(spec())
        self.assertEqual(self.fake.calls, [])

    def test_draft_created_only_by_explicit_gate(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            self.assertEqual(self.client.create_draft(spec()), 123)
        self.assertEqual(self.fake.calls[0][1], "/emailCampaigns")

    def test_contact_requires_provenance_and_gate(self):
        with patch.dict(os.environ, {"BREVO_CONTACT_SYNC_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.client.add_consented_contact("a@b.org", 15, "", "directory")
            self.client.add_consented_contact("a@b.org", 15, "consent receipt", "signed form")
        self.assertEqual(self.fake.calls[0][2]["updateEnabled"], False)

    def test_test_send_must_have_allowlisted_recipient(self):
        env = {"BREVO_TEST_SEND_ENABLED": "1",
               "BREVO_TEST_RECIPIENT": "owner@example.org"}
        with patch.dict(os.environ, env):
            with self.assertRaises(PermissionError):
                self.client.send_test(123, "other@example.org")
            self.client.send_test(123, "owner@example.org")
        self.assertEqual(self.fake.calls[-1][2], {"emailTo": ["owner@example.org"]})

    def test_dispatch_denied_without_gate(self):
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="owner-1",
                    recipient_approval_ref="owner-2",
                    expected_subject=spec().subject,
                    expected_html_sha256=__import__("hashlib").sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest="0"*64)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.client.send_now(123, **args)
        self.assertEqual(self.fake.calls, [])

    def test_dispatch_checks_remote_recipient_list(self):
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="owner-1",
                    recipient_approval_ref="owner-2",
                    expected_subject=spec().subject,
                    expected_html_sha256=__import__("hashlib").sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest="0"*64)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            self.fake.remote["recipients"] = {"lists": [16]}
            with self.assertRaises(PermissionError):
                self.client.send_now(123, **args)
            self.assertFalse(any("sendNow" in path for _, path, _ in self.fake.calls))


    def test_remote_content_change_blocks_dispatch(self):
        import hashlib
        args = dict(approved_campaign_id=123, approved_list_id=15,
                    actual_list_id=15, campaign_approval_ref="owner-1",
                    recipient_approval_ref="owner-2",
                    expected_subject=spec().subject,
                    expected_html_sha256=hashlib.sha256(spec().html.encode()).hexdigest(),
                    approved_audience_digest="0"*64)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            self.fake.remote["htmlContent"] = "<p>Conteúdo adulterado {{ unsubscribe }}</p>"
            with self.assertRaises(PermissionError):
                self.client.send_now(123, **args)
            self.assertFalse(any("sendNow" in path for _, path, _ in self.fake.calls))

class LedgerContractTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.ledger = CampaignLedger(os.path.join(self.folder.name, "ledger.db"))
        self.fake = FakeBrevo()
        self.client = BrevoMarketing(transport=self.fake, suppression_lookup=lambda email: False)

    def tearDown(self):
        self.folder.cleanup()

    def test_dedupe_on_restart_and_immutable_content(self):
        self.ledger.stage(spec())
        other = CampaignLedger(self.ledger.filename)
        self.assertEqual(other.get(spec().local_id)["state"], "STAGED")
        with self.assertRaises(ValueError):
            other.stage(spec(subject="Tema alterado"))

    def test_draft_creation_persists_remote_id(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            self.assertEqual(self.ledger.create_remote_draft(spec(), self.client), 123)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "REMOTE_DRAFT")
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            with self.assertRaises(RuntimeError):
                self.ledger.create_remote_draft(spec(), self.client)
        self.assertEqual(len([x for x in self.fake.calls if x[0] == "POST"]), 1)

    def test_uncertain_draft_never_retried(self):
        fake = FakeBrevo(fail=True)
        client = BrevoMarketing(transport=fake)
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            with self.assertRaises(ConnectionError):
                self.ledger.create_remote_draft(spec(), client)
            with self.assertRaises(RuntimeError):
                self.ledger.create_remote_draft(spec(), client)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "RECONCILE_REQUIRED")
        self.assertEqual(len(fake.calls), 1)

    def test_dispatch_needs_two_approvals_and_stays_off(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            self.ledger.create_remote_draft(spec(), self.client)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(PermissionError):
                self.ledger.dispatch(spec().local_id, self.client)
        self.ledger.record_approval(spec().local_id, "campaign", "operator:review-1")
        self.ledger.record_recipients_approval(spec().local_id, "operator:review-2", self.client)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.ledger.dispatch(spec().local_id, self.client)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "REMOTE_DRAFT")

    def test_mock_dispatch_once_with_dual_approval(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            self.ledger.create_remote_draft(spec(), self.client)
        self.ledger.record_approval(spec().local_id, "campaign", "operator:review-1")
        self.ledger.record_recipients_approval(spec().local_id, "operator:review-2", self.client)
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            self.ledger.dispatch(spec().local_id, self.client)
            with self.assertRaises(PermissionError):
                self.ledger.dispatch(spec().local_id, self.client)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "SCHEDULED")
        self.assertEqual(sum("sendNow" in p for _,p,_ in self.fake.calls), 1)


    def test_ledger_draft_write_gate_preserves_staged_state(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "0"}):
            with self.assertRaises(PermissionError):
                self.ledger.create_remote_draft(spec(), self.client)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "STAGED")
        self.assertEqual(self.fake.calls, [])

    def test_dispatch_ambiguous_provider_result_never_retried(self):
        with patch.dict(os.environ, {"BREVO_DRAFT_WRITE_ENABLED": "1"}):
            self.ledger.create_remote_draft(spec(), self.client)
        self.ledger.record_approval(spec().local_id, "campaign", "operator:review-1")
        self.ledger.record_recipients_approval(spec().local_id, "operator:review-2", self.client)
        self.fake.fail = True
        with patch.dict(os.environ, {"BREVO_LIVE_SEND_ENABLED": "1"}):
            with self.assertRaises(ConnectionError):
                self.ledger.dispatch(spec().local_id, self.client)
            with self.assertRaises(PermissionError):
                self.ledger.dispatch(spec().local_id, self.client)
        self.assertEqual(self.ledger.get(spec().local_id)["state"], "RECONCILE_REQUIRED")
        self.assertEqual(sum("sendNow" in path for _, path, _ in self.fake.calls), 1)

if __name__ == "__main__":
    unittest.main()
