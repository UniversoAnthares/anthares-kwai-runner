"""Private one-writer Sender marketing ledger with irreversible send fences.

Execution is disabled by default. Future UI must authenticate approvals; manual
reference strings are insufficient proof of a real authorization by the owner.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from sender_marketing import SenderDraft, SenderMarketing, safe_id


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SenderCampaignLedger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if os.path.islink(db_path):
            raise PermissionError("database path cannot be a symlink")
        with self._database() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS sender_campaigns(
                local_id TEXT PRIMARY KEY,
                remote_id TEXT UNIQUE,
                group_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                state TEXT NOT NULL,
                approved_remote_content_hash TEXT,
                approved_audience_digest TEXT,
                approved_audience_count INTEGER,
                content_approval_ref TEXT,
                recipient_approval_ref TEXT,
                updated_at TEXT NOT NULL
            )""")

    @contextmanager
    def _database(self):
        db = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def get(self, local_id: str) -> dict:
        with self._database() as db:
            row = db.execute("SELECT * FROM sender_campaigns WHERE local_id=?",
                             (safe_id(local_id, "local id"),)).fetchone()
        if row is None:
            raise KeyError(local_id)
        return dict(row)

    def stage(self, spec: SenderDraft) -> dict:
        payload = spec.payload()
        import json
        digest = hashlib.sha256(json.dumps(
            payload, sort_keys=True, ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM sender_campaigns WHERE local_id=?", (spec.local_id,)
            ).fetchone()
            if existing:
                if (existing["group_id"], existing["subject"], existing["payload_sha256"]) != (
                    spec.group_id, spec.subject, digest
                ):
                    db.rollback()
                    raise ValueError("campaign identifier already bound to different content")
                db.commit()
                return dict(existing)
            db.execute("""INSERT INTO sender_campaigns(
                local_id, group_id, subject, payload_sha256, state, updated_at
                ) VALUES (?,?,?,?,?,?)""",
                (spec.local_id, spec.group_id, spec.subject, digest, "STAGED", utcnow()))
            db.commit()
        return self.get(spec.local_id)

    def create_remote_draft(self, spec: SenderDraft, client: SenderMarketing) -> str:
        self.stage(spec)
        if os.environ.get("SENDER_DRAFT_WRITE_ENABLED") != "1":
            raise PermissionError("remote draft writes disabled")
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute("""UPDATE sender_campaigns SET state='CREATING',
                updated_at=? WHERE local_id=? AND state='STAGED'""",
                (utcnow(), spec.local_id))
            if cur.rowcount != 1:
                db.rollback()
                raise RuntimeError("already attempted remote draft; reconcile first")
            db.commit()
        try:
            cid = client.create_draft(spec)
        except Exception:
            self._update_state(spec.local_id, "RECONCILE_REQUIRED", "CREATING")
            raise
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute("""UPDATE sender_campaigns SET remote_id=?,
                state='REMOTE_DRAFT', updated_at=?
                WHERE local_id=? AND state='CREATING'""",
                (cid, utcnow(), spec.local_id))
            if cur.rowcount != 1:
                db.rollback()
                raise RuntimeError("draft result uncertain; reconcile before proceeding")
            db.commit()
        return cid

    def record_content_approval(self, local_id: str, approval_ref: str,
                                client: SenderMarketing) -> None:
        """Store a fingerprint of remote content. Call only after user approval."""
        if not approval_ref.strip():
            raise ValueError("approval reference required")
        row = self.get(local_id)
        if row["state"] != "REMOTE_DRAFT":
            raise PermissionError("only a remote draft can be approved")
        remote = client.campaign(row["remote_id"])
        html = remote.get("html")
        if (remote.get("status") != "DRAFT" or remote.get("subject") != row["subject"]
                or not isinstance(html, dict) or not isinstance(html.get("html_content"), str)):
            raise PermissionError("remote campaign content cannot be verified")
        digest = hashlib.sha256(html["html_content"].encode("utf-8")).hexdigest()
        self._update_fields(local_id, {
            "content_approval_ref": approval_ref.strip(),
            "approved_remote_content_hash": digest,
        })

    def record_recipient_approval(self, local_id: str, approval_ref: str,
                                  client: SenderMarketing) -> dict:
        if not approval_ref.strip():
            raise ValueError("approval reference required")
        row = self.get(local_id)
        if row["state"] != "REMOTE_DRAFT":
            raise PermissionError("only a remote draft can be approved")
        if client.suppression_lookup is None:
            raise PermissionError("global suppression lookup must be verified first")
        audience = client.audience_snapshot(row["group_id"])
        self._update_fields(local_id, {
            "recipient_approval_ref": approval_ref.strip(),
            "approved_audience_digest": audience["digest"],
            "approved_audience_count": audience["count"],
        })
        return {"count": audience["count"], "digest": audience["digest"]}

    def _update_fields(self, local_id: str, updates: dict) -> None:
        permitted = {"content_approval_ref", "approved_remote_content_hash",
                     "recipient_approval_ref", "approved_audience_digest",
                     "approved_audience_count"}
        if not set(updates) <= permitted:
            raise ValueError("invalid approval field")
        fields = ", ".join(f"{key}=?" for key in updates)
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute(
                f"UPDATE sender_campaigns SET {fields}, updated_at=? "
                "WHERE local_id=? AND state='REMOTE_DRAFT'",
                (*updates.values(), utcnow(), local_id),
            )
            if cur.rowcount != 1:
                db.rollback()
                raise PermissionError("approval state changed")
            db.commit()

    def _update_state(self, local_id: str, state: str, old_state: str) -> None:
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""UPDATE sender_campaigns SET state=?, updated_at=?
                WHERE local_id=? AND state=?""",
                (state, utcnow(), local_id, old_state))
            db.commit()

    def dispatch(self, local_id: str, client: SenderMarketing) -> None:
        """Irreversible single attempt. Requires authenticated approvals upstream."""
        if os.environ.get("SENDER_LIVE_SEND_ENABLED") != "1":
            raise PermissionError("Sender live sending disabled")
        if client.suppression_lookup is None:
            raise PermissionError("global suppression lookup is required")
        with self._database() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM sender_campaigns WHERE local_id=?", (local_id,)
            ).fetchone()
            if row is None or row["state"] != "REMOTE_DRAFT":
                db.rollback()
                raise PermissionError("campaign must be an unsent draft")
            required = ("content_approval_ref", "recipient_approval_ref",
                        "approved_remote_content_hash", "approved_audience_digest")
            if not all(row[key] for key in required):
                db.rollback()
                raise PermissionError("separate approvals and fingerprints required")
            snapshot = dict(row)
            db.execute("""UPDATE sender_campaigns SET state='DISPATCHING',
                updated_at=? WHERE local_id=? AND state='REMOTE_DRAFT'""",
                (utcnow(), local_id))
            db.commit()
        try:
            client.send_approved(
                snapshot["remote_id"],
                approved_subject=snapshot["subject"],
                approved_remote_content_hash=snapshot["approved_remote_content_hash"],
                approved_group_id=snapshot["group_id"],
                approved_audience_digest=snapshot["approved_audience_digest"],
                content_approval=snapshot["content_approval_ref"],
                audience_approval=snapshot["recipient_approval_ref"],
            )
        except Exception:
            self._update_state(local_id, "RECONCILE_REQUIRED", "DISPATCHING")
            raise
        self._update_state(local_id, "SENT_PENDING_REPORT", "DISPATCHING")
