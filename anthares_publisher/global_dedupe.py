#!/usr/bin/env python3
"""Global publication dedupe ledger.

Canonical key scope is source interval + platform/account. The same clip may be
sent to distinct authorized destinations, but a target cannot receive the same
content or overlapping source interval twice. Any temporal intersection is
conservatively treated as overlap until a different reviewed policy exists.
Ambiguous post-submit outcomes require explicit reconciliation before retry.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

ACTIVE_STATES=('reserved','queued','leased','publication_started','uncertain','confirmed')

SCHEMA="""
CREATE TABLE IF NOT EXISTS dedupe_ledger(
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL,
 source_hash TEXT,
 start_ms INTEGER NOT NULL,
 end_ms INTEGER NOT NULL,
 clip_hash TEXT NOT NULL,
 platform TEXT NOT NULL,
 account_id TEXT NOT NULL,
 state TEXT NOT NULL,
 remote_id TEXT,
 last_error TEXT,
 created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL,
 UNIQUE(source_id,start_ms,end_ms,platform,account_id),
 UNIQUE(clip_hash,platform,account_id)
);
CREATE INDEX IF NOT EXISTS dedupe_target_interval
 ON dedupe_ledger(source_id,platform,account_id,start_ms,end_ms,state);
CREATE INDEX IF NOT EXISTS dedupe_target_hash
 ON dedupe_ledger(clip_hash,platform,account_id,state);
"""

def _now(now=None): return int(time.time() if now is None else now)
def _platform(v):
    p=str(v).strip().casefold(); return 'x' if p=='twitter' else p
def _account(v): return str(v).strip().lstrip('@').casefold()
def _hex64(v):
    s=str(v).strip().casefold()
    return len(s)==64 and all(c in '0123456789abcdef' for c in s)
def _id(*parts): return hashlib.sha256('\n'.join(map(str,parts)).encode()).hexdigest()

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30,isolation_level=None)
    db.execute('PRAGMA busy_timeout=30000');db.execute('PRAGMA journal_mode=WAL');db.executescript(SCHEMA)
    return db

def conflicts(db,source_id,start_ms,end_ms,clip_hash,platform,account_id):
    source_id=str(source_id).strip(); platform=_platform(platform); account_id=_account(account_id)
    start_ms,end_ms=int(start_ms),int(end_ms); clip_hash=str(clip_hash).casefold()
    if end_ms<=start_ms: raise ValueError('invalid interval')
    if not _hex64(clip_hash): raise ValueError('clip_hash must be sha256 hex')
    params=(platform,account_id,*ACTIVE_STATES)
    by_hash=db.execute(f"SELECT id,state,'content_hash' FROM dedupe_ledger WHERE clip_hash=? AND platform=? AND account_id=? AND state IN ({','.join('?'*len(ACTIVE_STATES))}) LIMIT 1",
                       (clip_hash,*params)).fetchone()
    if by_hash: return {'conflict':True,'id':by_hash[0],'state':by_hash[1],'reason':by_hash[2]}
    # Half-open intervals: touching boundaries are safe; any positive intersection is blocked.
    by_interval=db.execute(f"""SELECT id,state,'temporal_overlap' FROM dedupe_ledger
      WHERE source_id=? AND platform=? AND account_id=? AND start_ms<? AND end_ms>?
        AND state IN ({','.join('?'*len(ACTIVE_STATES))}) ORDER BY created_at LIMIT 1""",
      (source_id,platform,account_id,end_ms,start_ms,*ACTIVE_STATES)).fetchone()
    if by_interval:return {'conflict':True,'id':by_interval[0],'state':by_interval[1],'reason':by_interval[2]}
    return {'conflict':False}

def reserve(db,source_id,start_ms,end_ms,clip_hash,platform,account_id,source_hash=None,now=None):
    source_id=str(source_id).strip(); platform=_platform(platform); account_id=_account(account_id)
    start_ms,end_ms=int(start_ms),int(end_ms); clip_hash=str(clip_hash).casefold()
    if not source_id or not platform or not account_id: raise ValueError('source_id/platform/account_id required')
    if source_hash is not None and not _hex64(source_hash): raise ValueError('source_hash must be sha256 hex')
    t=_now(now); key=_id(source_id,start_ms,end_ms,platform,account_id)
    db.execute('BEGIN IMMEDIATE')
    try:
        existing=db.execute('SELECT id,state FROM dedupe_ledger WHERE id=?',(key,)).fetchone()
        if existing:
            db.execute('COMMIT'); return {'id':existing[0],'state':existing[1],'created':False}
        conflict=conflicts(db,source_id,start_ms,end_ms,clip_hash,platform,account_id)
        if conflict.get('conflict'):
            db.execute('ROLLBACK'); return {**conflict,'created':False}
        db.execute("""INSERT INTO dedupe_ledger(id,source_id,source_hash,start_ms,end_ms,clip_hash,platform,account_id,state,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?,'reserved',?,?)""",(key,source_id,source_hash,start_ms,end_ms,clip_hash,platform,account_id,t,t))
        db.execute('COMMIT'); return {'id':key,'state':'reserved','created':True}
    except BaseException:
        if db.in_transaction: db.execute('ROLLBACK')
        raise

def transition(db,entry_id,expected,new_state,error=None,remote_id=None,now=None):
    if isinstance(expected,str): expected=(expected,)
    expected=tuple(expected)
    if not expected: raise ValueError('expected state required')
    t=_now(now); marks=','.join('?'*len(expected))
    return db.execute(f"UPDATE dedupe_ledger SET state=?,last_error=?,remote_id=COALESCE(?,remote_id),updated_at=? WHERE id=? AND state IN ({marks})",
                      (new_state,error,remote_id,t,entry_id,*expected)).rowcount==1

def mark_publication_started(db,entry_id,now=None):
    return transition(db,entry_id,('reserved','queued','leased'),'publication_started',now=now)
def mark_uncertain(db,entry_id,error=None,now=None):
    return transition(db,entry_id,'publication_started','uncertain',error=error,now=now)
def confirm(db,entry_id,remote_id,now=None):
    if not str(remote_id).strip(): raise ValueError('remote_id required')
    return transition(db,entry_id,('publication_started','uncertain'),'confirmed',remote_id=str(remote_id),now=now)

def reconcile_absent(db,entry_id,proved_absent=False,evidence=None,now=None):
    """Release an uncertain reservation only with explicit evidence of absence."""
    if not proved_absent: return False
    error='reconciled_absent' + (f': {str(evidence)[:160]}' if evidence else '')
    return transition(db,entry_id,'uncertain','retry_safe',error=error,now=now)

def can_retry(db,entry_id):
    row=db.execute('SELECT state FROM dedupe_ledger WHERE id=?',(entry_id,)).fetchone()
    return bool(row and row[0]=='retry_safe')

def snapshot(db,platform=None,account_id=None):
    sql='SELECT id,source_id,start_ms,end_ms,clip_hash,platform,account_id,state,remote_id FROM dedupe_ledger';args=[]
    where=[]
    if platform is not None: where.append('platform=?');args.append(_platform(platform))
    if account_id is not None: where.append('account_id=?');args.append(_account(account_id))
    if where: sql+=' WHERE '+' AND '.join(where)
    sql+=' ORDER BY created_at,id'
    keys=('id','source_id','start_ms','end_ms','clip_hash','platform','account_id','state','remote_id')
    return [dict(zip(keys,r)) for r in db.execute(sql,args).fetchall()]
