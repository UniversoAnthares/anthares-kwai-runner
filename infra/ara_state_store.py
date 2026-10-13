import copy
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

FINAL = {"done", "failed", "expired"}
SAFE_RETRY_TYPES = {
    "ping", "system_info", "process_list", "clipboard_get",
    "file_stat", "file_list", "file_read", "file_read_chunk",
    "job_list", "job_status", "job_logs",
}


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_safe_retry(job_type):
    return str(job_type or "") in SAFE_RETRY_TYPES


class MemoryStore:
    """Reference implementation used by tests and as explicit dev fallback only."""
    def __init__(self, now_fn=None):
        self._lock = threading.RLock()
        self._devices = {}
        self._jobs = {}
        self._queue = {}
        self._now = now_fn or time.time

    def heartbeat(self, device_id, payload):
        row = dict(payload or {})
        row["seen_at"] = utcnow()
        row["_seen_epoch"] = self._now()
        with self._lock:
            self._devices[device_id] = row
        return copy.deepcopy(row)

    def status(self, device_id, freshness_seconds=45):
        with self._lock:
            self._reap(device_id)
            hb = copy.deepcopy(self._devices.get(device_id))
            queued = sum(1 for jid in self._queue.get(device_id, [])
                         if self._jobs.get(jid, {}).get("status") == "queued")
            uncertain = sum(1 for row in self._jobs.values()
                            if row["device_id"] == device_id and row.get("status") == "uncertain")
        connected = bool(hb and self._now() - hb.get("_seen_epoch", 0) <= freshness_seconds)
        if hb:
            hb.pop("_seen_epoch", None)
        return {"heartbeat": hb, "connected": connected, "queued": queued, "uncertain": uncertain}

    def enqueue(self, device_id, job_type, args=None, timeout_seconds=30,
                idempotency_key=None, job_id=None):
        now = self._now()
        timeout = max(1, min(int(timeout_seconds or 30), 120))
        with self._lock:
            if idempotency_key:
                for row in self._jobs.values():
                    if row["device_id"] == device_id and row.get("idempotency_key") == idempotency_key:
                        return copy.deepcopy(row)
            jid = job_id or uuid.uuid4().hex
            row = {
                "id": jid,
                "device_id": device_id,
                "type": job_type,
                "args": args or {},
                "timeout_seconds": timeout,
                "created_at": utcnow(),
                "created_epoch": now,
                "expires_epoch": now + timeout + 30,
                "status": "queued",
                "attempts": 0,
                "lease_until": None,
                "idempotency_key": idempotency_key,
                "result": None,
            }
            self._jobs[jid] = row
            self._queue.setdefault(device_id, []).append(jid)
            return copy.deepcopy(row)

    def _reap(self, device_id):
        now = self._now()
        for row in self._jobs.values():
            if row["device_id"] != device_id or row["status"] in FINAL or row["status"] == "uncertain":
                continue
            if now >= row["expires_epoch"]:
                row["status"] = "expired"
                row["lease_until"] = None
                continue
            if row["status"] == "leased" and row.get("lease_until") and now >= row["lease_until"]:
                row["lease_until"] = None
                if is_safe_retry(row["type"]):
                    row["status"] = "queued"
                    if row["id"] not in self._queue.setdefault(device_id, []):
                        self._queue[device_id].append(row["id"])
                else:
                    row["status"] = "uncertain"

    def lease_next(self, device_id, lease_seconds=35):
        lease_seconds = max(5, min(int(lease_seconds), 120))
        with self._lock:
            self._reap(device_id)
            q = self._queue.setdefault(device_id, [])
            while q:
                jid = q.pop(0)
                row = self._jobs.get(jid)
                if not row or row["status"] != "queued":
                    continue
                row["status"] = "leased"
                row["attempts"] += 1
                row["lease_until"] = self._now() + lease_seconds
                return copy.deepcopy(row)
            return None

    def complete(self, device_id, job_id, result):
        with self._lock:
            row = self._jobs.get(job_id)
            if not row or row["device_id"] != device_id:
                return None
            if row["status"] in FINAL:
                return copy.deepcopy(row)
            row["result"] = copy.deepcopy(result or {})
            row["status"] = "done" if bool((result or {}).get("ok")) else "failed"
            row["lease_until"] = None
            return copy.deepcopy(row)

    def get_job(self, device_id, job_id):
        with self._lock:
            self._reap(device_id)
            row = self._jobs.get(job_id)
            return copy.deepcopy(row) if row and row["device_id"] == device_id else None


class PostgresStore:
    """Durable implementation. Requires psycopg and ARA_DATABASE_URL/DATABASE_URL."""
    def __init__(self, dsn):
        import psycopg
        self.psycopg = psycopg
        self.dsn = dsn
        self._init_schema()

    def _conn(self):
        return self.psycopg.connect(self.dsn, autocommit=False)

    def _init_schema(self):
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
        with self._conn() as c, c.cursor() as cur:
            cur.execute(ddl)
            c.commit()

    def heartbeat(self, device_id, payload):
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO ara_devices(device_id,heartbeat,seen_at)
                   VALUES(%s,%s::jsonb,now())
                   ON CONFLICT(device_id) DO UPDATE SET heartbeat=excluded.heartbeat, seen_at=now()
                   RETURNING heartbeat, seen_at""",
                (device_id, json.dumps(payload or {})),
            )
            hb, seen = cur.fetchone()
            c.commit()
        hb = dict(hb)
        hb["seen_at"] = seen.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return hb

    def status(self, device_id, freshness_seconds=45):
        with self._conn() as c, c.cursor() as cur:
            self._reap(cur, device_id)
            cur.execute("SELECT heartbeat,seen_at FROM ara_devices WHERE device_id=%s", (device_id,))
            row = cur.fetchone()
            cur.execute("SELECT count(*) FROM ara_jobs WHERE device_id=%s AND status='queued'", (device_id,))
            queued = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM ara_jobs WHERE device_id=%s AND status='uncertain'", (device_id,))
            uncertain = cur.fetchone()[0]
            c.commit()
        if not row:
            return {"heartbeat": None, "connected": False, "queued": queued, "uncertain": uncertain}
        hb, seen = row
        hb = dict(hb)
        hb["seen_at"] = seen.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        connected = (datetime.now(timezone.utc) - seen).total_seconds() <= freshness_seconds
        return {"heartbeat": hb, "connected": connected, "queued": queued, "uncertain": uncertain}

    def enqueue(self, device_id, job_type, args=None, timeout_seconds=30,
                idempotency_key=None, job_id=None):
        timeout = max(1, min(int(timeout_seconds or 30), 120))
        jid = job_id or uuid.uuid4().hex
        with self._conn() as c, c.cursor() as cur:
            if idempotency_key:
                cur.execute("SELECT * FROM ara_jobs WHERE device_id=%s AND idempotency_key=%s",
                            (device_id, idempotency_key))
                existing = cur.fetchone()
                if existing:
                    cols = [d.name for d in cur.description]
                    c.commit()
                    return self._row(dict(zip(cols, existing)))
            cur.execute(
                """INSERT INTO ara_jobs(id,device_id,type,args,timeout_seconds,expires_at,status,idempotency_key)
                   VALUES(%s,%s,%s,%s::jsonb,%s,now()+(%s||' seconds')::interval,'queued',%s)
                   RETURNING *""",
                (jid, device_id, job_type, json.dumps(args or {}), timeout, timeout + 30, idempotency_key),
            )
            cols = [d.name for d in cur.description]
            row = self._row(dict(zip(cols, cur.fetchone())))
            c.commit()
            return row

    def _reap(self, cur, device_id):
        safe = list(SAFE_RETRY_TYPES)
        cur.execute(
            """UPDATE ara_jobs SET status='expired', lease_until=NULL
               WHERE device_id=%s AND status IN ('queued','leased') AND expires_at<=now()""",
            (device_id,),
        )
        cur.execute(
            """UPDATE ara_jobs SET status='queued', lease_until=NULL
               WHERE device_id=%s AND status='leased' AND lease_until<=now()
                 AND expires_at>now() AND type=ANY(%s)""",
            (device_id, safe),
        )
        cur.execute(
            """UPDATE ara_jobs SET status='uncertain', lease_until=NULL
               WHERE device_id=%s AND status='leased' AND lease_until<=now()
                 AND expires_at>now() AND NOT (type=ANY(%s))""",
            (device_id, safe),
        )

    def lease_next(self, device_id, lease_seconds=35):
        lease_seconds = max(5, min(int(lease_seconds), 120))
        with self._conn() as c, c.cursor() as cur:
            self._reap(cur, device_id)
            cur.execute(
                """SELECT id FROM ara_jobs
                   WHERE device_id=%s AND status='queued' AND expires_at>now()
                   ORDER BY created_at
                   FOR UPDATE SKIP LOCKED LIMIT 1""",
                (device_id,),
            )
            picked = cur.fetchone()
            if not picked:
                c.commit()
                return None
            cur.execute(
                """UPDATE ara_jobs SET status='leased', attempts=attempts+1,
                     lease_until=now()+(%s||' seconds')::interval
                   WHERE id=%s RETURNING *""",
                (lease_seconds, picked[0]),
            )
            cols = [d.name for d in cur.description]
            row = self._row(dict(zip(cols, cur.fetchone())))
            c.commit()
            return row

    def complete(self, device_id, job_id, result):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT status FROM ara_jobs WHERE id=%s AND device_id=%s FOR UPDATE", (job_id, device_id))
            found = cur.fetchone()
            if not found:
                c.commit()
                return None
            if found[0] in FINAL:
                cur.execute("SELECT * FROM ara_jobs WHERE id=%s", (job_id,))
            else:
                status = "done" if bool((result or {}).get("ok")) else "failed"
                cur.execute(
                    """UPDATE ara_jobs SET status=%s,result=%s::jsonb,lease_until=NULL
                       WHERE id=%s RETURNING *""",
                    (status, json.dumps(result or {}), job_id),
                )
            cols = [d.name for d in cur.description]
            row = self._row(dict(zip(cols, cur.fetchone())))
            c.commit()
            return row

    def get_job(self, device_id, job_id):
        with self._conn() as c, c.cursor() as cur:
            self._reap(cur, device_id)
            cur.execute("SELECT * FROM ara_jobs WHERE id=%s AND device_id=%s", (job_id, device_id))
            row = cur.fetchone()
            if not row:
                c.commit()
                return None
            cols = [d.name for d in cur.description]
            out = self._row(dict(zip(cols, row)))
            c.commit()
            return out

    @staticmethod
    def _row(row):
        if not row:
            return None
        for k in ("created_at", "expires_at", "lease_until"):
            if row.get(k):
                row[k] = row[k].astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return row


def build_store():
    dsn = os.getenv("ARA_DATABASE_URL") or os.getenv("DATABASE_URL")
    if dsn:
        return PostgresStore(dsn)
    if os.getenv("ARA_ALLOW_VOLATILE", "") == "1":
        return MemoryStore()
    raise RuntimeError("ARA durable state unavailable: set ARA_DATABASE_URL or explicit ARA_ALLOW_VOLATILE=1")
