#!/usr/bin/env python3
"""Durable publication queue with fenced leases and per-account/platform locks.

Safety boundary: a lease lost before ``publication_started`` is retry-safe. A
lease lost after that fence becomes ``uncertain`` and blocks the target until
reconciliation. This module never interprets an expired lease as proof that a
publish did not happen.
"""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS publication_jobs(
 id TEXT PRIMARY KEY,
 publication_id TEXT NOT NULL UNIQUE,
 platform TEXT NOT NULL,
 account_id TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued',
 attempts INTEGER NOT NULL DEFAULT 0,
 lease_owner TEXT,
 lease_generation INTEGER NOT NULL DEFAULT 0,
 lease_until INTEGER,
 heartbeat_at INTEGER,
 last_error TEXT,
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS pub_jobs_ready
 ON publication_jobs(status, platform, account_id, created_at);
CREATE INDEX IF NOT EXISTS pub_jobs_target
 ON publication_jobs(platform, account_id, status);
CREATE TABLE IF NOT EXISTS publication_target_locks(
 platform TEXT NOT NULL,
 account_id TEXT NOT NULL,
 publication_id TEXT NOT NULL,
 owner TEXT NOT NULL,
 generation INTEGER NOT NULL,
 lease_until INTEGER NOT NULL,
 PRIMARY KEY(platform, account_id)
);
"""


def _now(now=None): return int(time.time() if now is None else now)
def _account(v): return str(v).strip().lstrip('@').casefold()
def _platform(v):
    p=str(v).strip().casefold()
    return 'x' if p=='twitter' else p


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db=sqlite3.connect(path, timeout=30, isolation_level=None)
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript(SCHEMA)
    return db


def enqueue(db, publication_id, platform, account_id, job_id=None, now=None):
    publication_id=str(publication_id).strip(); platform=_platform(platform); account_id=_account(account_id)
    if not publication_id or not platform or not account_id: raise ValueError('publication_id, platform and account_id are required')
    job_id=str(job_id or uuid.uuid5(uuid.NAMESPACE_URL, f'anthares:{publication_id}'))
    t=_now(now)
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('SELECT id,platform,account_id FROM publication_jobs WHERE publication_id=?',(publication_id,)).fetchone()
        if row and (row[1],row[2])!=(platform,account_id):
            raise ValueError('publication idempotency key reused for a different target')
        if not row:
            db.execute("INSERT INTO publication_jobs(id,publication_id,platform,account_id,status,created_at,updated_at) VALUES(?,?,?,?, 'queued',?,?)",
                       (job_id,publication_id,platform,account_id,t,t))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK'); raise
    return row[0] if row else job_id


def recover_stale(db, now=None):
    """Recover only pre-fence work; quarantine post-fence work as uncertain."""
    t=_now(now)
    db.execute('BEGIN IMMEDIATE')
    try:
        pre=db.execute("""UPDATE publication_jobs SET status='queued',lease_owner=NULL,lease_until=NULL,
            heartbeat_at=NULL,updated_at=? WHERE status='leased' AND lease_until<=?""",(t,t)).rowcount
        post=db.execute("""UPDATE publication_jobs SET status='uncertain',lease_owner=NULL,lease_until=NULL,
            heartbeat_at=NULL,last_error=COALESCE(last_error,'lease_expired_after_publication_started'),updated_at=?
            WHERE status='publication_started' AND lease_until<=?""",(t,t)).rowcount
        db.execute('DELETE FROM publication_target_locks WHERE lease_until<=?',(t,))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK'); raise
    return {'retry_safe_requeued':pre,'uncertain_quarantined':post}


def claim(db, owner, ttl=120, now=None):
    owner=str(owner).strip()
    if not owner: raise ValueError('owner is required')
    if int(ttl)<10: raise ValueError('ttl must be >= 10 seconds')
    t=_now(now); ttl=int(ttl)
    recover_stale(db,t)
    db.execute('BEGIN IMMEDIATE')
    try:
        # An unresolved uncertain result serializes that account/platform. This is
        # intentional: do not race a new publish while an earlier one may exist.
        row=db.execute("""SELECT j.id,j.publication_id,j.platform,j.account_id,j.lease_generation,j.attempts
          FROM publication_jobs j
          WHERE j.status='queued'
            AND NOT EXISTS (SELECT 1 FROM publication_jobs u
              WHERE u.platform=j.platform AND u.account_id=j.account_id AND u.status='uncertain')
            AND NOT EXISTS (SELECT 1 FROM publication_target_locks l
              WHERE l.platform=j.platform AND l.account_id=j.account_id AND l.lease_until>?)
          ORDER BY j.created_at,j.id LIMIT 1""",(t,)).fetchone()
        if row is None:
            db.execute('COMMIT'); return None
        generation=int(row[4])+1
        db.execute("""UPDATE publication_jobs SET status='leased',attempts=attempts+1,
          lease_owner=?,lease_generation=?,lease_until=?,heartbeat_at=?,updated_at=?
          WHERE id=? AND status='queued'""",(owner,generation,t+ttl,t,t,row[0]))
        db.execute("""INSERT INTO publication_target_locks(platform,account_id,publication_id,owner,generation,lease_until)
          VALUES(?,?,?,?,?,?)""",(row[2],row[3],row[1],owner,generation,t+ttl))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK'); raise
    return {'id':row[0],'publication_id':row[1],'platform':row[2],'account_id':row[3],
            'lease_generation':generation,'attempts':int(row[5])+1,'lease_until':t+ttl}


def heartbeat(db, job_id, owner, generation, ttl=120, now=None):
    t=_now(now); ttl=int(ttl); generation=int(generation)
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute("SELECT platform,account_id,publication_id FROM publication_jobs WHERE id=? AND lease_owner=? AND lease_generation=? AND status IN ('leased','publication_started') AND lease_until>?",
                       (job_id,owner,generation,t)).fetchone()
        if row is None:
            db.execute('COMMIT'); return False
        ok=db.execute("UPDATE publication_jobs SET lease_until=?,heartbeat_at=?,updated_at=? WHERE id=? AND lease_owner=? AND lease_generation=?",
                      (t+ttl,t,t,job_id,owner,generation)).rowcount==1
        lock=db.execute("""UPDATE publication_target_locks SET lease_until=? WHERE platform=? AND account_id=?
          AND publication_id=? AND owner=? AND generation=? AND lease_until>?""",
          (t+ttl,row[0],row[1],row[2],owner,generation,t)).rowcount==1
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK'); raise
    return ok and lock


def mark_publication_started(db, job_id, owner, generation, now=None):
    t=_now(now)
    return db.execute("""UPDATE publication_jobs SET status='publication_started',updated_at=?
      WHERE id=? AND status='leased' AND lease_owner=? AND lease_generation=? AND lease_until>?""",
      (t,job_id,owner,int(generation),t)).rowcount==1


def fail_before_publish(db, job_id, owner, generation, error=None, now=None):
    """Safe retry path. Invalid once the irreversible publication fence was crossed."""
    t=_now(now); generation=int(generation)
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute("SELECT platform,account_id,publication_id FROM publication_jobs WHERE id=? AND status='leased' AND lease_owner=? AND lease_generation=? AND lease_until>?",
                       (job_id,owner,generation,t)).fetchone()
        if row is None: db.execute('COMMIT'); return False
        db.execute("""UPDATE publication_jobs SET status='queued',lease_owner=NULL,lease_until=NULL,heartbeat_at=NULL,
          last_error=?,updated_at=? WHERE id=?""",(error,t,job_id))
        db.execute("DELETE FROM publication_target_locks WHERE platform=? AND account_id=? AND publication_id=? AND owner=? AND generation=?",
                   (row[0],row[1],row[2],owner,generation))
        db.execute('COMMIT'); return True
    except BaseException:
        db.execute('ROLLBACK'); raise


def mark_uncertain(db, job_id, owner, generation, error=None, now=None):
    t=_now(now); generation=int(generation)
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute("SELECT platform,account_id,publication_id FROM publication_jobs WHERE id=? AND status='publication_started' AND lease_owner=? AND lease_generation=?",
                       (job_id,owner,generation)).fetchone()
        if row is None: db.execute('COMMIT'); return False
        db.execute("""UPDATE publication_jobs SET status='uncertain',lease_owner=NULL,lease_until=NULL,heartbeat_at=NULL,
          last_error=?,updated_at=? WHERE id=?""",(error,t,job_id))
        db.execute("DELETE FROM publication_target_locks WHERE platform=? AND account_id=? AND publication_id=? AND owner=? AND generation=?",
                   (row[0],row[1],row[2],owner,generation))
        db.execute('COMMIT'); return True
    except BaseException:
        db.execute('ROLLBACK'); raise


def confirm(db, job_id, owner=None, generation=None, now=None):
    """Confirm a known publish. Uncertain jobs can be reconciled without a live lease."""
    t=_now(now)
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('SELECT platform,account_id,publication_id,status,lease_owner,lease_generation FROM publication_jobs WHERE id=?',(job_id,)).fetchone()
        if row is None: db.execute('COMMIT'); return False
        if row[3]=='publication_started':
            if row[4]!=owner or int(row[5])!=int(generation or -1): db.execute('COMMIT'); return False
        elif row[3]!='uncertain':
            db.execute('COMMIT'); return False
        db.execute("""UPDATE publication_jobs SET status='confirmed',lease_owner=NULL,lease_until=NULL,heartbeat_at=NULL,
          last_error=NULL,updated_at=? WHERE id=?""",(t,job_id))
        db.execute('DELETE FROM publication_target_locks WHERE platform=? AND account_id=? AND publication_id=?',(row[0],row[1],row[2]))
        db.execute('COMMIT'); return True
    except BaseException:
        db.execute('ROLLBACK'); raise


def queue_state(db):
    statuses=dict(db.execute('SELECT status,count(*) FROM publication_jobs GROUP BY status').fetchall())
    return {k:int(statuses.get(k,0)) for k in ('queued','leased','publication_started','uncertain','confirmed')}
