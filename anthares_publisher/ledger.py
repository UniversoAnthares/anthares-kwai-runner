#!/usr/bin/env python3
"""Durable, deterministic publication ledger for Anthares Publisher."""
import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from anthares_publisher.contract import PublicationEvidence, validate_evidence

SCHEMA="""
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
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30,isolation_level=None)
    db.execute("PRAGMA busy_timeout=30000")
    db.executescript(SCHEMA)
    return db

def publication_id(source_id,start_ms,end_ms,platform,account):
    raw=f"{source_id}\n{int(start_ms)}\n{int(end_ms)}\n{platform.casefold()}\n{account.casefold()}".encode()
    return hashlib.sha256(raw).hexdigest()

def reserve(db,source_id,start_ms,end_ms,platform,account,content_sha256):
    if int(end_ms)<=int(start_ms): raise ValueError("end_ms must be greater than start_ms")
    pid=publication_id(source_id,start_ms,end_ms,platform,account)
    now=int(time.time())
    db.execute("""INSERT OR IGNORE INTO publications
      (id,source_id,start_ms,end_ms,platform,account,content_sha256,status,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,'queued',?,?)""",
      (pid,source_id,int(start_ms),int(end_ms),platform,account,content_sha256,now,now))
    row=db.execute("SELECT id,status,content_sha256,external_id,public_url,attempts FROM publications WHERE id=?",(pid,)).fetchone()
    if row[2] != content_sha256:
        raise ValueError("same source/timecode target maps to different content hash")
    return {"id":row[0],"status":row[1],"external_id":row[3],"public_url":row[4],"attempts":row[5],"already_published":row[1]=="published"}

def mark_attempt(db,pid):
    now=int(time.time())
    cur=db.execute("UPDATE publications SET attempts=attempts+1,status='publishing',updated_at=? WHERE id=? AND status IN ('queued','retry')",(now,pid))
    return cur.rowcount==1

def fail(db,pid,retry=True):
    now=int(time.time());status='retry' if retry else 'failed'
    return db.execute("UPDATE publications SET status=?,updated_at=? WHERE id=? AND status='publishing'",(status,now,pid)).rowcount==1

def confirm(db,pid,external_id,public_url):
    row=db.execute("SELECT platform,account FROM publications WHERE id=?",(pid,)).fetchone()
    if row is None:
        return False
    validate_evidence(PublicationEvidence(row[0],row[1],external_id,public_url),row[0],row[1])
    now=int(time.time())
    return db.execute("""UPDATE publications SET status='published',external_id=?,public_url=?,updated_at=?
      WHERE id=? AND status='publishing'""",(external_id,public_url,now,pid)).rowcount==1

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='state/anthares-publisher.sqlite3')
    sub=p.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('reserve');r.add_argument('source_id');r.add_argument('start_ms',type=int);r.add_argument('end_ms',type=int);r.add_argument('platform');r.add_argument('account');r.add_argument('content_sha256')
    a=sub.add_parser('attempt');a.add_argument('id')
    f=sub.add_parser('fail');f.add_argument('id');f.add_argument('--terminal',action='store_true')
    c=sub.add_parser('confirm');c.add_argument('id');c.add_argument('external_id');c.add_argument('public_url')
    sub.add_parser('list')
    x=p.parse_args();db=connect(x.db)
    if x.cmd=='reserve': out=reserve(db,x.source_id,x.start_ms,x.end_ms,x.platform,x.account,x.content_sha256)
    elif x.cmd=='attempt': out={'accepted':mark_attempt(db,x.id)}
    elif x.cmd=='fail': out={'accepted':fail(db,x.id,not x.terminal)}
    elif x.cmd=='confirm': out={'accepted':confirm(db,x.id,x.external_id,x.public_url)}
    else:
        rows=db.execute("SELECT id,source_id,start_ms,end_ms,platform,account,status,external_id,public_url,attempts FROM publications ORDER BY created_at,id")
        out=[dict(zip(('id','source_id','start_ms','end_ms','platform','account','status','external_id','public_url','attempts'),r)) for r in rows]
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
