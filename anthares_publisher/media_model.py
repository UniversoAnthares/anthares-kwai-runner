#!/usr/bin/env python3
"""Canonical Anthares media state model: Source -> Clip -> Publication.

This module is deliberately platform-neutral. It does not publish content; it
owns durable identity, destination isolation, dedupe and source-retention rules.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

SHORT_PLATFORMS={"kwai","tiktok","instagram","pinterest","linkedin","threads"}
LONG_PLATFORMS={"youtube","facebook","x","twitter","bilibili","odysee","rumble","bluesky","reddit"}
ALL_PLATFORMS=SHORT_PLATFORMS|LONG_PLATFORMS
FINAL_SUCCESS={"confirmed"}
NON_RETRIABLE={"uncertain"}

SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(
 id TEXT PRIMARY KEY,
 uri TEXT,
 sha256 TEXT,
 status TEXT NOT NULL DEFAULT 'active',
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS clips(
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
 master_id TEXT NOT NULL,
 duration_class TEXT NOT NULL CHECK(duration_class IN ('short','long')),
 start_ms INTEGER NOT NULL,
 end_ms INTEGER NOT NULL,
 content_sha256 TEXT NOT NULL,
 storage_uri TEXT,
 created_at INTEGER NOT NULL,
 UNIQUE(source_id,start_ms,end_ms,duration_class),
 UNIQUE(master_id)
);
CREATE TABLE IF NOT EXISTS publications(
 id TEXT PRIMARY KEY,
 clip_id TEXT NOT NULL REFERENCES clips(id) ON DELETE RESTRICT,
 master_id TEXT NOT NULL,
 platform TEXT NOT NULL,
 account_id TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued',
 remote_id TEXT,
 public_url TEXT,
 attempts INTEGER NOT NULL DEFAULT 0,
 last_error TEXT,
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL,
 UNIQUE(master_id,platform,account_id)
);
CREATE INDEX IF NOT EXISTS idx_publications_target ON publications(platform,account_id,status);
CREATE INDEX IF NOT EXISTS idx_publications_clip ON publications(clip_id,status);
"""

def _now(): return int(time.time())
def _norm_account(v): return str(v).strip().lstrip('@').casefold()
def _norm_platform(v):
    p=str(v).strip().casefold()
    if p=="twitter": p="x"
    if p not in ALL_PLATFORMS: raise ValueError(f"unsupported platform: {p}")
    return p

def _sha_ok(v):
    s=str(v).lower()
    return len(s)==64 and all(c in "0123456789abcdef" for c in s)

def _id(*parts): return hashlib.sha256("\n".join(map(str,parts)).encode()).hexdigest()

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30,isolation_level=None)
    db.execute("PRAGMA busy_timeout=30000")
    db.executescript(SCHEMA)
    return db

def register_source(db,source_id,uri=None,sha256=None):
    source_id=str(source_id).strip()
    if not source_id: raise ValueError("source_id is required")
    if sha256 is not None and not _sha_ok(sha256): raise ValueError("sha256 must be a 64-character hex digest")
    now=_now()
    db.execute("""INSERT INTO sources(id,uri,sha256,status,created_at,updated_at)
      VALUES(?,?,?,'active',?,?) ON CONFLICT(id) DO UPDATE SET
      uri=COALESCE(excluded.uri,sources.uri),sha256=COALESCE(excluded.sha256,sources.sha256),updated_at=excluded.updated_at""",
      (source_id,uri,sha256.lower() if sha256 else None,now,now))
    return source_id

def register_clip(db,source_id,start_ms,end_ms,duration_class,content_sha256,storage_uri=None,master_id=None):
    if db.execute("SELECT 1 FROM sources WHERE id=?",(source_id,)).fetchone() is None:
        raise ValueError("source must be registered first")
    start_ms,end_ms=int(start_ms),int(end_ms)
    if start_ms<0 or end_ms<=start_ms: raise ValueError("invalid time range")
    duration_class=str(duration_class).casefold()
    seconds=(end_ms-start_ms)/1000.0
    if duration_class=="short" and not 30<=seconds<=90: raise ValueError("short clip must be 30-90 seconds")
    if duration_class=="long" and not 300<=seconds<=840: raise ValueError("long clip must be 5-14 minutes")
    if duration_class not in ("short","long"): raise ValueError("duration_class must be short or long")
    if not _sha_ok(content_sha256): raise ValueError("content_sha256 must be a 64-character hex digest")
    content_sha256=content_sha256.lower()
    master_id=str(master_id or content_sha256).strip()
    if not master_id: raise ValueError("master_id is required")
    clip_id=_id(source_id,start_ms,end_ms,duration_class,master_id)
    now=_now()
    db.execute("""INSERT INTO clips(id,source_id,master_id,duration_class,start_ms,end_ms,content_sha256,storage_uri,created_at)
      VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING""",
      (clip_id,source_id,master_id,duration_class,start_ms,end_ms,content_sha256,storage_uri,now))
    return clip_id

def reserve_publication(db,clip_id,platform,account_id):
    row=db.execute("SELECT master_id,duration_class FROM clips WHERE id=?",(clip_id,)).fetchone()
    if row is None: raise ValueError("clip not found")
    master_id,duration_class=row
    platform=_norm_platform(platform);account_id=_norm_account(account_id)
    if not account_id: raise ValueError("account_id is required")
    if platform in SHORT_PLATFORMS and duration_class!="short": raise ValueError("short-form platform requires short master")
    if platform in LONG_PLATFORMS and duration_class!="long": raise ValueError("long-form platform requires long master")
    pub_id=_id(master_id,platform,account_id)
    now=_now()
    db.execute("""INSERT INTO publications(id,clip_id,master_id,platform,account_id,status,created_at,updated_at)
      VALUES(?,?,?,?,?,'queued',?,?) ON CONFLICT(master_id,platform,account_id) DO NOTHING""",
      (pub_id,clip_id,master_id,platform,account_id,now,now))
    row=db.execute("SELECT id,status,attempts,remote_id,public_url FROM publications WHERE master_id=? AND platform=? AND account_id=?",
                   (master_id,platform,account_id)).fetchone()
    return dict(zip(("id","status","attempts","remote_id","public_url"),row))

def start_publication(db,pub_id):
    now=_now()
    return db.execute("""UPDATE publications SET status='publishing',attempts=attempts+1,updated_at=?
      WHERE id=? AND status IN ('queued','retry')""",(now,pub_id)).rowcount==1

def mark_pre_submit_failure(db,pub_id,error=None):
    now=_now()
    return db.execute("UPDATE publications SET status='retry',last_error=?,updated_at=? WHERE id=? AND status='publishing'",
                      (error,now,pub_id)).rowcount==1

def mark_uncertain(db,pub_id,error=None):
    now=_now()
    return db.execute("UPDATE publications SET status='uncertain',last_error=?,updated_at=? WHERE id=? AND status='publishing'",
                      (error,now,pub_id)).rowcount==1

def confirm_publication(db,pub_id,remote_id,public_url=None):
    remote_id=str(remote_id).strip()
    if not remote_id: raise ValueError("remote_id is required")
    now=_now()
    return db.execute("""UPDATE publications SET status='confirmed',remote_id=?,public_url=?,last_error=NULL,updated_at=?
      WHERE id=? AND status IN ('publishing','uncertain')""",(remote_id,public_url,now,pub_id)).rowcount==1

def mark_source_processing_complete(db,source_id):
    return db.execute("UPDATE sources SET status='processing_complete',updated_at=? WHERE id=?",(_now(),source_id)).rowcount==1

def source_safe_to_delete(db,source_id):
    source=db.execute("SELECT status FROM sources WHERE id=?",(source_id,)).fetchone()
    if source is None or source[0]!="processing_complete": return False
    total=db.execute("SELECT count(*) FROM publications p JOIN clips c ON c.id=p.clip_id WHERE c.source_id=?",(source_id,)).fetchone()[0]
    if total==0: return False
    incomplete=db.execute("""SELECT count(*) FROM publications p JOIN clips c ON c.id=p.clip_id
      WHERE c.source_id=? AND p.status!='confirmed'""",(source_id,)).fetchone()[0]
    return incomplete==0

def target_state(db,platform,account_id):
    platform=_norm_platform(platform);account_id=_norm_account(account_id)
    rows=db.execute("SELECT id,master_id,status,attempts,remote_id FROM publications WHERE platform=? AND account_id=? ORDER BY created_at,id",
                    (platform,account_id)).fetchall()
    return [dict(zip(("id","master_id","status","attempts","remote_id"),r)) for r in rows]
