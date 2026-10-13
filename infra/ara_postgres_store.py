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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ara_devices (
              device_id TEXT PRIMARY KEY, heartbeat JSONB, seen_at TIMESTAMPTZ
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ara_jobs (
              id TEXT PRIMARY KEY, device_id TEXT NOT NULL, job_type TEXT NOT NULL,
              args JSONB NOT NULL DEFAULT '{}'::jsonb, timeout_seconds INTEGER NOT NULL DEFAULT 30,
              status TEXT NOT NULL CHECK (status IN ('queued','leased','done','failed')),
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(), lease_until TIMESTAMPTZ,
              result JSONB, completed_at TIMESTAMPTZ
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ara_jobs_queue_idx ON ara_jobs(device_id, status, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS ara_jobs_lease_idx ON ara_jobs(lease_until) WHERE status='leased'")


def heartbeat(device_id, body):
    with connection() as conn:
        conn.execute("""
          INSERT INTO ara_devices(device_id, heartbeat, seen_at) VALUES (%s, %s, now())
          ON CONFLICT(device_id) DO UPDATE SET heartbeat=EXCLUDED.heartbeat, seen_at=now()
        """, (device_id, json.dumps(body)))


def create_job(device_id, job_type, args, timeout):
    job_id = secrets.token_hex(16)
    with connection() as conn:
        conn.execute("""
          INSERT INTO ara_jobs(id, device_id, job_type, args, timeout_seconds, status)
          VALUES (%s,%s,%s,%s,%s,'queued')
        """, (job_id, device_id, job_type, json.dumps(args or {}), timeout))
        row = conn.execute("SELECT * FROM ara_jobs WHERE id=%s", (job_id,)).fetchone()
        return serialize(row)


def lease_next(device_id):
    with connection() as conn:
        # Expired leases return to the queue, so a process restart cannot strand jobs.
        conn.execute("""
          UPDATE ara_jobs SET status='queued', lease_until=NULL
          WHERE device_id=%s AND status='leased' AND lease_until < now()
        """, (device_id,))
        row = conn.execute("""
          SELECT * FROM ara_jobs
          WHERE device_id=%s AND status='queued'
          ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1
        """, (device_id,)).fetchone()
        if row is None:
            return None
        row = conn.execute("""
          UPDATE ara_jobs SET status='leased', lease_until=now() + (%s * interval '1 second')
          WHERE id=%s RETURNING *
        """, (LEASE_SECONDS, row["id"])).fetchone()
        return serialize(row)


def submit_result(device_id, job_id, result):
    with connection() as conn:
        row = conn.execute("""
          UPDATE ara_jobs SET result=%s,
            status=CASE WHEN COALESCE((%s::jsonb ->> 'ok')::boolean,false) THEN 'done' ELSE 'failed' END,
            completed_at=now(), lease_until=NULL
          WHERE id=%s AND device_id=%s AND status IN ('leased','done','failed')
          RETURNING id,status
        """, (json.dumps(result), json.dumps(result), job_id, device_id)).fetchone()
        return row is not None


def get_job(device_id, job_id):
    with connection() as conn:
        row = conn.execute("SELECT * FROM ara_jobs WHERE id=%s AND device_id=%s", (job_id, device_id)).fetchone()
        return serialize(row) if row else None


def device_status(device_id):
    with connection() as conn:
        device = conn.execute("SELECT heartbeat,seen_at FROM ara_devices WHERE device_id=%s", (device_id,)).fetchone()
        queued = conn.execute("SELECT count(*) AS n FROM ara_jobs WHERE device_id=%s AND status='queued'", (device_id,)).fetchone()["n"]
        return {"heartbeat": device["heartbeat"] if device else None, "seen_at": device["seen_at"].isoformat() if device and device["seen_at"] else None, "queued": queued}


def serialize(row):
    if not row:
        return None
    return {
      "id": row["id"], "device_id": row["device_id"], "type": row["job_type"],
      "args": row["args"], "timeout_seconds": row["timeout_seconds"],
      "status": row["status"], "created_at": row["created_at"].isoformat(),
      "lease_until": row["lease_until"].isoformat() if row["lease_until"] else None,
      "result": row["result"]
    }
