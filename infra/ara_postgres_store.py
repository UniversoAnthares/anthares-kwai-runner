import json
import os
import secrets
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("ARA_DATABASE_URL", "")
LEASE_SECONDS = max(30, min(int(os.getenv("ARA_LEASE_SECONDS", "90")), 600))


@contextmanager
def connection():
    if not DATABASE_URL:
        raise RuntimeError("ARA_DATABASE_URL is required")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=8) as conn:
        yield conn


def initialize():
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ara_devices (
              device_id TEXT PRIMARY KEY,
              heartbeat JSONB,
              seen_at TIMESTAMPTZ
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ara_jobs (
              id TEXT PRIMARY KEY,
              device_id TEXT NOT NULL,
              job_type TEXT NOT NULL,
              args JSONB NOT NULL DEFAULT '{}'::jsonb,
              timeout_seconds INTEGER NOT NULL DEFAULT 30,
              status TEXT NOT NULL CHECK (status IN ('queued','leased','done','failed')),
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              lease_until TIMESTAMPTZ,
              result JSONB,
              completed_at TIMESTAMPTZ,
              idempotency_key TEXT
            )
            """
        )
        conn.execute(
            "ALTER TABLE ara_jobs ADD COLUMN IF NOT EXISTS idempotency_key TEXT"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ara_jobs_queue_idx "
            "ON ara_jobs(device_id, status, created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ara_jobs_lease_idx "
            "ON ara_jobs(lease_until) WHERE status='leased'"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ara_jobs_idempotency_idx "
            "ON ara_jobs(device_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
        )


def heartbeat(device_id, body):
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO ara_devices(device_id, heartbeat, seen_at)
            VALUES (%s, %s, now())
            ON CONFLICT(device_id) DO UPDATE
            SET heartbeat=EXCLUDED.heartbeat, seen_at=now()
            """,
            (device_id, json.dumps(body)),
        )


def create_job(device_id, job_type, args, timeout, idempotency_key=None):
    job_id = secrets.token_hex(16)
    key = (idempotency_key or "").strip() or None
    with connection() as conn:
        if key:
            existing = conn.execute(
                "SELECT * FROM ara_jobs WHERE device_id=%s AND idempotency_key=%s",
                (device_id, key),
            ).fetchone()
            if existing:
                return serialize(existing), False
        try:
            conn.execute(
                """
                INSERT INTO ara_jobs(
                  id, device_id, job_type, args, timeout_seconds, status, idempotency_key
                ) VALUES (%s,%s,%s,%s,%s,'queued',%s)
                """,
                (
                    job_id,
                    device_id,
                    job_type,
                    json.dumps(args or {}),
                    timeout,
                    key,
                ),
            )
        except psycopg.errors.UniqueViolation:
            conn.rollback()
            existing = conn.execute(
                "SELECT * FROM ara_jobs WHERE device_id=%s AND idempotency_key=%s",
                (device_id, key),
            ).fetchone()
            return serialize(existing), False
        row = conn.execute("SELECT * FROM ara_jobs WHERE id=%s", (job_id,)).fetchone()
        return serialize(row), True


def lease_next(device_id):
    with connection() as conn:
        conn.execute(
            """
            UPDATE ara_jobs
            SET status='queued', lease_until=NULL
            WHERE device_id=%s AND status='leased' AND lease_until < now()
            """,
            (device_id,),
        )
        row = conn.execute(
            """
            SELECT * FROM ara_jobs
            WHERE device_id=%s AND status='queued'
            ORDER BY created_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """,
            (device_id,),
        ).fetchone()
        if row is None:
            return None
        row = conn.execute(
            """
            UPDATE ara_jobs
            SET status='leased', lease_until=now() + (%s * interval '1 second')
            WHERE id=%s AND status='queued'
            RETURNING *
            """,
            (LEASE_SECONDS, row["id"]),
        ).fetchone()
        return serialize(row)


def submit_result(device_id, job_id, result):
    encoded = json.dumps(result)
    with connection() as conn:
        row = conn.execute(
            "SELECT status, result FROM ara_jobs WHERE id=%s AND device_id=%s FOR UPDATE",
            (job_id, device_id),
        ).fetchone()
        if row is None:
            return "missing"
        if row["status"] in ("done", "failed"):
            return "duplicate" if row["result"] == result else "conflict"
        if row["status"] != "leased":
            return "not_leased"
        updated = conn.execute(
            """
            UPDATE ara_jobs
            SET result=%s,
                status=CASE
                  WHEN COALESCE((%s::jsonb ->> 'ok')::boolean,false) THEN 'done'
                  ELSE 'failed'
                END,
                completed_at=now(),
                lease_until=NULL
            WHERE id=%s AND device_id=%s AND status='leased'
            RETURNING id
            """,
            (encoded, encoded, job_id, device_id),
        ).fetchone()
        return "stored" if updated else "not_leased"


def get_job(device_id, job_id):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM ara_jobs WHERE id=%s AND device_id=%s",
            (job_id, device_id),
        ).fetchone()
        return serialize(row) if row else None


def device_status(device_id):
    with connection() as conn:
        device = conn.execute(
            "SELECT heartbeat,seen_at FROM ara_devices WHERE device_id=%s",
            (device_id,),
        ).fetchone()
        queued = conn.execute(
            "SELECT count(*) AS n FROM ara_jobs WHERE device_id=%s AND status='queued'",
            (device_id,),
        ).fetchone()["n"]
        leased = conn.execute(
            "SELECT count(*) AS n FROM ara_jobs WHERE device_id=%s AND status='leased'",
            (device_id,),
        ).fetchone()["n"]
        return {
            "heartbeat": device["heartbeat"] if device else None,
            "seen_at": device["seen_at"].isoformat()
            if device and device["seen_at"]
            else None,
            "queued": queued,
            "leased": leased,
        }


def transactional_selftest():
    marker = "ara-selftest-" + secrets.token_hex(8)
    job_id = secrets.token_hex(16)
    with connection() as conn:
        conn.execute("SAVEPOINT ara_selftest")
        try:
            conn.execute(
                """
                INSERT INTO ara_jobs(id, device_id, job_type, args, timeout_seconds, status)
                VALUES (%s,%s,'ping','{}'::jsonb,30,'queued')
                """,
                (job_id, marker),
            )
            row = conn.execute(
                """
                SELECT id FROM ara_jobs
                WHERE device_id=%s AND status='queued'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """,
                (marker,),
            ).fetchone()
            if not row or row["id"] != job_id:
                raise RuntimeError("queue selection failed")
            conn.execute(
                """
                UPDATE ara_jobs
                SET status='leased', lease_until=now() + interval '30 seconds'
                WHERE id=%s
                """,
                (job_id,),
            )
            conn.execute(
                """
                UPDATE ara_jobs
                SET lease_until=now() - interval '1 second'
                WHERE id=%s
                """,
                (job_id,),
            )
            recovered = conn.execute(
                """
                UPDATE ara_jobs
                SET status='queued', lease_until=NULL
                WHERE id=%s AND status='leased' AND lease_until < now()
                RETURNING id
                """,
                (job_id,),
            ).fetchone()
            if not recovered:
                raise RuntimeError("lease recovery failed")
            conn.execute(
                "UPDATE ara_jobs SET status='leased' WHERE id=%s",
                (job_id,),
            )
            result = {"id": job_id, "ok": True, "output": "pong"}
            encoded = json.dumps(result)
            conn.execute(
                """
                UPDATE ara_jobs
                SET result=%s, status='done', completed_at=now(), lease_until=NULL
                WHERE id=%s AND status='leased'
                """,
                (encoded, job_id),
            )
            final = conn.execute(
                "SELECT status,result FROM ara_jobs WHERE id=%s",
                (job_id,),
            ).fetchone()
            if not final or final["status"] != "done" or final["result"] != result:
                raise RuntimeError("result persistence failed")
            return {
                "ok": True,
                "checks": {
                    "schema": True,
                    "queue": True,
                    "lease": True,
                    "lease_recovery": True,
                    "result": True,
                },
            }
        finally:
            conn.execute("ROLLBACK TO SAVEPOINT ara_selftest")


def serialize(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "type": row["job_type"],
        "args": row["args"],
        "timeout_seconds": row["timeout_seconds"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "lease_until": row["lease_until"].isoformat() if row["lease_until"] else None,
        "result": row["result"],
        "idempotency_key": row.get("idempotency_key") if hasattr(row, "get") else None,
    }
