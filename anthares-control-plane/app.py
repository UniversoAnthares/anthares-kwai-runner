from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

SCHEMA_VERSION = 1


def _now() -> int:
    return int(time.time())


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _payload_hash(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _retry_delay(attempt: int, base: int = 5, cap: int = 300) -> int:
    return min(cap, base * (2 ** max(0, attempt - 1)))


def create_app(db_path: str | None = None, token: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("ANTHARES_DB_PATH", "/tmp/anthares-control-plane.db")
    app.config["TOKEN"] = token if token is not None else os.environ.get("ANTHARES_CONTROL_TOKEN", "")
    app.config["PROVIDER"] = os.environ.get("ANTHARES_PROVIDER", "anthares-own")
    app.config["INSTANCE_ID"] = os.environ.get("ANTHARES_INSTANCE_ID", secrets.token_hex(6))
    app.config["DEFAULT_ROLE"] = os.environ.get("ANTHARES_ROLE", "active")
    app.config["LEASE_TTL"] = int(os.environ.get("ANTHARES_LEASE_TTL", "120"))
    app.config["EXECUTOR_TTL"] = int(os.environ.get("ANTHARES_EXECUTOR_TTL", "180"))

    def connect() -> sqlite3.Connection:
        p = Path(app.config["DB_PATH"])
        p.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(str(p), timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def init_db() -> None:
        with connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    dedupe_key TEXT UNIQUE,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 100,
                    status TEXT NOT NULL,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 5,
                    available_at INTEGER NOT NULL,
                    lease_owner TEXT,
                    lease_token TEXT,
                    lease_generation INTEGER NOT NULL DEFAULT 0,
                    lease_until INTEGER,
                    result_json TEXT,
                    error_json TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    completed_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_claim
                ON jobs(status, available_at, priority, created_at);
                CREATE TABLE IF NOT EXISTS executors (
                    id TEXT PRIMARY KEY,
                    capabilities_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    last_seen INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    event_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_job ON events(job_id, seq);
                """
            )
            now = _now()
            db.execute(
                "INSERT OR IGNORE INTO meta(key,value,updated_at) VALUES('role',?,?)",
                (app.config["DEFAULT_ROLE"], now),
            )
            db.execute(
                "INSERT OR IGNORE INTO meta(key,value,updated_at) VALUES('epoch','1',?)",
                (now,),
            )

    def require_auth() -> tuple[bool, Any | None]:
        expected = app.config["TOKEN"]
        if not expected:
            return False, (jsonify({"error": "control_token_not_configured"}), 503)
        header = request.headers.get("Authorization", "")
        supplied = header[7:] if header.startswith("Bearer ") else ""
        if not hmac.compare_digest(supplied, expected):
            return False, (jsonify({"error": "unauthorized"}), 401)
        return True, None

    def event(db: sqlite3.Connection, job_id: str | None, event_type: str, data: Any) -> None:
        db.execute(
            "INSERT INTO events(job_id,event_type,data_json,created_at) VALUES(?,?,?,?)",
            (job_id, event_type, _canonical(data), _now()),
        )

    def role(db: sqlite3.Connection) -> tuple[str, int]:
        r = db.execute("SELECT key,value FROM meta WHERE key IN ('role','epoch')").fetchall()
        values = {x["key"]: x["value"] for x in r}
        return values.get("role", "standby"), int(values.get("epoch", "0"))

    def row_to_job(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for k in ("payload_json", "result_json", "error_json"):
            raw = d.pop(k)
            d[k[:-5]] = json.loads(raw) if raw else None
        return d

    def fenced_job(db: sqlite3.Connection, job_id: str, body: dict[str, Any]) -> sqlite3.Row | None:
        return db.execute(
            """SELECT * FROM jobs WHERE id=? AND lease_owner=? AND lease_token=?
               AND lease_generation=? AND lease_until>? AND status IN ('leased','running')""",
            (
                job_id,
                body.get("executor_id"),
                body.get("lease_token"),
                int(body.get("lease_generation", -1)),
                _now(),
            ),
        ).fetchone()

    init_db()

    @app.get("/health")
    def health():
        with connect() as db:
            current_role, epoch = role(db)
            counts = {
                r["status"]: r["n"]
                for r in db.execute("SELECT status,COUNT(*) n FROM jobs GROUP BY status").fetchall()
            }
        return jsonify(
            {
                "ok": True,
                "schema_version": SCHEMA_VERSION,
                "provider": app.config["PROVIDER"],
                "instance_id": app.config["INSTANCE_ID"],
                "role": current_role,
                "epoch": epoch,
                "jobs": counts,
                "time": _now(),
            }
        )

    @app.post("/v1/admin/role")
    def set_role():
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        new_role = body.get("role")
        if new_role not in {"active", "standby", "draining"}:
            return jsonify({"error": "invalid_role"}), 400
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            _, epoch = role(db)
            epoch += 1
            now = _now()
            db.execute("UPDATE meta SET value=?,updated_at=? WHERE key='role'", (new_role, now))
            db.execute("UPDATE meta SET value=?,updated_at=? WHERE key='epoch'", (str(epoch), now))
            event(db, None, "role_changed", {"role": new_role, "epoch": epoch})
            db.execute("COMMIT")
        return jsonify({"role": new_role, "epoch": epoch})

    @app.post("/v1/jobs")
    def create_job():
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        idem = str(body.get("idempotency_key", "")).strip()
        kind = str(body.get("kind", "")).strip()
        payload = body.get("payload", {})
        dedupe_key = body.get("dedupe_key")
        if not idem or not kind:
            return jsonify({"error": "idempotency_key_and_kind_required"}), 400
        ph = _payload_hash(payload)
        job_id = hashlib.sha256(idem.encode("utf-8")).hexdigest()[:32]
        now = _now()
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM jobs WHERE idempotency_key=? OR (dedupe_key IS NOT NULL AND dedupe_key=?) LIMIT 1",
                (idem, dedupe_key),
            ).fetchone()
            if existing:
                if existing["idempotency_key"] == idem and existing["payload_hash"] != ph:
                    db.execute("ROLLBACK")
                    return jsonify({"error": "idempotency_conflict", "job_id": existing["id"]}), 409
                db.execute("COMMIT")
                return jsonify({"created": False, "job": row_to_job(existing)}), 200
            db.execute(
                """INSERT INTO jobs(
                    id,idempotency_key,dedupe_key,kind,payload_json,payload_hash,priority,status,
                    max_attempts,available_at,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,'queued',?,?,?,?)""",
                (
                    job_id,
                    idem,
                    dedupe_key,
                    kind,
                    _canonical(payload),
                    ph,
                    int(body.get("priority", 100)),
                    int(body.get("max_attempts", 5)),
                    int(body.get("available_at", now)),
                    now,
                    now,
                ),
            )
            event(db, job_id, "job_created", {"kind": kind, "dedupe_key": dedupe_key})
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            db.execute("COMMIT")
        return jsonify({"created": True, "job": row_to_job(row)}), 201

    @app.get("/v1/jobs/<job_id>")
    def get_job(job_id: str):
        ok, err = require_auth()
        if not ok:
            return err
        with connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return jsonify({"error": "not_found"}), 404
        return jsonify(row_to_job(row))

    @app.post("/v1/jobs/next")
    def claim_job():
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        executor_id = str(body.get("executor_id", "")).strip()
        kinds = body.get("kinds") or []
        if not executor_id:
            return jsonify({"error": "executor_id_required"}), 400
        now = _now()
        ttl = max(15, min(int(body.get("ttl_seconds", app.config["LEASE_TTL"])), 900))
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current_role, epoch = role(db)
            if current_role != "active":
                db.execute("ROLLBACK")
                return jsonify({"error": "provider_not_active", "role": current_role, "epoch": epoch}), 503
            expired = db.execute(
                """SELECT id FROM jobs WHERE status IN ('leased','running')
                   AND lease_until IS NOT NULL AND lease_until<=?""",
                (now,),
            ).fetchall()
            for x in expired:
                db.execute(
                    """UPDATE jobs SET status='queued',lease_owner=NULL,lease_token=NULL,lease_until=NULL,
                       updated_at=? WHERE id=?""",
                    (now, x["id"]),
                )
                event(db, x["id"], "lease_expired", {})
            sql = "SELECT * FROM jobs WHERE status='queued' AND available_at<=?"
            params: list[Any] = [now]
            if kinds:
                placeholders = ",".join("?" for _ in kinds)
                sql += f" AND kind IN ({placeholders})"
                params.extend(str(x) for x in kinds)
            sql += " ORDER BY priority ASC, created_at ASC LIMIT 1"
            row = db.execute(sql, params).fetchone()
            if not row:
                db.execute("COMMIT")
                return ("", 204)
            lease_token = secrets.token_urlsafe(24)
            generation = int(row["lease_generation"]) + 1
            db.execute(
                """UPDATE jobs SET status='leased',attempt=attempt+1,lease_owner=?,lease_token=?,
                   lease_generation=?,lease_until=?,updated_at=? WHERE id=?""",
                (executor_id, lease_token, generation, now + ttl, now, row["id"]),
            )
            event(db, row["id"], "job_leased", {"executor_id": executor_id, "generation": generation, "epoch": epoch})
            claimed = db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
            db.execute("COMMIT")
        result = row_to_job(claimed)
        result["lease_token"] = lease_token
        result["provider_epoch"] = epoch
        return jsonify(result)

    @app.post("/v1/jobs/<job_id>/heartbeat")
    def job_heartbeat(job_id: str):
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        ttl = max(15, min(int(body.get("ttl_seconds", app.config["LEASE_TTL"])), 900))
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = fenced_job(db, job_id, body)
            if not row:
                db.execute("ROLLBACK")
                return jsonify({"error": "stale_or_invalid_lease"}), 409
            now = _now()
            db.execute(
                "UPDATE jobs SET status='running',lease_until=?,updated_at=? WHERE id=?",
                (now + ttl, now, job_id),
            )
            event(db, job_id, "lease_heartbeat", {"executor_id": body.get("executor_id")})
            db.execute("COMMIT")
        return jsonify({"ok": True, "lease_until": now + ttl})

    @app.post("/v1/jobs/<job_id>/complete")
    def complete_job(job_id: str):
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = fenced_job(db, job_id, body)
            if not row:
                db.execute("ROLLBACK")
                return jsonify({"error": "stale_or_invalid_lease"}), 409
            now = _now()
            result = body.get("result", {})
            db.execute(
                """UPDATE jobs SET status='completed',result_json=?,error_json=NULL,completed_at=?,
                   lease_owner=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?""",
                (_canonical(result), now, now, job_id),
            )
            event(db, job_id, "job_completed", {"executor_id": body.get("executor_id"), "result": result})
            db.execute("COMMIT")
        return jsonify({"ok": True, "status": "completed"})

    @app.post("/v1/jobs/<job_id>/fail")
    def fail_job(job_id: str):
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = fenced_job(db, job_id, body)
            if not row:
                db.execute("ROLLBACK")
                return jsonify({"error": "stale_or_invalid_lease"}), 409
            now = _now()
            dead = int(row["attempt"]) >= int(row["max_attempts"])
            status = "dead" if dead else "queued"
            available_at = now if dead else now + _retry_delay(int(row["attempt"]))
            error = body.get("error", {})
            db.execute(
                """UPDATE jobs SET status=?,error_json=?,available_at=?,lease_owner=NULL,
                   lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?""",
                (status, _canonical(error), available_at, now, job_id),
            )
            event(db, job_id, "job_failed", {"executor_id": body.get("executor_id"), "status": status, "error": error})
            db.execute("COMMIT")
        return jsonify({"ok": True, "status": status, "available_at": available_at})

    @app.post("/v1/executors/heartbeat")
    def executor_heartbeat():
        ok, err = require_auth()
        if not ok:
            return err
        body = request.get_json(silent=True) or {}
        executor_id = str(body.get("executor_id", "")).strip()
        if not executor_id:
            return jsonify({"error": "executor_id_required"}), 400
        now = _now()
        with connect() as db:
            db.execute(
                """INSERT INTO executors(id,capabilities_json,metadata_json,last_seen,created_at,updated_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET capabilities_json=excluded.capabilities_json,
                   metadata_json=excluded.metadata_json,last_seen=excluded.last_seen,updated_at=excluded.updated_at""",
                (
                    executor_id,
                    _canonical(body.get("capabilities", [])),
                    _canonical(body.get("metadata", {})),
                    now,
                    now,
                    now,
                ),
            )
        return jsonify({"ok": True, "server_time": now})

    @app.get("/v1/executors")
    def list_executors():
        ok, err = require_auth()
        if not ok:
            return err
        now = _now()
        with connect() as db:
            rows = db.execute("SELECT * FROM executors ORDER BY id").fetchall()
        data = []
        for r in rows:
            d = dict(r)
            d["capabilities"] = json.loads(d.pop("capabilities_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            d["healthy"] = now - int(d["last_seen"]) <= app.config["EXECUTOR_TTL"]
            data.append(d)
        return jsonify({"executors": data})

    @app.get("/v1/stats")
    def stats():
        ok, err = require_auth()
        if not ok:
            return err
        with connect() as db:
            current_role, epoch = role(db)
            counts = {
                r["status"]: r["n"]
                for r in db.execute("SELECT status,COUNT(*) n FROM jobs GROUP BY status").fetchall()
            }
            total_events = db.execute("SELECT COUNT(*) n FROM events").fetchone()["n"]
        return jsonify({"role": current_role, "epoch": epoch, "jobs": counts, "events": total_events})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
