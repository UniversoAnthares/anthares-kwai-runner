#!/usr/bin/env python3
"""Durable, deterministic publication ledger for Anthares Publisher."""
import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence

SUPPORTED_PLATFORMS = frozenset((
    "kwai", "tiktok", "x", "instagram", "facebook", "threads", "pinterest", "bilibili",
    "discord", "linkedin", "medium", "rumble", "odysee",
))

SCHEMA = """
CREATE TABLE IF NOT EXISTS publications(
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL,
 start_ms INTEGER NOT NULL,
 end_ms INTEGER NOT NULL,
 platform TEXT NOT NULL,
 account TEXT NOT NULL,
 content_sha256 TEXT NOT NULL,
 status TEXT NOT NULL,
 external_id TEXT,
 public_url TEXT,
 attempts INTEGER NOT NULL DEFAULT 0,
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL,
 UNIQUE(source_id,start_ms,end_ms,platform,account)
);
"""


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.execute("PRAGMA busy_timeout=30000")
    db.executescript(SCHEMA)
    return db


def publication_id(source_id, start_ms, end_ms, platform, account):
    raw = f"{source_id}\n{int(start_ms)}\n{int(end_ms)}\n{platform.casefold()}\n{account.casefold()}".encode()
    return hashlib.sha256(raw).hexdigest()


def reserve(db, source_id, start_ms, end_ms, platform, account, content_sha256):
    """Atomically reserve a clip without overlapping or duplicate publication."""
    if not source_id or not source_id.strip():
        raise ValueError("source_id is required")
    if int(start_ms) < 0 or int(end_ms) <= int(start_ms):
        raise ValueError("end_ms must be greater than nonnegative start_ms")
    if len(content_sha256) != 64 or any(c not in "0123456789abcdef" for c in content_sha256.lower()):
        raise ValueError("content_sha256 must be a 64-character hex digest")
    platform = platform.casefold()
    account = account.strip().lstrip("@").casefold()
    if not account or platform not in SUPPORTED_PLATFORMS:
        raise ValueError("unsupported platform or missing account")
    pid = publication_id(source_id, start_ms, end_ms, platform, account)
    now = int(time.time())
    db.execute("BEGIN IMMEDIATE")
    try:
        existing = db.execute(
            "SELECT id,status,content_sha256,external_id,public_url,attempts FROM publications WHERE id=?",
            (pid,),
        ).fetchone()
        if existing:
            if existing[2].lower() != content_sha256.lower():
                raise ValueError("same source/timecode target maps to different content hash")
            row = existing
        else:
            overlap = db.execute(
                """SELECT id FROM publications
                   WHERE source_id=? AND platform=? AND account=?
                   AND start_ms<? AND end_ms>? LIMIT 1""",
                (source_id, platform, account, int(end_ms), int(start_ms)),
            ).fetchone()
            if overlap:
                raise ValueError("overlapping clip already reserved for this source and account")
            duplicate = db.execute(
                """SELECT id FROM publications
                   WHERE content_sha256=? AND platform=? AND account=? LIMIT 1""",
                (content_sha256.lower(), platform, account),
            ).fetchone()
            if duplicate:
                raise ValueError("identical video already reserved for this platform and account")
            db.execute(
                """INSERT INTO publications
                   (id,source_id,start_ms,end_ms,platform,account,content_sha256,status,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,'queued',?,?)""",
                (pid, source_id, int(start_ms), int(end_ms), platform, account, content_sha256.lower(), now, now),
            )
            row = (pid, "queued", content_sha256.lower(), None, None, 0)
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    return {
        "id": row[0],
        "status": row[1],
        "external_id": row[3],
        "public_url": row[4],
        "attempts": row[5],
        "already_published": row[1] == "published",
    }


def mark_attempt(db, pid):
    now = int(time.time())
    cur = db.execute(
        "UPDATE publications SET attempts=attempts+1,status='publishing',updated_at=? WHERE id=? AND status IN ('queued','retry')",
        (now, pid),
    )
    return cur.rowcount == 1


def fail(db, pid, retry=False):
    """Unknown post outcome is quarantined; retry is only safe pre-submit."""
    now = int(time.time())
    status = "retry" if retry else "uncertain"
    return db.execute(
        "UPDATE publications SET status=?,updated_at=? WHERE id=? AND status='publishing'",
        (status, now, pid),
    ).rowcount == 1


def confirm(db, pid, external_id, public_url):
    row = db.execute("SELECT platform,account FROM publications WHERE id=?", (pid,)).fetchone()
    if row is None:
        return False
    validate_evidence(PublicationEvidence(row[0], row[1], external_id, public_url), row[0], row[1])
    now = int(time.time())
    return db.execute(
        """UPDATE publications SET status='published',external_id=?,public_url=?,updated_at=?
           WHERE id=? AND status='publishing'""",
        (external_id, public_url, now, pid),
    ).rowcount == 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="state/anthares-publisher.sqlite3")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reserve")
    r.add_argument("source_id")
    r.add_argument("start_ms", type=int)
    r.add_argument("end_ms", type=int)
    r.add_argument("platform")
    r.add_argument("account")
    r.add_argument("content_sha256")
    a = sub.add_parser("attempt")
    a.add_argument("id")
    f = sub.add_parser("fail")
    f.add_argument("id")
    f.add_argument("--safe-pre-submit", action="store_true", help="only if no upload or submit request was sent")
    c = sub.add_parser("confirm")
    c.add_argument("id")
    c.add_argument("external_id")
    c.add_argument("public_url")
    sub.add_parser("list")
    x = p.parse_args()
    db = connect(x.db)
    if x.cmd == "reserve":
        out = reserve(db, x.source_id, x.start_ms, x.end_ms, x.platform, x.account, x.content_sha256)
    elif x.cmd == "attempt":
        out = {"accepted": mark_attempt(db, x.id)}
    elif x.cmd == "fail":
        out = {"accepted": fail(db, x.id, x.safe_pre_submit)}
    elif x.cmd == "confirm":
        out = {"accepted": confirm(db, x.id, x.external_id, x.public_url)}
    else:
        rows = db.execute(
            "SELECT id,source_id,start_ms,end_ms,platform,account,status,external_id,public_url,attempts FROM publications ORDER BY created_at,id"
        )
        out = [
            dict(zip(("id", "source_id", "start_ms", "end_ms", "platform", "account", "status", "external_id", "public_url", "attempts"), row))
            for row in rows
        ]
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
