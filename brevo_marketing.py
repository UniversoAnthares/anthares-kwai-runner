"""Brevo Marketing API adapter. No campaign sends happen on import or by default.

This module uses marketing campaigns (/emailCampaigns), not transactional SMTP.
Provider writes are gated by environment switches and explicit operator actions.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional


BASE_URL = "https://api.brevo.com/v3"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BrevoAPIError(RuntimeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Brevo API HTTP {status}; inspect the provider dashboard")


def _positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{label} must be a positive integer") from None
    if parsed <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return parsed


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if not EMAIL.fullmatch(normalized):
        raise ValueError("invalid email")
    return normalized


def _enabled(name: str) -> bool:
    return os.environ.get(name) == "1"


@dataclass(frozen=True)
class MarketingDraft:
    local_id: str
    name: str
    subject: str
    html: str
    sender_email: str
    sender_name: str
    list_id: int
    reply_to: str

    def payload(self) -> dict:
        if not self.local_id or not re.fullmatch(r"[a-zA-Z0-9_-]{3,80}", self.local_id):
            raise ValueError("invalid local campaign identifier")
        if not self.name.strip() or not self.subject.strip() or not self.sender_name.strip():
            raise ValueError("name and subject are required")
        if not 10 < len(self.html.encode("utf-8")) < 1_000_000:
            raise ValueError("HTML must contain 11 bytes to less than 1 MB")
        if "{{ unsubscribe }}" not in self.html:
            raise ValueError("campaign HTML requires Brevo unsubscribe placeholder")
        sender = _email(self.sender_email)
        reply = _email(self.reply_to)
        return {
            "name": f"Anthares {self.local_id} - {self.name.strip()}",
            "subject": self.subject.strip(),
            "sender": {"email": sender, "name": self.sender_name.strip()},
            "replyTo": reply,
            "recipients": {"listIds": [_positive_id(self.list_id, "list_id")]},
            "htmlContent": self.html,
            "tag": "anthares-mailing",
        }


class BrevoMarketing:
    """HTTP client with an injectable transport for offline contract tests."""

    def __init__(self, api_key: Optional[str] = None,
                 transport: Optional[Callable[[str, str, Optional[dict]], Any]] = None):
        self.transport = transport
        self.api_key = api_key or os.environ.get("BREVO_API_KEY", "")
        if not self.api_key and transport is None:
            raise RuntimeError("BREVO_API_KEY missing (leave campaign disabled)")

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> Any:
        if self.transport is not None:
            return self.transport(method, path, data)
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        req = urllib.request.Request(
            BASE_URL + path,
            data=body,
            method=method,
            headers={"api-key": self.api_key, "accept": "application/json",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                result = response.read(1_000_000)
                return json.loads(result) if result else {}
        except urllib.error.HTTPError as exc:
            # Never log provider response or secret-bearing request headers.
            raise BrevoAPIError(exc.code) from None

    def lists(self, limit: int = 50, offset: int = 0) -> Any:
        if not 1 <= limit <= 50 or offset < 0:
            raise ValueError("invalid pagination")
        return self._request("GET", f"/contacts/lists?limit={limit}&offset={offset}")

    def list_details(self, list_id: int) -> Any:
        return self._request("GET", f"/contacts/lists/{_positive_id(list_id, 'list_id')}")

    def campaign_details(self, campaign_id: int) -> Any:
        return self._request("GET", f"/emailCampaigns/{_positive_id(campaign_id, 'campaign_id')}")

    def create_draft(self, spec: MarketingDraft) -> int:
        if not _enabled("BREVO_DRAFT_WRITE_ENABLED"):
            raise PermissionError("remote draft writes disabled")
        result = self._request("POST", "/emailCampaigns", spec.payload())
        return _positive_id(result.get("id"), "Brevo draft id")

    def add_consented_contact(self, email: str, list_id: int,
                              consent_evidence: str, source: str) -> int:
        """Strict admission. Never silently override a prior Brevo blocklist."""
        if not _enabled("BREVO_CONTACT_SYNC_ENABLED"):
            raise PermissionError("contact synchronization disabled")
        if not consent_evidence.strip() or not source.strip():
            raise PermissionError("contact requires affirmative consent evidence and provenance")
        response = self._request("POST", "/contacts", {
            "email": _email(email),
            "listIds": [_positive_id(list_id, "list_id")],
            "updateEnabled": False,
        })
        return _positive_id(response.get("id"), "Brevo contact id")

    def send_test(self, campaign_id: int, recipient: str) -> None:
        if not _enabled("BREVO_TEST_SEND_ENABLED"):
            raise PermissionError("test sends disabled")
        email = _email(recipient)
        if email != _email(os.environ.get("BREVO_TEST_RECIPIENT", "")):
            raise PermissionError("test recipient is not allowlisted")
        self._request("POST",
                      f"/emailCampaigns/{_positive_id(campaign_id, 'campaign_id')}/sendTest",
                      {"emailTo": [email]})

    def send_now(self, campaign_id: int, *, approved_campaign_id: int,
                 approved_list_id: int, actual_list_id: int,
                 campaign_approval_ref: str, recipient_approval_ref: str,
                 expected_subject: str, expected_html_sha256: str) -> None:
        """Explicit triple gate; never infer permission from a contact/list existing."""
        if not _enabled("BREVO_LIVE_SEND_ENABLED"):
            raise PermissionError("campaign dispatch disabled")
        cid = _positive_id(campaign_id, "campaign_id")
        if cid != _positive_id(approved_campaign_id, "approved_campaign_id"):
            raise PermissionError("campaign approval does not match")
        if _positive_id(approved_list_id, "approved_list_id") != _positive_id(actual_list_id, "actual_list_id"):
            raise PermissionError("recipient list approval does not match")
        if not campaign_approval_ref.strip() or not recipient_approval_ref.strip():
            raise PermissionError("campaign and recipient approvals both required")
        # Check actual remote list to avoid sending to a changed/unapproved list.
        info = self.campaign_details(cid)
        if info.get("status") != "draft":
            raise PermissionError("remote campaign must be an unsent draft")
        if info.get("subject") != expected_subject:
            raise PermissionError("remote subject differs from approved campaign")
        remote_html = info.get("htmlContent")
        if not isinstance(remote_html, str) or hashlib.sha256(remote_html.encode("utf-8")).hexdigest() != expected_html_sha256:
            raise PermissionError("remote HTML differs from approved campaign")
        remote_ids = info.get("recipients", {}).get("lists", [])
        # Provider's report representation may have list names/IDs in objects.
        ids = {int(x.get("id", 0)) if isinstance(x, dict) else int(x) for x in remote_ids}
        if ids != {_positive_id(actual_list_id, "actual_list_id")}:
            raise PermissionError("remote recipient list differs; reconcile before sending")
        self._request("POST", f"/emailCampaigns/{cid}/sendNow")
