#!/usr/bin/env python3
"""Anthares Core v0: zero-dependency, durable, fenced task queue."""
import argparse
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
 lease_owner TEXT, lease_token TEXT, lease_until INTEGER,
 result TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS tasks_ready ON tasks(status,lease_until,created_at);
"""

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db

def enqueue(db, kind, payload, task_id=None):
    now = int(time.time())
    task_id = task_id or str(uuid.uuid4())
    db.execute("INSERT OR IGNORE INTO tasks(id,kind,payload,status,created_at,updated_at) VALUES(?,?,?,'queued',?,?)",
               (task_id, kind, json.dumps(payload, sort_keys=True), now, now))
    return task_id

def claim(db, worker, ttl=120):
    now = int(time.time())
    token = str(uuid.uuid4())
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("""SELECT id,kind,payload,attempts FROM tasks
            WHERE status='queued' OR (status='running' AND lease_until<=?)
            ORDER BY created_at,id LIMIT 1""", (now,)).fetchone()
        if row:
            db.execute("""UPDATE tasks SET status='running',attempts=attempts+1,
                lease_owner=?,lease_token=?,lease_until=?,updated_at=? WHERE id=?""",
                (worker,token,now+ttl,now,row[0]))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    if not row:
        return None
    return dict(id=row[0],kind=row[1],payload=json.loads(row[2]),attempts=row[3]+1,token=token)

def finish(db, task_id, token, result, success=True):
    now = int(time.time())
    cur = db.execute("""UPDATE tasks SET status=?,result=?,lease_until=NULL,
      lease_owner=NULL,lease_token=NULL,updated_at=?
      WHERE id=? AND status='running' AND lease_token=? AND lease_until>?""",
      ('done' if success else 'failed',json.dumps(result,sort_keys=True),now,task_id,token,now))
    return cur.rowcount == 1

def heartbeat(db, task_id, token, ttl=120):
    now=int(time.time())
    return db.execute("""UPDATE tasks SET lease_until=?,updated_at=?
      WHERE id=? AND status='running' AND lease_token=? AND lease_until>?""",
      (now+ttl,now,task_id,token,now)).rowcount==1

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--db',default=os.environ.get('ANTHARES_CORE_DB','state/anthares-core.sqlite3'))
    sub=p.add_subparsers(dest='command',required=True)
    e=sub.add_parser('enqueue');e.add_argument('kind');e.add_argument('payload');e.add_argument('--id')
    c=sub.add_parser('claim');c.add_argument('--worker',required=True);c.add_argument('--ttl',type=int,default=120)
    f=sub.add_parser('finish');f.add_argument('id');f.add_argument('token');f.add_argument('result');f.add_argument('--failed',action='store_true')
    h=sub.add_parser('heartbeat');h.add_argument('id');h.add_argument('token');h.add_argument('--ttl',type=int,default=120)
    sub.add_parser('list')
    a=p.parse_args();db=connect(a.db)
    if a.command=='enqueue': out={'id':enqueue(db,a.kind,json.loads(a.payload),a.id)}
    elif a.command=='claim':out=claim(db,a.worker,a.ttl)
    elif a.command=='finish':out={'accepted':finish(db,a.id,a.token,json.loads(a.result),not a.failed)}
    elif a.command=='heartbeat':out={'accepted':heartbeat(db,a.id,a.token,a.ttl)}
    else:
        out=[dict(zip(('id','kind','status','attempts','lease_owner','lease_until'),row))
             for row in db.execute('SELECT id,kind,status,attempts,lease_owner,lease_until FROM tasks ORDER BY created_at')]
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
