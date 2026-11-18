"""Persistent single-writer ledger for marketing campaign creation and dispatch.

Store on an authorized external host. The SQLite schema is a pilot only:
distributed workers must use a shared transactional store before activation.
"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from brevo_marketing import MarketingDraft, BrevoMarketing


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CampaignLedger:
    def __init__(self, filename: str):
        self.filename = filename
        with self._db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS brevo_campaigns (
                local_id TEXT PRIMARY KEY,
                brevo_id INTEGER UNIQUE,
                list_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                html_sha256 TEXT NOT NULL,
                state TEXT NOT NULL,
                campaign_approval_ref TEXT,
                recipients_approval_ref TEXT,
                updated_at TEXT NOT NULL
            )""")

    @contextmanager
    def _db(self):
        c = sqlite3.connect(self.filename, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        try:
            yield c
        finally:
            c.close()

    def stage(self, spec: MarketingDraft) -> dict:
        payload = spec.payload()
        digest = hashlib.sha256(spec.html.encode("utf-8")).hexdigest()
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            found = c.execute("SELECT * FROM brevo_campaigns WHERE local_id=?",
                              (spec.local_id,)).fetchone()
            if found:
                if (found["list_id"], found["subject"], found["html_sha256"]) != (
                        spec.list_id, spec.subject, digest):
                    c.rollback()
                    raise ValueError("local campaign ID already used for different content")
                c.commit()
                return dict(found)
            c.execute("""INSERT INTO brevo_campaigns
                (local_id,list_id,subject,html_sha256,state,updated_at)
                VALUES (?,?,?,?,?,?)""",
                (spec.local_id, spec.list_id, spec.subject, digest, "STAGED", _now()))
            c.commit()
        return self.get(spec.local_id)

    def get(self, local_id: str) -> dict:
        with self._db() as c:
            row = c.execute("SELECT * FROM brevo_campaigns WHERE local_id=?",
                            (local_id,)).fetchone()
            if row is None:
                raise KeyError(local_id)
            return dict(row)

    def create_remote_draft(self, spec: MarketingDraft,
                            client: BrevoMarketing) -> int:
        # In case the HTTP response is lost, creation is UNCERTAIN: never auto-retry.
        # The Brevo dashboard must be reconciled by unique "Anthares <local_id>" name.
        self.stage(spec)
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            cur = c.execute("""UPDATE brevo_campaigns SET state='CREATING',
                updated_at=? WHERE local_id=? AND state='STAGED'""",
                            (_now(), spec.local_id))
            if cur.rowcount != 1:
                c.rollback()
                raise RuntimeError("draft is already created or pending reconciliation")
            c.commit()
        try:
            remote_id = client.create_draft(spec)
        except Exception:
            self._set_state(spec.local_id, "RECONCILE_REQUIRED", from_state="CREATING")
            raise
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            cur = c.execute("""UPDATE brevo_campaigns
                SET brevo_id=?, state='REMOTE_DRAFT', updated_at=?
                WHERE local_id=? AND state='CREATING'""",
                (remote_id, _now(), spec.local_id))
            if cur.rowcount != 1:
                c.rollback()
                raise RuntimeError("draft ledger state changed; reconcile before continuing")
            c.commit()
        return remote_id

    def _set_state(self, local_id: str, new_state: str, from_state: str) -> None:
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("""UPDATE brevo_campaigns SET state=?, updated_at=?
                WHERE local_id=? AND state=?""", (new_state, _now(), local_id, from_state))
            c.commit()

    def record_approval(self, local_id: str, kind: str, reference: str) -> None:
        """Reference must identify an explicit out-of-band owner approval."""
        if kind not in {"campaign", "recipients"} or not reference.strip():
            raise ValueError("approval kind/reference invalid")
        field = ("campaign_approval_ref" if kind == "campaign"
                 else "recipients_approval_ref")
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            cur = c.execute(f"""UPDATE brevo_campaigns SET {field}=?, updated_at=?
                WHERE local_id=? AND state='REMOTE_DRAFT'""",
                (reference.strip(), _now(), local_id))
            if cur.rowcount != 1:
                c.rollback()
                raise PermissionError("approval is only possible for a remote draft")
            c.commit()

    def dispatch(self, local_id: str, client: BrevoMarketing) -> None:
        """One attempt. An uncertain provider response is never blindly replayed."""
        with self._db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM brevo_campaigns WHERE local_id=?",
                            (local_id,)).fetchone()
            if not row or row["state"] != "REMOTE_DRAFT":
                c.rollback()
                raise PermissionError("campaign must be an unsent remote draft")
            if not row["campaign_approval_ref"] or not row["recipients_approval_ref"]:
                c.rollback()
                raise PermissionError("campaign and audience require separate approvals")
            # Fail before mutating the ledger when the global gate is disabled.
            import os
            if os.environ.get("BREVO_LIVE_SEND_ENABLED") != "1":
                c.rollback()
                raise PermissionError("live sending disabled")
            c.execute("""UPDATE brevo_campaigns SET state='DISPATCHING', updated_at=?
                WHERE local_id=? AND state='REMOTE_DRAFT'""", (_now(), local_id))
            c.commit()
            snapshot = dict(row)
        try:
            client.send_now(
                snapshot["brevo_id"],
                approved_campaign_id=snapshot["brevo_id"],
                approved_list_id=snapshot["list_id"],
                actual_list_id=snapshot["list_id"],
                campaign_approval_ref=snapshot["campaign_approval_ref"],
                recipient_approval_ref=snapshot["recipients_approval_ref"],
            )
        except Exception:
            self._set_state(local_id, "RECONCILE_REQUIRED", from_state="DISPATCHING")
            raise
        self._set_state(local_id, "SCHEDULED", from_state="DISPATCHING")
