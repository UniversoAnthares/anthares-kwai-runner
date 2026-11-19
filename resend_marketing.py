"""Resend Broadcasts marketing adapter, independent of /emails transactional sending.

No contact import or real send is available in this staging adapter. It can
read account marketing resources and, with explicit opt-in, create one draft.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional

API_ROOT = "https://api.resend.com"
UNSUBSCRIBE_TAG = "{{{RESEND_UNSUBSCRIBE_URL}}}"
UUID_PATTERN = re.compile(r"[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}\Z")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


class ResendMarketingError(RuntimeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Resend Marketing HTTP {status}")


def ensure_uuid(raw: str) -> str:
    if not isinstance(raw, str) or not UUID_PATTERN.fullmatch(raw):
        raise ValueError("invalid Resend resource ID")
    return raw.lower()


def normalize_email(value: str) -> str:
    if not isinstance(value, str) or not EMAIL_PATTERN.fullmatch(value.strip()):
        raise ValueError("invalid email")
    return value.strip().lower()


@dataclass(frozen=True)
class ResendBroadcastDraft:
    segment_id: str
    subject: str
    html: str
    from_address: str = "Universo Anthares <contato@anthares.us>"
    reply_to: str = "contato@anthares.us"
    title: str = "Anthares Mailing - rascunho tecnico"

    def payload(self) -> dict:
        segment = ensure_uuid(self.segment_id)
        if not self.subject.strip() or not self.title.strip():
            raise ValueError("subject and draft title required")
        if not isinstance(self.html, str) or not (30 <= len(self.html.encode()) <= 900_000):
            raise ValueError("invalid HTML")
        if UNSUBSCRIBE_TAG not in self.html:
            raise ValueError("Resend unsubscribe merge tag is required")
        if normalize_email(self.reply_to) != "contato@anthares.us":
            raise PermissionError("unapproved reply-to address")
        if self.from_address != "Universo Anthares <contato@anthares.us>":
            raise PermissionError("unapproved sender")
        return {"segment_id": segment, "from": self.from_address,
                "reply_to": self.reply_to, "subject": self.subject.strip(),
                "name": self.title.strip(), "html": self.html}
        # Deliberately omit 'send' and 'scheduled_at': draft-only request.


class ResendMarketing:
    def __init__(self, api_key: Optional[str] = None,
                 transport: Optional[Callable[[str, str, Optional[dict]], Any]] = None,
                 suppression_lookup: Optional[Callable[[str], bool]] = None):
        self._key = api_key or os.environ.get("RESEND_API_KEY", "")
        self._transport = transport
        self.suppression_lookup = suppression_lookup
        if not self._key and transport is None:
            raise RuntimeError("Resend API key not configured")

    def _request(self, method: str, route: str, body: Optional[dict] = None) -> Any:
        if self._transport is not None:
            return self._transport(method, route, body)
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            API_ROOT + route, data=payload, method=method,
            headers={"Authorization": f"Bearer {self._key}",
                     "Content-Type": "application/json",
                     "Accept": "application/json",
                     "User-Agent": "anthares-mailing-resend/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as resp:
                raw = resp.read(2_000_000)
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raise ResendMarketingError(exc.code) from None

    def segments(self) -> dict:
        result = self._request("GET", "/segments?limit=50")
        if not isinstance(result, dict) or not isinstance(result.get("data"), list):
            raise RuntimeError("invalid Resend segment response")
        return result

    def broadcasts(self) -> dict:
        result = self._request("GET", "/broadcasts?limit=50")
        if not isinstance(result, dict) or not isinstance(result.get("data"), list):
            raise RuntimeError("invalid Resend Broadcasts response")
        return result

    def broadcast(self, broadcast_id: str) -> dict:
        rid = ensure_uuid(broadcast_id)
        item = self._request("GET", f"/broadcasts/{rid}")
        if not isinstance(item, dict) or item.get("id") != rid:
            raise RuntimeError("invalid broadcast identity")
        return item

    def audience_snapshot(self, segment_id: str, maximum: int = 50_000) -> dict:
        """Read full segment with cursor pagination and fail closed on incomplete data."""
        segment = ensure_uuid(segment_id)
        after = None
        seen_ids: set[str] = set()
        eligible: set[str] = set()
        inspected = 0
        for _ in range(600):
            query = "/segments/" + segment + "/contacts?limit=100"
            if after:
                query += "&after=" + urllib.parse.quote(after, safe="")
            page = self._request("GET", query)
            if (not isinstance(page, dict) or page.get("object") != "list" or
                    not isinstance(page.get("data"), list) or
                    not isinstance(page.get("has_more"), bool)):
                raise RuntimeError("incomplete Resend contacts page")
            contacts = page["data"]
            if len(contacts) > 100 or (page["has_more"] and not contacts):
                raise RuntimeError("invalid Resend contact pagination")
            for contact in contacts:
                if not isinstance(contact, dict) or not isinstance(contact.get("unsubscribed"), bool):
                    raise RuntimeError("subscriber consent state missing")
                contact_id = ensure_uuid(contact.get("id"))
                if contact_id in seen_ids:
                    raise RuntimeError("duplicate cursor contact")
                seen_ids.add(contact_id)
                email = normalize_email(contact.get("email"))
                if not contact["unsubscribed"]:
                    if self.suppression_lookup is None:
                        raise PermissionError("global suppression lookup required")
                    if self.suppression_lookup(email):
                        raise PermissionError("previously suppressed address still eligible")
                    eligible.add(email)
                inspected += 1
                if inspected > maximum:
                    raise RuntimeError("audience exceeds configured cap")
            if not page["has_more"]:
                break
            after = ensure_uuid(contacts[-1]["id"])
        else:
            raise RuntimeError("contact pagination limit exceeded")
        if not eligible:
            raise PermissionError("no eligible segment contacts")
        return {"segment_id": segment, "count": len(eligible),
                "digest": hashlib.sha256("\n".join(sorted(eligible)).encode()).hexdigest()}

    def create_draft(self, draft: ResendBroadcastDraft) -> str:
        if os.environ.get("RESEND_DRAFT_WRITE_ENABLED") != "1":
            raise PermissionError("Resend draft creation disabled")
        payload = draft.payload()
        response = self._request("POST", "/broadcasts", payload)
        if not isinstance(response, dict) or response.get("object") != "broadcast":
            raise RuntimeError("Resend draft creation unconfirmed")
        return ensure_uuid(response.get("id"))

    def send_broadcast(self, *args, **kwargs):
        """Reserved until an authenticated approval ledger and live tests exist."""
        raise PermissionError("Resend sending disabled pending owner-approved campaign")
