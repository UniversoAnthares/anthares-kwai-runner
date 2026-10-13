"""Anthares remote Chromium executor.

Fail-closed authenticated API, single-writer fenced jobs, expiring leases,
loopback-only CDP, encrypted cross-host profile snapshots and read-only Kwai
verification. No endpoint publishes social content.
"""
import hmac
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import threading
import time
import urllib.request
from flask import Flask, jsonify, request

import profile_store
import kwai_probe

app = Flask(__name__)
TOKEN = os.getenv("ANTHARES_EXECUTOR_TOKEN", "")
IDENTITY = os.getenv("ANTHARES_EXECUTOR_ID", "reserva-01")
DB = os.getenv("STATE_DB", "/data/state/jobs.sqlite3")
PROFILE = os.getenv("CHROME_PROFILE_DIR", "/data/profile")
PORT = int(os.getenv("PORT", "8080"))
MEMORY_LIMIT = int(os.getenv("MEMORY_LIMIT_BYTES", "1073741824"))
LEASE_TTL = max(30, min(int(os.getenv("LEASE_TTL_SECONDS", "180")), 1800))
CDP = "http://127.0.0.1:9222"
lock = threading.RLock()
chrome = None

if not TOKEN or len(TOKEN) < 20:
    raise RuntimeError("ANTHARES_EXECUTOR_TOKEN must contain at least 20 characters")


def db():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, lease TEXT NOT NULL, generation INTEGER NOT NULL,
        status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
        result TEXT, heartbeat_at REAL, lease_expires REAL)""")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    if "heartbeat_at" not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN heartbeat_at REAL")
    if "lease_expires" not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN lease_expires REAL")
    now = time.time()
    conn.execute("UPDATE jobs SET heartbeat_at=COALESCE(heartbeat_at,updated), lease_expires=COALESCE(lease_expires,updated+?) WHERE status='leased'", (LEASE_TTL,))
    conn.execute("UPDATE jobs SET status='expired',updated=? WHERE status='leased' AND lease_expires<=?", (now, now))
    return conn


def authorized():
    header = request.headers.get("Authorization", "")
    supplied = header[7:] if header.startswith("Bearer ") else ""
    return hmac.compare_digest(supplied, TOKEN)


@app.before_request
def authorize():
    if request.path != "/health" and not authorized():
        return jsonify(error="unauthorized"), 401


def mem_bytes():
    for candidate in ("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            return int(Path(candidate).read_text().strip())
        except (OSError, ValueError):
            pass
    return 0


def browser_ready():
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=1.5) as response:
            return bool(json.load(response).get("Browser"))
    except (OSError, ValueError):
        return False


def expire_stale(conn, now=None):
    now = now or time.time()
    conn.execute("UPDATE jobs SET status='expired',updated=? WHERE status='leased' AND lease_expires IS NOT NULL AND lease_expires<=?", (now, now))


def begin(conn):
    conn.execute("BEGIN IMMEDIATE")


def rollback(conn):
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def valid_fence(jid, lease, generation):
    return bool(jid) and len(jid) <= 128 and 20 <= len(lease) <= 256 and type(generation) is int and generation >= 1


@app.get("/health")
def health():
    return jsonify(ok=True, executor=IDENTITY, chromium_ready=browser_ready(), memory_bytes=mem_bytes(), continuous_runner=True, lease_ttl_seconds=LEASE_TTL, encrypted_profile_store_configured=profile_store.configured())


@app.post("/v1/browser/start")
def start_browser():
    global chrome
    with lock:
        if browser_ready():
            return jsonify(ok=True, reused=True)
        if mem_bytes() and mem_bytes() >= MEMORY_LIMIT:
            return jsonify(ok=False, error="memory_guard"), 503
        if chrome and chrome.poll() is None:
            return jsonify(ok=False, error="chromium_starting"), 409
        Path(PROFILE).mkdir(parents=True, exist_ok=True)
        chrome = subprocess.Popen([
            "chromium", "--headless=new", "--no-sandbox", "--no-first-run",
            "--disable-dev-shm-usage", "--disable-background-networking",
            "--disable-extensions", "--disable-gpu", "--disable-features=Translate",
            "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=9222",
            "--user-data-dir=" + PROFILE, "about:blank"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(40):
            if browser_ready():
                return jsonify(ok=True, reused=False)
            if chrome.poll() is not None:
                chrome = None
                return jsonify(ok=False, error="chromium_exited"), 503
            time.sleep(.25)
        return jsonify(ok=False, error="chromium_start_timeout"), 503


@app.post("/v1/browser/stop")
def stop_browser():
    global chrome
    with lock:
        if chrome and chrome.poll() is None:
            os.killpg(chrome.pid, signal.SIGTERM)
            try:
                chrome.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(chrome.pid, signal.SIGKILL)
                chrome.wait(timeout=3)
        chrome = None
        return jsonify(ok=True, chromium_ready=browser_ready())


@app.post("/v1/profile/restore")
def restore_profile():
    with lock:
        if browser_ready():
            return jsonify(ok=False, error="browser_must_be_stopped"), 409
        try:
            result = profile_store.restore(PROFILE)
        except Exception as exc:
            return jsonify(ok=False, error="profile_restore_failed", detail=str(exc)[:80]), 502
        return jsonify(result), 200 if result.get("ok") else 503


@app.post("/v1/profile/snapshot")
def snapshot_profile():
    with lock:
        if browser_ready():
            return jsonify(ok=False, error="browser_must_be_stopped"), 409
        try:
            result = profile_store.backup(PROFILE)
        except Exception as exc:
            return jsonify(ok=False, error="profile_snapshot_failed", detail=str(exc)[:80]), 502
        return jsonify(result), 200 if result.get("ok") else 503


@app.post("/v1/kwai/session/import")
def import_kwai_session():
    if not browser_ready():
        return jsonify(ok=False, error="browser_not_ready"), 409
    if request.content_length is not None and request.content_length > 600 * 1024:
        return jsonify(ok=False, error="session_payload_too_large"), 413
    state = request.get_json(silent=True)
    if not isinstance(state, dict):
        return jsonify(ok=False, error="invalid_session_payload"), 400
    try:
        result = kwai_probe.import_state(state)
        return jsonify(result), 200
    except (ValueError, TypeError) as exc:
        return jsonify(ok=False, error="invalid_session_state", detail=str(exc)[:80]), 400
    except Exception as exc:
        return jsonify(ok=False, error="session_import_failed", detail=str(exc)[:80]), 502


@app.post("/v1/kwai/probe")
def probe_kwai():
    if not browser_ready():
        return jsonify(ok=False, error="browser_not_ready"), 409
    try:
        result = kwai_probe.probe()
        return jsonify(result), 200
    except Exception as exc:
        return jsonify(ok=False, identity_verified=False, upload_surface_verified=False, error="kwai_probe_failed", detail=str(exc)[:100], read_only=True), 502


@app.post("/v1/jobs")
def create_job():
    payload = request.get_json(silent=True) or {}
    jid = str(payload.get("id", ""))
    lease = str(payload.get("lease", ""))
    generation = payload.get("generation")
    if not valid_fence(jid, lease, generation):
        return jsonify(error="invalid_job_fencing"), 400
    now = time.time()
    with lock, db() as conn:
        try:
            begin(conn)
            expire_stale(conn, now)
            row = conn.execute("SELECT lease,generation,status,lease_expires FROM jobs WHERE id=?", (jid,)).fetchone()
            if row:
                old_lease, old_generation, status, expires = row
                if hmac.compare_digest(lease, old_lease) and generation == old_generation:
                    conn.execute("COMMIT")
                    return jsonify(ok=True, id=jid, status=status, idempotent=True, lease_expires=expires)
                if status == "expired" and generation > old_generation:
                    active = conn.execute("SELECT id FROM jobs WHERE status='leased' AND id<>? LIMIT 1", (jid,)).fetchone()
                    if active:
                        conn.execute("ROLLBACK")
                        return jsonify(error="executor_busy"), 409
                    expires = now + LEASE_TTL
                    conn.execute("UPDATE jobs SET lease=?,generation=?,status='leased',updated=?,heartbeat_at=?,lease_expires=?,result=NULL WHERE id=?", (lease, generation, now, now, expires, jid))
                    conn.execute("COMMIT")
                    return jsonify(ok=True, id=jid, status="leased", reacquired=True, lease_expires=expires), 200
                conn.execute("ROLLBACK")
                return jsonify(error="fencing_conflict"), 409
            active = conn.execute("SELECT id FROM jobs WHERE status='leased' LIMIT 1").fetchone()
            if active:
                conn.execute("ROLLBACK")
                return jsonify(error="executor_busy"), 409
            expires = now + LEASE_TTL
            conn.execute("INSERT INTO jobs(id,lease,generation,status,created,updated,result,heartbeat_at,lease_expires) VALUES(?,?,?,?,?,?,?,?,?)", (jid, lease, generation, "leased", now, now, None, now, expires))
            conn.execute("COMMIT")
            return jsonify(ok=True, id=jid, status="leased", idempotent=False, lease_expires=expires), 201
        except Exception:
            rollback(conn)
            raise


@app.post("/v1/jobs/<jid>/heartbeat")
def heartbeat(jid):
    payload = request.get_json(silent=True) or {}
    lease = str(payload.get("lease", ""))
    generation = payload.get("generation")
    if not valid_fence(jid, lease, generation):
        return jsonify(error="invalid_job_fencing"), 400
    now = time.time()
    with lock, db() as conn:
        try:
            begin(conn)
            expire_stale(conn, now)
            row = conn.execute("SELECT lease,generation,status FROM jobs WHERE id=?", (jid,)).fetchone()
            if not row:
                conn.execute("ROLLBACK")
                return jsonify(error="not_found"), 404
            if not hmac.compare_digest(lease, row[0]) or generation != row[1] or row[2] != "leased":
                conn.execute("ROLLBACK")
                return jsonify(error="stale_lease"), 409
            expires = now + LEASE_TTL
            conn.execute("UPDATE jobs SET heartbeat_at=?,lease_expires=?,updated=? WHERE id=?", (now, expires, now, jid))
            conn.execute("COMMIT")
            return jsonify(ok=True, id=jid, status="leased", lease_expires=expires)
        except Exception:
            rollback(conn)
            raise


@app.post("/v1/jobs/<jid>/complete")
def complete(jid):
    payload = request.get_json(silent=True) or {}
    lease = str(payload.get("lease", ""))
    generation = payload.get("generation")
    if not valid_fence(jid, lease, generation):
        return jsonify(error="invalid_job_fencing"), 400
    result = json.dumps(payload.get("result", {}), separators=(",", ":"))
    if len(result.encode()) > 4096:
        return jsonify(error="result_too_large"), 400
    now = time.time()
    with lock, db() as conn:
        try:
            begin(conn)
            expire_stale(conn, now)
            row = conn.execute("SELECT lease,generation,status FROM jobs WHERE id=?", (jid,)).fetchone()
            if not row:
                conn.execute("ROLLBACK")
                return jsonify(error="not_found"), 404
            if not hmac.compare_digest(lease, row[0]) or generation != row[1]:
                conn.execute("ROLLBACK")
                return jsonify(error="stale_lease"), 409
            if row[2] == "done":
                conn.execute("COMMIT")
                return jsonify(ok=True, id=jid, status="done", idempotent=True)
            if row[2] != "leased":
                conn.execute("ROLLBACK")
                return jsonify(error="stale_lease" if row[2] == "expired" else "invalid_transition"), 409
            conn.execute("UPDATE jobs SET status='done',result=?,updated=? WHERE id=?", (result, now, jid))
            conn.execute("COMMIT")
            return jsonify(ok=True, id=jid, status="done")
        except Exception:
            rollback(conn)
            raise


@app.get("/v1/jobs/<jid>")
def get_job(jid):
    with db() as conn:
        expire_stale(conn)
        row = conn.execute("SELECT id,generation,status,created,updated,result,heartbeat_at,lease_expires FROM jobs WHERE id=?", (jid,)).fetchone()
    if not row:
        return jsonify(error="not_found"), 404
    return jsonify(id=row[0], generation=row[1], status=row[2], created=row[3], updated=row[4], result=json.loads(row[5]) if row[5] else None, heartbeat_at=row[6], lease_expires=row[7])


db().close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
