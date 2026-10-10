"""Anthares Relay v1: platform-neutral, fail-closed publication coordinator.

Uses a local SQLite WAL database; external adapters must provide authenticated
identity and independent post verification. No platform login bypass.
"""
import argparse
import hashlib
import json
import sqlite3
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
 id TEXT PRIMARY KEY, account TEXT NOT NULL, digest TEXT NOT NULL,
 state TEXT NOT NULL, lease TEXT, expires INTEGER NOT NULL DEFAULT 0,
 external_id TEXT, public_url TEXT, updated INTEGER NOT NULL,
 UNIQUE(account, digest)
);
"""

class Relay:
 def __init__(self, path):
  self.db = sqlite3.connect(path, isolation_level=None, timeout=30)
  self.db.execute("PRAGMA journal_mode=WAL")
  self.db.executescript(SCHEMA)

 def enqueue(self, account, video_bytes):
  if not account or not video_bytes: raise ValueError("account and video required")
  digest=hashlib.sha256(video_bytes).hexdigest()
  now=int(time.time())
  self.db.execute("INSERT OR IGNORE INTO jobs(id,account,digest,state,updated) VALUES(?,?,?,?,?)",
                  (uuid.uuid4().hex,account,digest,"queued",now))
  row=self.db.execute("SELECT id,state FROM jobs WHERE account=? AND digest=?", (account,digest)).fetchone()
  return {"id":row[0],"state":row[1]}

 def lease(self, job_id, identity_verified, seconds=180):
  if not identity_verified: raise PermissionError("verified account identity required")
  if not 30 <= seconds <= 900: raise ValueError("lease outside safe bounds")
  token=uuid.uuid4().hex
  now=int(time.time())
  self.db.execute("BEGIN IMMEDIATE")
  try:
   row=self.db.execute("SELECT state FROM jobs WHERE id=?",(job_id,)).fetchone()
   if not row or row[0]!="queued": raise ValueError("job not queued; never retry uncertain submit")
   self.db.execute("UPDATE jobs SET state='leased',lease=?,expires=?,updated=? WHERE id=?",
                   (token,now+seconds,now,job_id))
   self.db.execute("COMMIT")
  except BaseException:
   self.db.execute("ROLLBACK")
   raise
  return token

 def submitted(self, job_id, token):
  now=int(time.time())
  self.db.execute("BEGIN IMMEDIATE")
  try:
   row=self.db.execute("SELECT state,lease,expires FROM jobs WHERE id=?",(job_id,)).fetchone()
   if not row or row[0]!="leased" or row[1]!=token or row[2]<now:
    raise PermissionError("invalid or expired fenced lease")
   self.db.execute("UPDATE jobs SET state='uncertain',updated=? WHERE id=?",(now,job_id))
   self.db.execute("COMMIT")
  except BaseException:
   self.db.execute("ROLLBACK")
   raise

 def verify(self, job_id, external_id, public_url, independent_check):
  if not external_id or not public_url.startswith("https://"):
   raise ValueError("external evidence required")
  if not independent_check(external_id, public_url):
   raise ValueError("independent public verification failed")
  row=self.db.execute("SELECT state FROM jobs WHERE id=?",(job_id,)).fetchone()
  if not row or row[0]!="uncertain": raise ValueError("no submitted job to verify")
  self.db.execute("UPDATE jobs SET state='published',external_id=?,public_url=?,updated=? WHERE id=? AND state='uncertain'",
                  (external_id,public_url,int(time.time()),job_id))

 def quarantine_expired(self):
  now=int(time.time())
  return self.db.execute("UPDATE jobs SET state='uncertain',updated=? WHERE state='leased' AND expires<?",
                         (now,now)).rowcount

 def status(self):
  return dict(self.db.execute("SELECT state,COUNT(*) FROM jobs GROUP BY state").fetchall())

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--db",default="anthares-relay.sqlite")
 p.add_argument("--status",action="store_true")
 args=p.parse_args()
 relay=Relay(args.db)
 print(json.dumps(relay.status(),sort_keys=True))

if __name__=="__main__": main()
