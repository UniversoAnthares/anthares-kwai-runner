"""Fail-closed independent ARA standby. Python stdlib only.

The standby is deliberately NOT a second job executor. Promotion requires
an external, strongly consistent fencing authority shared with the primary.
A local SQLite generation is insufficient to prevent split brain.
"""
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("ARA_STANDBY_DB", "./ara-standby.sqlite3")
TOKEN = os.environ.get("ARA_STANDBY_TOKEN", "")
HOST = os.environ.get("ARA_STANDBY_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8789"))
LOCK = threading.RLock()

def connect():
    db = sqlite3.connect(DB, timeout=10, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("""CREATE TABLE IF NOT EXISTS observations(
        device TEXT PRIMARY KEY, observed_at INTEGER NOT NULL,
        payload TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata(
        key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
    return db

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def authenticated(self):
        supplied = self.headers.get("Authorization", "")
        return bool(TOKEN) and hmac.compare_digest(supplied, "Bearer " + TOKEN)

    def do_GET(self):
        if self.path == "/healthz":
            try:
                with connect() as db:
                    db.execute("SELECT 1").fetchone()
                return self.reply(200, {"ok": True, "role": "standby", "promoted": False})
            except sqlite3.Error:
                return self.reply(503, {"ok": False})
        if not self.authenticated():
            return self.reply(401, {"error": "unauthorized"})
        if self.path == "/v1/control/status":
            with connect() as db:
                count = db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            return self.reply(200, {"role": "standby", "promoted": False, "observed_devices": count, "queued": 0, "leased": 0})
        return self.reply(404, {"error": "not_found"})

    def do_POST(self):
        if not self.authenticated():
            return self.reply(401, {"error": "unauthorized"})
        # Never accept work or promotion based solely on a health timeout.
        # Without a shared fencing authority, even manual promotion is unsafe.
        return self.reply(423, {"error": "standby_fenced", "promoted": False,
                                "reason": "shared_generation_authority_required"})

if __name__ == "__main__":
    if not TOKEN or len(TOKEN) < 32:
        raise SystemExit("ARA_STANDBY_TOKEN must contain at least 32 characters")
    with connect():
        pass
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
