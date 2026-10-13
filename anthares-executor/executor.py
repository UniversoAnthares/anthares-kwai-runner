"""Independent Anthares remote Chromium executor: fail-closed, single-writer jobs."""
import hmac
import json
import os
import signal
import sqlite3
import subprocess
import threading
import time
import urllib.request
import uuid
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
TOKEN = os.getenv("ANTHARES_EXECUTOR_TOKEN", "")
IDENTITY = os.getenv("ANTHARES_EXECUTOR_ID", "reserva-01")
DB = os.getenv("STATE_DB", "/data/state/jobs.sqlite3")
PROFILE = os.getenv("CHROME_PROFILE_DIR", "/data/profile")
PORT = int(os.getenv("PORT", "8080"))
MEMORY_LIMIT = int(os.getenv("MEMORY_LIMIT_BYTES", "1073741824"))
CDP = "http://127.0.0.1:9222"
lock = threading.RLock()
chrome = None

def db():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, lease TEXT NOT NULL, generation INTEGER NOT NULL,
        status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
        result TEXT)""")
    return conn

def auth():
    supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
    return bool(TOKEN) and hmac.compare_digest(supplied, TOKEN)

@app.before_request
def authorize():
    if request.path != "/health" and not auth():
        return jsonify(error="unauthorized"), 401

def mem_bytes():
    try:
        return int(Path("/sys/fs/cgroup/memory.current").read_text().strip())
    except (OSError, ValueError):
        return 0

def browser_ready():
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=1.5) as r:
            return bool(json.load(r).get("Browser"))
    except (OSError, ValueError):
        return False

@app.get("/health")
def health():
    return jsonify(ok=True, executor=IDENTITY, chromium_ready=browser_ready(),
                   memory_bytes=mem_bytes(), continuous_runner=True)

@app.post("/v1/browser/start")
def start_browser():
    global chrome
    with lock:
        if browser_ready():
            return jsonify(ok=True, reused=True)
        if mem_bytes() >= MEMORY_LIMIT:
            return jsonify(ok=False, error="memory_guard"), 503
        if chrome and chrome.poll() is None:
            return jsonify(ok=False, error="chromium_starting"), 409
        Path(PROFILE).mkdir(parents=True, exist_ok=True)
        chrome = subprocess.Popen([
            "chromium", "--headless=new", "--no-first-run", "--disable-dev-shm-usage",
            "--disable-background-networking", "--disable-extensions",
            "--disable-gpu", "--disable-features=Translate",
            "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=9222",
            "--user-data-dir=" + PROFILE, "about:blank"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(20):
            if browser_ready():
                return jsonify(ok=True, reused=False)
            if chrome.poll() is not None:
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
                chrome.wait(timeout=6)
            except subprocess.TimeoutExpired:
                os.killpg(chrome.pid, signal.SIGKILL)
                chrome.wait(timeout=3)
        chrome = None
        return jsonify(ok=True)

@app.post("/v1/jobs")
def create_job():
    payload = request.get_json(silent=True) or {}
    jid = str(payload.get("id", ""))
    lease = str(payload.get("lease", ""))
    generation = payload.get("generation")
    if not (len(jid) <= 128 and len(lease) >= 20 and len(lease) <= 256 and
            isinstance(generation, int) and generation >= 1 and jid):
        return jsonify(error="invalid_job_fencing"), 400
    with lock, db() as c:
        row = c.execute("SELECT lease,generation,status FROM jobs WHERE id=?", (jid,)).fetchone()
        if row:
            if row[0] != lease or row[1] != generation:
                return jsonify(error="fencing_conflict"), 409
            return jsonify(ok=True, id=jid, status=row[2], idempotent=True)
        active = c.execute("SELECT id FROM jobs WHERE status='leased' LIMIT 1").fetchone()
        if active:
            return jsonify(error="executor_busy"), 409
        now = time.time()
        c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?)", (jid, lease, generation, "leased", now, now, None))
        return jsonify(ok=True, id=jid, status="leased", idempotent=False), 201

@app.post("/v1/jobs/<jid>/complete")
def complete(jid):
    payload = request.get_json(silent=True) or {}
    with lock, db() as c:
        row = c.execute("SELECT lease,generation,status FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row:
            return jsonify(error="not_found"), 404
        if not (hmac.compare_digest(str(payload.get("lease", "")), row[0]) and
                type(payload.get("generation")) is int and payload["generation"] == row[1]):
            return jsonify(error="stale_lease"), 409
        if row[2] == "done":
            return jsonify(ok=True, id=jid, idempotent=True)
        if row[2] != "leased":
            return jsonify(error="invalid_transition"), 409
        result = json.dumps(payload.get("result", {}), separators=(",", ":"))
        if len(result) > 4096:
            return jsonify(error="result_too_large"), 400
        c.execute("UPDATE jobs SET status='done',result=?,updated=? WHERE id=?",
                  (result, time.time(), jid))
        return jsonify(ok=True, id=jid, status="done")

@app.get("/v1/jobs/<jid>")
def get_job(jid):
    with db() as c:
        row = c.execute("SELECT id,generation,status,created,updated,result FROM jobs WHERE id=?", (jid,)).fetchone()
    if not row:
        return jsonify(error="not_found"), 404
    return jsonify(id=row[0], generation=row[1], status=row[2],
                   created=row[3], updated=row[4], result=json.loads(row[5]) if row[5] else None)

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("ANTHARES_EXECUTOR_TOKEN required")
    db().close()
    app.run(host="0.0.0.0", port=PORT)
