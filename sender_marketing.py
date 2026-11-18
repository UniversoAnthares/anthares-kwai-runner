"""Sender.net v2 marketing campaigns adapter with immutable audience checks.

All writes require explicit switches. No transactional fallback is implemented.
Docs: https://api.sender.net/campaigns/create-campaign/
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional


BASE_URL = "https://api.sender.net/v2"
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


class SenderAPIError(RuntimeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Sender API HTTP {status}; inspect the provider dashboard")


def normalized_email(value: str) -> str:
    result = value.strip().lower()
    if not EMAIL.fullmatch(result):
        raise ValueError("invalid email")
    return result


def safe_id(value: str, label: str = "id") -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid {label}")
    return value


def enabled(name: str) -> bool:
    return os.environ.get(name, "0") == "1"


@dataclass(frozen=True)
class SenderDraft:
    local_id: str
    name: str
    subject: str
    html: str
    sender_name: str
    reply_to: str
    group_id: str
    preheader: str = ""

    def payload(self) -> dict:
        local = safe_id(self.local_id, "local campaign id")
        group = safe_id(self.group_id, "Sender group")
        if not self.name.strip() or not self.subject.strip() or not self.sender_name.strip():
            raise ValueError("name, subject and sender name are required")
        if not 20 <= len(self.html.encode("utf-8")) <= 900_000:
            raise ValueError("HTML content length is invalid")
        # Official Sender HTML unsubscribe merge tag (shown in campaign API docs).
        if "{$unsubscribe_link}" not in self.html:
            raise ValueError("Sender unsubscribe placeholder is required")
        return {
            "title": f"Anthares {local} - {self.name.strip()}",
            "subject": self.subject.strip(),
            "from": self.sender_name.strip(),
            "reply_to": normalized_email(self.reply_to),
            "preheader": self.preheader.strip(),
            "content_type": "html",
            "content": self.html,
            "groups": [group],
            "segments": [],
            "auto_followup_active": False,
            "google_analytics": 0,
        }


class SenderMarketing:
    def __init__(self, token: Optional[str] = None,
                 transport: Optional[Callable[[str, str, Optional[dict]], Any]] = None,
                 suppression_lookup: Optional[Callable[[str], bool]] = None):
        self._transport = transport
        self._token = token or os.environ.get("SENDER_API_TOKEN", "")
        self.suppression_lookup = suppression_lookup
        if not self._token and transport is None:
            raise RuntimeError("SENDER_API_TOKEN missing; operations disabled")

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> Any:
        if self._transport is not None:
            return self._transport(method, path, body)
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            BASE_URL + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self._token}",
                     "Accept": "application/json",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as reply:
                data = reply.read(1_500_000)
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as exc:
            # Hide provider body/headers: user addresses and token must not leak.
            raise SenderAPIError(exc.code) from None

    def campaigns(self, status: str = "DRAFT", limit: int = 20) -> dict:
        if status not in {"DRAFT", "SENT", "SCHEDULED", "SENDING"}:
            raise ValueError("unsupported campaign status")
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("invalid limit")
        response = self._request("GET", f"/campaigns?limit={limit}&status={status}")
        if not isinstance(response, dict):
            raise RuntimeError("invalid campaign response")
        return response

    def campaign(self, campaign_id: str) -> dict:
        response = self._request("GET", f"/campaigns/{safe_id(campaign_id, 'campaign')}")
        if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
            raise RuntimeError("invalid campaign response")
        if response["data"].get("id") != campaign_id:
            raise RuntimeError("campaign ID mismatch")
        return response["data"]

    def groups(self) -> dict:
        result = self._request("GET", "/groups")
        if not isinstance(result, dict):
            raise RuntimeError("invalid groups response")
        return result

    def audience_snapshot(self, group_id: str, max_contacts: int = 50_000) -> dict:
        """Read each group page, count eligible members, fingerprint exact audience.

        A 'suppressed locally but active remotely' member blocks the operation.
        Cached/global suppression source is required for live dispatch.
        """
        group_id = safe_id(group_id, "group")
        if max_contacts < 1:
            raise ValueError("invalid max_contacts")
        emails = set()
        processed = 0
        expected_total = None
        for page in range(1, 5001):
            response = self._request(
                "GET", f"/groups/{group_id}/subscribers?page={page}")
            if not isinstance(response, dict) or not isinstance(response.get("data"), list):
                raise RuntimeError("invalid group subscribers response")
            members = response["data"]
            meta = response.get("meta")
            links = response.get("links")
            if not isinstance(meta, dict) or not isinstance(links, dict):
                raise RuntimeError("missing group pagination metadata")
            total = meta.get("total")
            if type(total) is not int or total < 0 or total > max_contacts:
                raise RuntimeError("invalid group subscriber count")
            if expected_total is None:
                expected_total = total
            if total != expected_total or meta.get("current_page") != page:
                raise RuntimeError("group membership changed during scan")
            if not members and processed < total:
                raise RuntimeError("incomplete subscriber list")
            for member in members:
                if not isinstance(member, dict) or not member.get("email"):
                    raise RuntimeError("invalid group member")
                email = normalized_email(member["email"])
                status = member.get("status")
                if not isinstance(status, dict) or not isinstance(status.get("email"), str):
                    raise RuntimeError("missing subscriber status")
                st = status["email"].lower()
                if st == "active":
                    if member.get("unsubscribed_at") is not None or member.get("bounced_at") is not None:
                        raise RuntimeError("conflicting subscriber eligibility")
                    if self.suppression_lookup and self.suppression_lookup(email):
                        raise PermissionError("global suppression conflicts with Sender group")
                    emails.add(email)
                elif st not in {"unsubscribed", "bounced", "complained", "inactive", "pending"}:
                    raise RuntimeError("unknown subscriber status")
            processed += len(members)
            if processed > max_contacts or processed > total:
                raise RuntimeError("invalid group page size")
            if links.get("next") is None:
                if processed != total:
                    raise RuntimeError("group scan incomplete")
                break
        else:
            raise RuntimeError("group pagination limit exceeded")
        if not emails:
            raise PermissionError("eligible group audience is empty")
        digest = hashlib.sha256("\n".join(sorted(emails)).encode("utf-8")).hexdigest()
        return {"count": len(emails), "digest": digest, "group_id": group_id}

    def create_draft(self, draft: SenderDraft) -> str:
        if not enabled("SENDER_DRAFT_WRITE_ENABLED"):
            raise PermissionError("Sender draft write disabled")
        result = self._request("POST", "/campaigns", draft.payload())
        if not isinstance(result, dict) or result.get("success") is not True:
            raise RuntimeError("Sender draft not confirmed")
        data = result.get("data")
        if not isinstance(data, dict) or data.get("status") != "DRAFT":
            raise RuntimeError("Sender draft response invalid")
        return safe_id(data.get("id"), "Sender campaign id")

    def send_approved(self, campaign_id: str, *, approved_subject: str,
                      approved_remote_content_hash: str, approved_group_id: str,
                      approved_audience_digest: str, content_approval: str,
                      audience_approval: str) -> None:
        if not enabled("SENDER_LIVE_SEND_ENABLED"):
            raise PermissionError("Sender campaign dispatch disabled")
        if self.suppression_lookup is None:
            raise PermissionError("verified global suppression lookup required")
        if not content_approval.strip() or not audience_approval.strip():
            raise PermissionError("separate content and recipient approvals required")
        cid = safe_id(campaign_id, "campaign")
        group = safe_id(approved_group_id, "group")
        for x in (approved_remote_content_hash, approved_audience_digest):
            if not re.fullmatch("[0-9a-f]{64}", x):
                raise PermissionError("invalid approved fingerprint")
        remote = self.campaign(cid)
        if remote.get("status") != "DRAFT" or remote.get("subject") != approved_subject:
            raise PermissionError("remote campaign is no longer the approved draft")
        if remote.get("campaign_groups") != [group] or remote.get("segments") not in ([], None):
            raise PermissionError("remote audience selectors differ from approval")
        if remote.get("send_to_all") not in (0, False, None):
            raise PermissionError("remote campaign would send to additional recipients")
        if remote.get("auto_followup_active") not in (0, False, None):
            raise PermissionError("unapproved follow-up is enabled")
        html = remote.get("html")
        if not isinstance(html, dict) or not isinstance(html.get("html_content"), str):
            raise PermissionError("remote HTML cannot be validated")
        digest = hashlib.sha256(html["html_content"].encode("utf-8")).hexdigest()
        if digest != approved_remote_content_hash:
            raise PermissionError("remote message changed after approval")
        audience = self.audience_snapshot(group)
        if audience["digest"] != approved_audience_digest:
            raise PermissionError("remote audience changed after approval")
        result = self._request("POST", f"/campaigns/{cid}/send")
        if not isinstance(result, dict) or result.get("success") is not True:
            raise RuntimeError("Sender dispatch response uncertain")
