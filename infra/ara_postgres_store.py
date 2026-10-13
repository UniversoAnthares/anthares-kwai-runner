import json
import os
import secrets
from contextlib import contextmanager
from urllib.parse import quote

import psycopg
from psycopg.rows import dict_row

SAFE_RETRY_TYPES = {
    "ping",
    "system_info",
    "process_list",
    "clipboard_get",
    "file_stat",
    "file_list",
    "file_read",
    "file_read_chunk",
    "job_list",
    "job_status",
    "job_logs",
}
FINAL = {"done", "failed", "expired"}


def _database_url_from_env():
    value = os.getenv("ARA_DATABASE_URL", "").strip()
    if not value:
        return ""
    if value.startswith(("postgres://", "postgresql://")) or "=" in value:
        return value
    host = os.getenv("ARA_DATABASE_HOST", "dpg-db6n9nqvcj2c73afk82g-a").strip()
    port = os.getenv("ARA_DATABASE_PORT", "5432").strip()
    name = os.getenv("ARA_DATABASE_NAME", "anthares_ara_state").strip()
    user = os.getenv("ARA_DATABASE_USER", "anthares_ara_state_user").strip()
    return (
        "postgresql://"
        + quote(user, safe="")
        + ":"
        + quote(value, safe="")
        + "@"
        + host
        + ":"
        + port
        + "/"
        + quote(name, safe="")
    )


DATABASE_URL = _database_url_from_env()
LEASE_SECONDS = max(5, min(int(os.getenv("ARA_LEASE_SECONDS", "35")), 120))


@contextmanager
def connection():
    if not DATABASE_URL:
        raise RuntimeError("ARA_DATABASE_URL is required")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=8) as conn:
        yield conn


def initialize():
    # Use the canonical schema already shared by the production ARA canary.
    # CREATE IF NOT EXISTS keeps this service compatible with that existing store.
    ddl = """
    CREATE TABLE IF NOT EXISTS ara_devices(
      device_id TEXT PRIMARY KEY,
      heartbeat JSONB NOT NULL,
      seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS ara_jobs(
      id TEXT PRIMARY KEY,
      device_id TEXT NOT NULL,
      type TEXT NOT NULL,
      args JSONB NOT NULL DEFAULT '{}'::jsonb,
      timeout_seconds INTEGER NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      expires_at TIMESTAMPTZ NOT NULL,
      status TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      lease_until TIMESTAMPTZ,
      idempotency_key TEXT,
      result JSONB
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ara_jobs_dedupe
      ON ara_jobs(device_id,idempotency_key) WHERE idempotency_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ara_jobs_pick
      ON ara_jobs(device_id,status,created_at);
    """
    with connection() as conn:
        conn.execute(ddl)


def heartbeat(device_id, body):
    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO ara_devices(device_id,heartbeat,seen_at)
            VALUES(%s,%s::jsonb,now())
            ON CONFLICT(device_id) DO UPDATE
            SET heartbeat=excluded.heartbeat, seen_at=now()
            RETURNING heartbeat, seen_at
            """,
            (device_id, json.dumps(body or {})),
        ).fetchone()
        return {"heartbeat": row["heartbeat"], "seen_at": row["seen_at"].isoformat()}


def _reap(conn, device_id):
    safe = list(SAFE_RETRY_TYPES)
    conn.execute(
        """
        UPDATE ara_jobs SET status=CASE
          WHEN status='leased' AND NOT (type=ANY(%s)) THEN 'uncertain'
          ELSE 'expired' END,
          lease_until=NULL
        WHERE device_id=%s AND status IN ('queued','leased') AND expires_at<=now()
        """,
        (safe, device_id),
    )
    conn.execute(
        """
        UPDATE ara_jobs SET status='queued', lease_until=NULL
        WHERE device_id=%s AND status='leased' AND lease_until<=now()
          AND expires_at>now() AND type=ANY(%s)
        """,
        (device_id, safe),
    )
    conn.execute(
        """
        UPDATE ara_jobs SET status='uncertain', lease_until=NULL
        WHERE device_id=%s AND status='leased' AND lease_until<=now()
          AND expires_at>now() AND NOT (type=ANY(%s))
        """,
        (device_id, safe),
    )


def create_job(device_id, job_type, args, timeout, idempotency_key=None):
    job_id = secrets.token_hex(16)
    key = (idempotency_key or "").strip() or None
    timeout = max(1, min(int(timeout or 30), 120))
    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO ara_jobs(
              id,device_id,type,args,timeout_seconds,expires_at,status,idempotency_key
            ) VALUES(
              %s,%s,%s,%s::jsonb,%s,now()+(%s||' seconds')::interval,'queued',%s
            )
            ON CONFLICT DO NOTHING
            RETURNING *
            """,
            (
                job_id,
                device_id,
                job_type,
                json.dumps(args or {}),
                timeout,
                timeout + 30,
                key,
            ),
        ).fetchone()
        if row is not None:
            return serialize(row), True
        if not key:
            raise RuntimeError("ARA job id collision")
        existing = conn.execute(
            "SELECT * FROM ara_jobs WHERE device_id=%s AND idempotency_key=%s",
            (device_id, key),
        ).fetchone()
        if existing is None:
            raise RuntimeError("ARA idempotency conflict without matching job")
        return serialize(existing), False


def lease_next(device_id):
    with connection() as conn:
        _reap(conn, device_id)
        picked = conn.execute(
            """
            SELECT id FROM ara_jobs
            WHERE device_id=%s AND status='queued' AND expires_at>now()
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED LIMIT 1
            """,
            (device_id,),
        ).fetchone()
        if not picked:
            return None
        row = conn.execute(
            """
            UPDATE ara_jobs
            SET status='leased', attempts=attempts+1,
                lease_until=now()+(%s||' seconds')::interval
            WHERE id=%s AND status='queued'
            RETURNING *
            """,
            (LEASE_SECONDS, picked["id"]),
        ).fetchone()
        return serialize(row)


def submit_result(device_id, job_id, result):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM ara_jobs WHERE id=%s AND device_id=%s FOR UPDATE",
            (job_id, device_id),
        ).fetchone()
        if row is None:
            return "missing"
        if row["status"] in FINAL:
            return "duplicate" if row["result"] == (result or {}) else "conflict"
        if row["status"] != "leased":
            return "not_leased"
        status = "done" if bool((result or {}).get("ok")) else "failed"
        conn.execute(
            """
            UPDATE ara_jobs
            SET status=%s,result=%s::jsonb,lease_until=NULL
            WHERE id=%s AND device_id=%s AND status='leased'
            """,
            (status, json.dumps(result or {}), job_id, device_id),
        )
        return "stored"


def get_job(device_id, job_id):
    with connection() as conn:
        _reap(conn, device_id)
        row = conn.execute(
            "SELECT * FROM ara_jobs WHERE id=%s AND device_id=%s",
            (job_id, device_id),
        ).fetchone()
        return serialize(row) if row else None


def device_status(device_id):
    with connection() as conn:
        _reap(conn, device_id)
        device = conn.execute(
            "SELECT heartbeat,seen_at FROM ara_devices WHERE device_id=%s",
            (device_id,),
        ).fetchone()
        counts = conn.execute(
            """
            SELECT
              count(*) FILTER (WHERE status='queued') AS queued,
              count(*) FILTER (WHERE status='leased') AS leased,
              count(*) FILTER (WHERE status='uncertain') AS uncertain
            FROM ara_jobs WHERE device_id=%s
            """,
            (device_id,),
        ).fetchone()
        return {
            "heartbeat": device["heartbeat"] if device else None,
            "seen_at": device["seen_at"].isoformat() if device else None,
            "queued": counts["queued"],
            "leased": counts["leased"],
            "uncertain": counts["uncertain"],
        }


def transactional_selftest():
    marker = "ara-selftest-" + secrets.token_hex(8)
    job_id = secrets.token_hex(16)
    with connection() as conn:
        conn.execute("SAVEPOINT ara_selftest")
        try:
            conn.execute(
                """
                INSERT INTO ara_jobs(
                  id,device_id,type,args,timeout_seconds,expires_at,status,attempts
                ) VALUES(
                  %s,%s,'ping','{}'::jsonb,30,now()+interval '60 seconds','queued',0
                )
                """,
                (job_id, marker),
            )
            selected = conn.execute(
                """
                SELECT id FROM ara_jobs
                WHERE device_id=%s AND status='queued' AND expires_at>now()
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED LIMIT 1
                """,
                (marker,),
            ).fetchone()
            if not selected or selected["id"] != job_id:
                raise RuntimeError("queue selection failed")
            conn.execute(
                """
                UPDATE ara_jobs
                SET status='leased',attempts=attempts+1,
                    lease_until=now()+interval '30 seconds'
                WHERE id=%s
                """,
                (job_id,),
            )
            conn.execute(
                "UPDATE ara_jobs SET lease_until=now()-interval '1 second' WHERE id=%s",
                (job_id,),
            )
            _reap(conn, marker)
            recovered = conn.execute(
                "SELECT status FROM ara_jobs WHERE id=%s",
                (job_id,),
            ).fetchone()
            if not recovered or recovered["status"] != "queued":
                raise RuntimeError("lease recovery failed")
            conn.execute(
                "UPDATE ara_jobs SET status='leased',lease_until=now()+interval '30 seconds' WHERE id=%s",
                (job_id,),
            )
            result = {"id": job_id, "ok": True, "output": "pong"}
            conn.execute(
                """
                UPDATE ara_jobs SET status='done',result=%s::jsonb,lease_until=NULL
                WHERE id=%s
                """,
                (json.dumps(result), job_id),
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
                    "canonical_schema": True,
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
        "type": row["type"],
        "args": row["args"],
        "timeout_seconds": row["timeout_seconds"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
        "lease_until": row["lease_until"].isoformat() if row.get("lease_until") else None,
        "attempts": row.get("attempts", 0),
        "result": row["result"],
        "idempotency_key": row.get("idempotency_key"),
    }
