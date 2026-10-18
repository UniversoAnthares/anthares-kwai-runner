#!/usr/bin/env python3
"""Scope Android physical leases to current CORTES and its verified Kwai account.

Runs after publisher-target v17 and physical Android v18 migrations.
Old/non-CORTES jobs and their historical records remain unchanged.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"src"/"index.js"
s=p.read_text(encoding="utf-8-sig")
old='  const candidates=this.sql.exec("SELECT q.* FROM jobs q WHERE q.platform=? AND q.status=\'queued\' AND q.attempts<? AND NOT EXISTS (SELECT 1 FROM jobs a WHERE a.platform=q.platform AND a.account_id=q.account_id AND a.id<>q.id AND ((a.status=\'leased\' AND a.lease_until>?) OR (a.status=\'uncertain\' AND a.publication_started=1))) ORDER BY q.created_at,q.id LIMIT 200",b.platform,MAX_ATTEMPTS,t).toArray();'
new="""  const candidates=this.sql.exec("SELECT q.* FROM jobs q WHERE q.platform=? AND q.status='queued' AND q.attempts<? AND NOT EXISTS (SELECT 1 FROM jobs a WHERE a.platform=q.platform AND a.account_id=q.account_id AND a.id<>q.id AND ((a.status='leased' AND a.lease_until>?) OR (a.status='uncertain' AND a.publication_started=1))) AND (? <> 'physical_android' OR q.id LIKE 'kwai-cortes-%') ORDER BY q.created_at,q.id LIMIT 200",b.platform,MAX_ATTEMPTS,t,b.executor).toArray();"""
if new in s:
    print("CORTES_PHYSICAL_LEASE_PRIORITY_ALREADY_APPLIED=1")
elif s.count(old)==1:
    p.write_text(s.replace(old,new,1),encoding="utf-8")
    print("CORTES_PHYSICAL_LEASE_PRIORITY_APPLIED=1")
else:
    raise SystemExit("CORTES_LEASE_PRIORITY_ANCHOR_UNEXPECTED")
