#!/usr/bin/env python3
"""Deterministically upgrade the central queue from v16 to target-scoped v17.

Source of truth for publication execution remains the AntharesQueue Durable
Object. This patch is applied to the deploy snapshot; it creates no second
queue/store. Re-running is idempotent.
"""
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"src"/"index.js"
s=p.read_text(encoding="utf-8-sig")
OLD='2026-10-05-queue-fencing-v16'
NEW='2026-10-15-publisher-target-v17'
if NEW in s:
    print('PUBLISHER_TARGET_V17_ALREADY_APPLIED=1')
    raise SystemExit(0)
if OLD not in s:
    raise SystemExit('expected v16 control version not found')
s=s.replace(f'CONTROL_VERSION="{OLD}"',f'CONTROL_VERSION="{NEW}"',1)

s=s.replace(
'    platform TEXT NOT NULL,\n    dedupe_key TEXT,',
'    platform TEXT NOT NULL,\n    account_id TEXT NOT NULL DEFAULT \'default\',\n    dedupe_key TEXT,',1)

anchor='  try{this.sql.exec("ALTER TABLE jobs ADD COLUMN lease_generation INTEGER NOT NULL DEFAULT 0")}catch{}\n'
insert='''  try{this.sql.exec("ALTER TABLE jobs ADD COLUMN account_id TEXT NOT NULL DEFAULT 'default'")}catch{}\n  for(const raw of this.sql.exec("SELECT id,payload,account_id FROM jobs").toArray()){\n    if(raw.account_id&&raw.account_id!=="default")continue;\n    let payload={};try{payload=JSON.parse(raw.payload||"{}")}catch{}\n    const account=String(payload.account_id||payload.expected_account_id||payload.account||"default").trim().replace(/^@/,"").toLowerCase()||"default";\n    this.sql.exec("UPDATE jobs SET account_id=? WHERE id=?",account,raw.id);\n  }\n'''
if anchor not in s: raise SystemExit('migration anchor missing')
s=s.replace(anchor,anchor+insert,1)

s=s.replace(
'  this.sql.exec("CREATE INDEX IF NOT EXISTS idx_jobs_reserved_day ON jobs(platform,reserved_day,status,publication_started);");',
'  this.sql.exec("CREATE INDEX IF NOT EXISTS idx_jobs_reserved_day ON jobs(platform,reserved_day,status,publication_started);");\n  this.sql.exec("CREATE INDEX IF NOT EXISTS idx_jobs_target_status_created ON jobs(platform,account_id,status,created_at);");\n  this.sql.exec("CREATE INDEX IF NOT EXISTS idx_jobs_target_dedupe ON jobs(platform,account_id,dedupe_key);");',1)

s=s.replace(
'return {...p,id:r.id,platform:r.platform,dedupe_key:r.dedupe_key,status:r.status',
'return {...p,id:r.id,platform:r.platform,account_id:r.account_id||"default",target_key:r.platform+":"+(r.account_id||"default"),dedupe_key:r.dedupe_key,status:r.status',1)

old_enqueue=''' async enqueue(b){\n  const e=this.one(b.id); if(e)return {ok:true,job:this.row(e),deduplicated:true};\n  if(b.dedupe_key){const d=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND dedupe_key=? AND status<>'failed' ORDER BY created_at LIMIT 1",b.platform,String(b.dedupe_key)).toArray()[0];if(d)return {ok:true,job:this.row(d),deduplicated:true,dedupe_key:true};}\n  const mediaSha=String(b.media_sha256||"").trim().toLowerCase();\n  if(mediaSha&&/^[0-9a-f]{64}$/.test(mediaSha)){\n    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status<>'failed' ORDER BY created_at",b.platform).toArray()){\n      const prior=this.row(raw),priorSha=String(prior.media_sha256||"").trim().toLowerCase();\n      if(priorSha===mediaSha)return {ok:true,job:prior,deduplicated:true,media_sha256:true};\n    }\n  }\n  const sourceId=String(b.source_id||"").trim(),start=Number(b.source_start),end=Number(b.source_end);\n  if(sourceId&&Number.isFinite(start)&&Number.isFinite(end)&&end>start){\n    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status<>'failed' ORDER BY created_at",b.platform).toArray()){\n      const prior=this.row(raw);\n      if(String(prior.source_id||"")!==sourceId)continue;\n      const ps=Number(prior.source_start),pe=Number(prior.source_end);\n      if(Number.isFinite(ps)&&Number.isFinite(pe)&&pe>ps&&Math.max(start,ps)<Math.min(end,pe)){\n        return {ok:true,job:prior,deduplicated:true,timeline_overlap:true,requested:{source_id:sourceId,source_start:start,source_end:end}};\n      }\n    }\n  }\n  const created=now(); this.sql.exec("INSERT INTO jobs(id,platform,dedupe_key,payload,status,created_at) VALUES(?,?,?,?,?,?)",String(b.id),String(b.platform),b.dedupe_key?String(b.dedupe_key):null,JSON.stringify(b),"queued",created);\n  return {ok:true,job:this.row(this.one(b.id))};\n }'''
new_enqueue=''' async enqueue(b){\n  const accountId=String(b.account_id||b.expected_account_id||b.account||"default").trim().replace(/^@/,"").toLowerCase()||"default";\n  const e=this.one(b.id); if(e){const prior=this.row(e);if(prior.platform!==String(b.platform)||prior.account_id!==accountId)return {ok:false,error:"id_target_conflict"};return {ok:true,job:prior,deduplicated:true};}\n  if(b.dedupe_key){const d=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND account_id=? AND dedupe_key=? AND status<>'failed' ORDER BY created_at LIMIT 1",b.platform,accountId,String(b.dedupe_key)).toArray()[0];if(d)return {ok:true,job:this.row(d),deduplicated:true,dedupe_key:true};}\n  const mediaSha=String(b.media_sha256||"").trim().toLowerCase();\n  if(mediaSha&&/^[0-9a-f]{64}$/.test(mediaSha)){\n    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND account_id=? AND status<>'failed' ORDER BY created_at",b.platform,accountId).toArray()){\n      const prior=this.row(raw),priorSha=String(prior.media_sha256||"").trim().toLowerCase();\n      if(priorSha===mediaSha)return {ok:true,job:prior,deduplicated:true,media_sha256:true};\n    }\n  }\n  const sourceId=String(b.source_id||"").trim(),start=Number(b.source_start),end=Number(b.source_end);\n  if(sourceId&&Number.isFinite(start)&&Number.isFinite(end)&&end>start){\n    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND account_id=? AND status<>'failed' ORDER BY created_at",b.platform,accountId).toArray()){\n      const prior=this.row(raw);\n      if(String(prior.source_id||"")!==sourceId)continue;\n      const ps=Number(prior.source_start),pe=Number(prior.source_end);\n      if(Number.isFinite(ps)&&Number.isFinite(pe)&&pe>ps&&Math.max(start,ps)<Math.min(end,pe)){\n        return {ok:true,job:prior,deduplicated:true,timeline_overlap:true,requested:{source_id:sourceId,source_start:start,source_end:end,account_id:accountId}};\n      }\n    }\n  }\n  const created=now(); this.sql.exec("INSERT INTO jobs(id,platform,account_id,dedupe_key,payload,status,created_at) VALUES(?,?,?,?,?,?,?)",String(b.id),String(b.platform),accountId,b.dedupe_key?String(b.dedupe_key):null,JSON.stringify({...b,account_id:accountId}),"queued",created);\n  return {ok:true,job:this.row(this.one(b.id))};\n }'''
if old_enqueue not in s: raise SystemExit('enqueue v16 block missing')
s=s.replace(old_enqueue,new_enqueue,1)

old='''  const count=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND completed_day=? AND confirmed=1",b.platform,day).one().n||0);\n  const reserved=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND reserved_day=? AND ((status='leased') OR (status='uncertain' AND publication_started=1))",b.platform,day).one().n||0);\n  if(count+reserved>=DAILY_LIMIT)return {ok:true,job:null,daily_limit_reached:true,count,reserved,limit:DAILY_LIMIT};\n  const j=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status='queued' AND attempts<? ORDER BY created_at LIMIT 1",b.platform,MAX_ATTEMPTS).toArray()[0];\n  if(!j)return {ok:true,job:null,count,reserved,limit:DAILY_LIMIT};'''
new='''  const limits={kwai:100,tiktok:100,instagram:20,pinterest:20,linkedin:20,threads:100,youtube:3,facebook:10,x:10,twitter:10,bilibili:10,odysee:10,rumble:10,bluesky:10,reddit:10};\n  const limit=Number(limits[String(b.platform).toLowerCase()]||DAILY_LIMIT);\n  const candidates=this.sql.exec("SELECT q.* FROM jobs q WHERE q.platform=? AND q.status='queued' AND q.attempts<? AND NOT EXISTS (SELECT 1 FROM jobs a WHERE a.platform=q.platform AND a.account_id=q.account_id AND a.id<>q.id AND ((a.status='leased' AND a.lease_until>?) OR (a.status='uncertain' AND a.publication_started=1))) ORDER BY q.created_at,q.id LIMIT 200",b.platform,MAX_ATTEMPTS,t).toArray();\n  let j=null,count=0,reserved=0;\n  for(const candidate of candidates){\n    const accountId=String(candidate.account_id||"default");\n    count=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND account_id=? AND completed_day=? AND confirmed=1",b.platform,accountId,day).one().n||0);\n    reserved=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND account_id=? AND reserved_day=? AND ((status='leased') OR (status='uncertain' AND publication_started=1))",b.platform,accountId,day).one().n||0);\n    if(count+reserved<limit){j=candidate;break;}\n  }\n  if(!j)return {ok:true,job:null,daily_limit_reached:candidates.length>0,count,reserved,limit};'''
if old not in s: raise SystemExit('lease quota v16 block missing')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('PUBLISHER_TARGET_V17_APPLIED=1')
