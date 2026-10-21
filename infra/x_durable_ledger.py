"""Exactly-once X submission claim in the existing durable ARA PostgreSQL.

Insert is atomic and irreversible. A started request stays uncertain after a
timeout or worker restart, until a separate readback confirms a post. This
intentionally prefers a retained queue item over a duplicate publication.
"""
from __future__ import annotations

import hashlib
import os
import re
from urllib.parse import urlparse

DDL = """
CREATE TABLE IF NOT EXISTS anthares_x_submission_ledger (
    idempotency_sha256 text PRIMARY KEY,
    account text NOT NULL CHECK (account = 'lucasyahn'),
    status text NOT NULL CHECK (status IN ('started','confirmed')),
    post_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    confirmed_at timestamptz
)
"""


class AlreadyStarted(RuntimeError):
    pass


class DailyLimitReached(RuntimeError):
    pass


def _connection():
    dsn = os.getenv("X_LEDGER_DATABASE_URL") or os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("X_DURABLE_LEDGER_DATABASE_REQUIRED")
    parsed = urlparse(dsn)
    if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname:
        raise RuntimeError("X_DURABLE_LEDGER_INVALID_DSN")
    import psycopg
    return psycopg.connect(dsn, connect_timeout=12, autocommit=True)


def identity(key):
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{12,160}", key or ""):
        raise ValueError("X_IDEMPOTENCY_KEY_REQUIRED")
    return hashlib.sha256(("x:lucasyahn:" + key).encode()).hexdigest()


def begin(key):
    row_id = identity(key)
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
        with conn.transaction():
            with conn.cursor() as cur:
                # Shared PostgreSQL lock fences all consumers and direct API
                # callers, regardless of worker, browser, or deployment.
                cur.execute("SELECT pg_advisory_xact_lock(hashtext('anthares-x:lucasyahn:daily'))")
                cur.execute("""
                    SELECT count(*) FROM anthares_x_submission_ledger
                    WHERE account='lucasyahn' AND status IN ('started','confirmed')
                      AND (created_at AT TIME ZONE 'America/Campo_Grande')::date =
                          (now() AT TIME ZONE 'America/Campo_Grande')::date
                """)
                used = int((cur.fetchone() or (0,))[0])
                if used >= 10:
                    raise DailyLimitReached("X_DAILY_HARD_LIMIT_10")
                cur.execute(
                    """INSERT INTO anthares_x_submission_ledger
                       (idempotency_sha256, account, status)
                       VALUES (%s, 'lucasyahn', 'started')
                       ON CONFLICT DO NOTHING RETURNING idempotency_sha256""",
                    (row_id,),
                )
                claimed = cur.fetchone()
    if not claimed:
        raise AlreadyStarted("X_POST_ALREADY_ATTEMPTED_RECONCILE")
    return row_id


def confirm(row_id, url):
    from tools.x_publication_safety import verified_post_url
    if not re.fullmatch(r"[a-f0-9]{64}", row_id or "") or verified_post_url(url) != url:
        raise ValueError("X_DURABLE_LEDGER_CONFIRMATION_INVALID")
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE anthares_x_submission_ledger SET
                    status='confirmed', post_url=%s, confirmed_at=now()
                   WHERE idempotency_sha256=%s AND account='lucasyahn'
                     AND status='started' RETURNING idempotency_sha256""",
                (url, row_id),
            )
            if not cur.fetchone():
                raise RuntimeError("X_DURABLE_LEDGER_CONFIRMATION_CONFLICT")


def readback(key):
    """Read-only cross-worker proof. Never transitions uncertain to queued."""
    row_id = identity(key)
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute(
                "SELECT status, post_url FROM anthares_x_submission_ledger "
                "WHERE idempotency_sha256=%s AND account='lucasyahn'",
                (row_id,),
            )
            row = cur.fetchone()
    if not row:
        return {"status": "NOT_FOUND"}
    if row[0] == "confirmed" and row[1]:
        return {"status": "CONFIRMED", "post_url": str(row[1])}
    return {"status": "UNCERTAIN", "post_url": None}
