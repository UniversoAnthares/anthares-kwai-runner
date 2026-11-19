"""Private pastoral mailing eligibility, suppression and once-only delivery ledger.

No outbound HTTP or SMTP code exists in this module. The Resend AUP requires
an explicit prior opt-in; public directory listings do not establish consent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Campo_Grande")
VALID_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SALUTATION_PREFIX = re.compile(r"^(?:Rev(?:erendo)?\.?|Pr\.?|Pastor(?:a)?|Dr\.?)\s+", re.I)
ALLOWED_REASONS = {"hard_bounce", "complaint", "unsubscribe", "manual_block"}
MAX_DAILY = 100
MAX_MONTHLY = 3000


def clock_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_address(raw: str) -> str:
    val = raw.strip().lower()
    if not VALID_EMAIL.fullmatch(val) or len(val) > 254:
        raise ValueError("invalid email address")
    return val


def given_name(raw: str) -> str:
    val = SALUTATION_PREFIX.sub("", " ".join(raw.split())).strip()
    result = val.split(" ", 1)[0] if val else ""
    if not result or not result[0].isalpha():
        raise ValueError("person's first name is missing")
    return result


def utc_stamp() -> str:
    return clock_now().isoformat()


class PastoralQueue:
    def __init__(self, db_path: str):
        self.path = Path(db_path)
        if self.path.is_symlink():
            raise PermissionError("symlink database not allowed")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == "posix":
            os.chmod(self.path.parent, 0o700)
        self.init_db()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA busy_timeout=30000")
            db.execute("PRAGMA journal_mode=WAL")
            yield db
        finally:
            db.close()

    def init_db(self):
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
              email TEXT PRIMARY KEY, full_name TEXT NOT NULL,
              first_name TEXT NOT NULL, source TEXT NOT NULL,
              consent_at TEXT, consent_evidence TEXT, consent_method TEXT,
              imported_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suppressions (
              email TEXT PRIMARY KEY, reason TEXT NOT NULL,
              evidence TEXT NOT NULL, suppressed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbound (
              email TEXT NOT NULL, campaign_id TEXT NOT NULL,
              provider_id TEXT, attempted_at TEXT NOT NULL,
              state TEXT NOT NULL, idempotency_id TEXT NOT NULL UNIQUE,
              PRIMARY KEY(email, campaign_id)
            );
            CREATE TABLE IF NOT EXISTS inbound_events (
              mailbox TEXT NOT NULL, provider_uid TEXT NOT NULL,
              kind TEXT NOT NULL, sender TEXT, subject TEXT,
              received_at TEXT NOT NULL, processed_at TEXT NOT NULL,
              PRIMARY KEY(mailbox, provider_uid)
            );
            """)
        if self.path.exists() and os.name == "posix":
            os.chmod(self.path, 0o600)

    def import_directory(self, records, source: str) -> dict:
        """Import contacts but NEVER convert a directory record into opt-in."""
        if not source.strip():
            raise ValueError("source required")
        scanned, created, invalid, duplicates = 0, 0, 0, 0
        seen = set()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for full_name, raw_email in records:
                scanned += 1
                try:
                    email = normalize_address(str(raw_email))
                    first = given_name(str(full_name))
                except ValueError:
                    invalid += 1
                    continue
                if email in seen:
                    duplicates += 1
                    continue
                seen.add(email)
                cur = db.execute(
                    """INSERT OR IGNORE INTO contacts(
                        email,full_name,first_name,source,imported_at)
                        VALUES (?,?,?,?,?)""",
                    (email, full_name.strip(), first, source.strip(), utc_stamp()))
                created += cur.rowcount
            db.commit()
        return {"scanned": scanned, "created": created,
                "invalid": invalid, "repeated_in_import": duplicates,
                "unique_valid_in_import": len(seen)}

    def add_consent(self, email: str, method: str, evidence: str, when: str):
        """A provenance reference is mandatory; claims alone aren't validation."""
        e = normalize_address(email)
        if method not in {"double_opt_in", "documented_prior_permission"}:
            raise ValueError("unsupported consent method")
        if not evidence.strip() or len(evidence.strip()) < 12:
            raise ValueError("documented verifiable evidence required")
        timestamp = datetime.fromisoformat(when.replace("Z", "+00:00"))
        if timestamp.tzinfo is None or timestamp > clock_now():
            raise ValueError("consent time invalid")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM suppressions WHERE email=?", (e,)).fetchone():
                db.rollback()
                raise PermissionError("suppressed email cannot be re-enabled")
            cur = db.execute("""UPDATE contacts SET consent_at=?,
                  consent_evidence=?,consent_method=?
                  WHERE email=? AND consent_at IS NULL""",
                (timestamp.isoformat(), evidence.strip(), method, e))
            if cur.rowcount != 1:
                db.rollback()
                raise PermissionError("unknown or already authorized")
            db.commit()

    def suppress(self, email: str, reason: str, evidence: str) -> bool:
        e = normalize_address(email)
        if reason not in ALLOWED_REASONS:
            raise ValueError("temporary bounces must not be suppressed")
        if not evidence.strip():
            raise ValueError("provider evidence needed")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute("""INSERT OR IGNORE INTO suppressions
                (email,reason,evidence,suppressed_at) VALUES (?,?,?,?)""",
                (e, reason, evidence.strip(), utc_stamp())).rowcount == 1
            db.commit()
            return changed

    def plan(self, campaign_id: str, provider_daily_remaining: int = 0,
             provider_monthly_remaining: int = 0) -> dict:
        """Read-only gate; returns no addresses until consent and quota confirmed."""
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{4,100}", campaign_id):
            raise ValueError("invalid campaign")
        now = clock_now().astimezone(TZ)
        today = now.date().isoformat()
        current_month = now.strftime("%Y-%m")
        with self.connect() as db:
            daily = db.execute(
                "SELECT COUNT(*) FROM outbound WHERE substr(attempted_at,1,10)=?", (today,)).fetchone()[0]
            monthly = db.execute(
                "SELECT COUNT(*) FROM outbound WHERE substr(attempted_at,1,7)=?", (current_month,)).fetchone()[0]
            eligible = db.execute("""SELECT COUNT(*) FROM contacts c
                   WHERE c.consent_at IS NOT NULL
                   AND c.consent_evidence IS NOT NULL
                   AND NOT EXISTS (SELECT 1 FROM suppressions s WHERE s.email=c.email)
                   AND NOT EXISTS (SELECT 1 FROM outbound o WHERE o.email=c.email
                                  AND o.campaign_id=?)""", (campaign_id,)).fetchone()[0]
            missing = db.execute("SELECT COUNT(*) FROM contacts WHERE consent_at IS NULL").fetchone()[0]
            suppressed = db.execute("SELECT COUNT(*) FROM suppressions").fetchone()[0]
        left = max(0, min(MAX_DAILY-daily,MAX_MONTHLY-monthly,
                          max(0,provider_daily_remaining),
                          max(0,provider_monthly_remaining)))
        return {"campaign_id": campaign_id, "eligible": eligible,
                "unconfirmed_consent": missing, "suppressed": suppressed,
                "local_daily_used": daily, "local_monthly_used": monthly,
                "dispatch_cap": min(eligible,left), "dispatch_enabled": False}

    def record_attempt(self, email: str, campaign_id: str, provider_id: str | None,
                       state: str, idempotency_id: str):
        if state not in {"ATTEMPTED_UNKNOWN", "ACCEPTED", "REJECTED"}:
            raise ValueError("invalid state")
        email = normalize_address(email)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            consent = db.execute("""SELECT 1 FROM contacts WHERE email=? AND
                consent_at IS NOT NULL AND consent_evidence IS NOT NULL""",
                (email,)).fetchone()
            suppressed = db.execute("SELECT 1 FROM suppressions WHERE email=?", (email,)).fetchone()
            if not consent or suppressed:
                db.rollback()
                raise PermissionError("recipient ineligible")
            db.execute("""INSERT INTO outbound(email,campaign_id,provider_id,
                         attempted_at,state,idempotency_id)
                         VALUES (?,?,?,?,?,?)""",
                (email,campaign_id,provider_id,
                 clock_now().astimezone(TZ).isoformat(),state,idempotency_id))
            db.commit()

    def record_inbox_event(self, mailbox: str, uid: str, kind: str,
                           sender: str, subject: str, received_at: str) -> bool:
        if kind not in {"reply", "hard_bounce", "soft_bounce", "complaint",
                        "unsubscribe", "other"}:
            raise ValueError("invalid event kind")
        with self.connect() as db:
            cur = db.execute("""INSERT OR IGNORE INTO inbound_events(
                mailbox,provider_uid,kind,sender,subject,received_at,processed_at)
                VALUES (?,?,?,?,?,?,?)""",
                (mailbox,uid,kind,sender,subject,received_at,utc_stamp()))
            return cur.rowcount == 1

    def status(self) -> dict:
        with self.connect() as db:
            return {
                "contacts": db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
                "consented": db.execute("SELECT COUNT(*) FROM contacts WHERE consent_at IS NOT NULL").fetchone()[0],
                "suppressed": db.execute("SELECT COUNT(*) FROM suppressions").fetchone()[0],
                "outbound_attempts": db.execute("SELECT COUNT(*) FROM outbound").fetchone()[0],
                "inbox_processed": db.execute("SELECT COUNT(*) FROM inbound_events").fetchone()[0],
                "live_sending": "DISABLED_PENDING_PROVEN_CONSENT_AND_IMPLEMENTATION",
            }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    commands = p.add_subparsers(dest="cmd", required=True)
    commands.add_parser("status")
    imp = commands.add_parser("import-csv")
    imp.add_argument("--csv", required=True)
    imp.add_argument("--source", required=True)
    sub = commands.add_parser("suppress")
    sub.add_argument("--email", required=True)
    sub.add_argument("--reason", required=True)
    sub.add_argument("--evidence", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--campaign-id", default="mente-crista-ebd-2027")
    plan.add_argument("--provider-daily-left", type=int, default=0)
    plan.add_argument("--provider-monthly-left", type=int, default=0)
    args = p.parse_args()
    queue = PastoralQueue(args.db)
    if args.cmd == "status":
        result = queue.status()
    elif args.cmd == "import-csv":
        with open(args.csv, encoding="utf-8-sig", newline="") as f:
            rows = csv.DictReader(f)
            if not {"Nome do pastor", "E-mail"} <= set(rows.fieldnames or []):
                raise ValueError("CSV expected headers missing")
            result = queue.import_directory(
                ((x["Nome do pastor"],x["E-mail"]) for x in rows), args.source)
    elif args.cmd == "suppress":
        result = {"newly_suppressed": queue.suppress(args.email,args.reason,args.evidence)}
    else:
        result = queue.plan(args.campaign_id,args.provider_daily_left,args.provider_monthly_left)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__ == "__main__":
    main()
