"""QA-only, durable per-network SQLite fencing reference for CORTES.

No publication, Neon, external auth or automatic activation. The controller
must provision OS identities and directory ACLs independently.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import os
import re
import secrets
import sqlite3
import time

OWNERS = {"kwai": "lucasrosalem", "tiktok": "lucasrosalem4"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,96}$")
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK(status IN ('queued','leased','started','uncertain','confirmed')),
  lease_generation INTEGER NOT NULL DEFAULT 0,
  worker TEXT, token_digest TEXT, expires_at INTEGER,
  remote_id TEXT, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS effects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id),
  remote_id TEXT NOT NULL UNIQUE,
  account TEXT NOT NULL,
  network TEXT NOT NULL,
  recorded_at INTEGER NOT NULL
);
"""


class ScopeDenied(RuntimeError):
    pass


class QAFencedQueue:
    def __init__(self, qa_root, network, account, *, clock=None):
        if OWNERS.get(network) != account or not SAFE_ID.fullmatch(account or ""):
            raise ScopeDenied("unregistered_network_account")
        root = Path(qa_root)
        if root.is_symlink() or not root.is_dir():
            raise ScopeDenied("missing_qa_directory")
        root = root.resolve(strict=True)
        try:
            marker = (root / ".cortes-iso03-qa-only").read_text(encoding="ascii").strip()
        except (OSError, UnicodeError) as exc:
            raise ScopeDenied("not_qa_environment") from exc
        if marker != "qa-only":
            raise ScopeDenied("not_qa_environment")
        # The controller provisions both directories. The agent cannot.
        dir_ = root / network
        if dir_.is_symlink() or not dir_.is_dir():
            raise ScopeDenied("network_directory_not_provisioned")
        self.dir = dir_.resolve(strict=True)
        self.db_path = self.dir / (account + ".sqlite3")
        if self.db_path.is_symlink():
            raise ScopeDenied("state_symlink_denied")
        self.network = network
        self.account = account
        self.clock = clock or (lambda: int(time.time()))
        with self.conn() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        if self.db_path.is_symlink() or not self.db_path.parent.samefile(self.dir):
            raise ScopeDenied("state_path_changed")
        db = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, key):
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key):
            raise ScopeDenied("event_key_invalid")
        with self.conn() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO jobs(event_key,status,created_at) VALUES(?, 'queued', ?)",
                       (key, self.clock()))
            return db.execute("SELECT id FROM jobs WHERE event_key=?", (key,)).fetchone()[0]

    def claim(self, worker):
        if not isinstance(worker, str) or not SAFE_ID.fullmatch(worker):
            raise ScopeDenied("worker_invalid")
        with self.conn() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
            if row is None:
                return None
            token = secrets.token_hex(32)
            digest = hashlib.sha256(token.encode()).hexdigest()
            n = db.execute("UPDATE jobs SET status='leased',lease_generation=lease_generation+1,"
                           "worker=?,token_digest=?,expires_at=? WHERE id=? AND status='queued'",
                           (worker, digest, self.clock()+600, row["id"])).rowcount
            if n != 1:
                raise ScopeDenied("race_fence_denied")
            gen = db.execute("SELECT lease_generation FROM jobs WHERE id=?", (row["id"],)).fetchone()[0]
            return {"network": self.network, "account": self.account, "id": row["id"],
                    "worker": worker, "generation": gen, "token": token}

    def _require(self, db, claim, state):
        if (not isinstance(claim, dict) or claim.get("network") != self.network
                or claim.get("account") != self.account):
            raise ScopeDenied("foreign_network_claim_denied")
        row = db.execute("SELECT * FROM jobs WHERE id=?", (claim.get("id"),)).fetchone()
        if (row is None or row["status"] != state or row["worker"] != claim.get("worker")
                or row["lease_generation"] != claim.get("generation")
                or row["expires_at"] is None or row["expires_at"] <= self.clock()
                or not isinstance(claim.get("token"), str)
                or row["token_digest"] != hashlib.sha256(claim["token"].encode()).hexdigest()):
            raise ScopeDenied("stale_or_forged_fence_denied")
        return row

    def start(self, claim):
        with self.conn() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._require(db, claim, "leased")
            db.execute("UPDATE jobs SET status='started' WHERE id=?", (row["id"],))

    def confirm(self, claim, remote_id):
        if not isinstance(remote_id, str) or not SAFE_ID.fullmatch(remote_id):
            raise ScopeDenied("unverified_remote_id_denied")
        with self.conn() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._require(db, claim, "started")
            db.execute("INSERT INTO effects(job_id,remote_id,account,network,recorded_at) "
                       "VALUES(?,?,?,?,?)", (row["id"], remote_id, self.account,
                                          self.network, self.clock()))
            db.execute("UPDATE jobs SET status='confirmed',token_digest=NULL,"
                       "expires_at=NULL,remote_id=? WHERE id=?",
                       (remote_id, row["id"]))

    def uncertain(self, claim):
        with self.conn() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._require(db, claim, "started")
            db.execute("UPDATE jobs SET status='uncertain',token_digest=NULL,"
                       "expires_at=NULL WHERE id=?", (row["id"],))

    def count_effects(self):
        with self.conn() as db:
            return db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]

    def count_states(self):
        with self.conn() as db:
            return dict(db.execute("SELECT status,COUNT(*) FROM jobs GROUP BY status").fetchall())


def kwai_fanout_shadow(snapshot, *, trusted_controller):
    """Deterministic intents only; never enqueues a target or publishes."""
    if (trusted_controller is not True or not isinstance(snapshot, dict)
            or snapshot.get("target_key") != "kwai:lucasrosalem"
            or snapshot.get("status") not in ("queued", "confirmed")
            or not SAFE_ID.fullmatch(snapshot.get("segment_key", ""))):
        raise ScopeDenied("untrusted_kwai_master_denied")
    targets = ("instagram:universoanthares", "pinterest:lucasyahn",
               "linkedin:primary", "linkedin:personal")
    return {"source": "kwai:lucasrosalem",
            "intents": [{"target": t, "digest": hashlib.sha256(
                (snapshot["segment_key"] + "|" + t).encode()).hexdigest(),
                "enqueue_authorized": False, "publish_authorized": False}
                for t in targets],
            "legacy_trigger_changed": False, "database_modified": False,
            "cutover_authorized": False}
