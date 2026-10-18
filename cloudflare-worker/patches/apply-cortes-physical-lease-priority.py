#!/usr/bin/env python3
"""Restrict physical Android Kwai leases to CORTES jobs without deleting legacy jobs.

Applied *after* canonical v18 patches and before Cloudflare deployment.
Other executors retain their pre-existing queue ordering and semantics.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"src"/"index.js"
s=p.read_text(encoding="utf-8-sig")
old='const j=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status=\'queued\' AND attempts<? ORDER BY created_at LIMIT 1",b.platform,MAX_ATTEMPTS).toArray()[0];'
new=('const leaseSql=(b.executor==="physical_android"&&b.platform==="kwai")'
     '? "SELECT * FROM jobs WHERE platform=? AND status=\'queued\' AND attempts<? AND id LIKE \'kwai-cortes-%\' ORDER BY created_at LIMIT 1"'
     ': "SELECT * FROM jobs WHERE platform=? AND status=\'queued\' AND attempts<? ORDER BY created_at LIMIT 1";'
     ' const j=this.sql.exec(leaseSql,b.platform,MAX_ATTEMPTS).toArray()[0];')
if new in s:
    print("CORTES_PHYSICAL_LEASE_PRIORITY_ALREADY_APPLIED=1")
elif s.count(old)==1:
    p.write_text(s.replace(old,new,1),encoding="utf-8")
    print("CORTES_PHYSICAL_LEASE_PRIORITY_APPLIED=1")
else:
    raise SystemExit("CORTES_LEASE_PRIORITY_ANCHOR_UNEXPECTED")
