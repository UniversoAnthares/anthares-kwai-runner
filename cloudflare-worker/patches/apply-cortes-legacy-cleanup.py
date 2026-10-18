#!/usr/bin/env python3
"""Add authenticated one-off removal of legacy Kwai queued jobs.

Never touch active CORTES jobs or jobs whose publication may have started.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"src"/"index.js"
s=p.read_text(encoding="utf-8-sig")
if 'async cleanupCortesLegacy()' in s:
 print("CORTES_LEGACY_CLEANUP_ALREADY_PATCHED=1")
 raise SystemExit(0)
anchor=' async stats(day){'
assert s.count(anchor)==1, 'queue stats insertion point changed'
method=""" async cleanupCortesLegacy(){
  const cutoff='2026-10-17T00:00:00.000Z';
  const candidates=this.sql.exec("SELECT id,status,publication_started,lease_until,created_at FROM jobs WHERE platform='kwai' AND id NOT LIKE 'kwai-cortes-%' AND created_at < ? ORDER BY created_at",cutoff).toArray();
  const removed=[],protectedJobs=[];
  const current=Date.now();
  for(const j of candidates){
    const safe=!j.publication_started&&(j.status==='queued'||j.status==='failed'||(j.status==='leased'&&Number(j.lease_until||0)<current));
    if(!safe){protectedJobs.push({id:j.id,status:j.status});continue;}
    this.sql.exec("DELETE FROM jobs WHERE id=? AND status=? AND COALESCE(publication_started,0)=0",j.id,j.status);
    if(!this.one(j.id))removed.push(j.id);
  }
  return {ok:true,removed_count:removed.length,removed_ids:removed,protected_count:protectedJobs.length,protected_jobs:protectedJobs,cutoff};
 }
"""
s=s.replace(anchor,method+anchor,1)
route='  if(url.pathname==="/queue-self-test"'
assert s.count(route)==1, 'queue route insertion point changed'
insertion="""  if(url.pathname==='/cortes/maintenance/cleanup-legacy-kwai'&&request.method==='POST'){
    const token=(request.headers.get('Authorization')||'').replace(/^Bearer\\s+/i,'').trim();
    const v=await verifyGithubOidc(token,env,['cloudflare-central-deploy.yml']);
    if(!v.ok||v.claims?.repository!=='UniversoAnthares/anthares-kwai-runner'
      ||!String(v.claims?.job_workflow_ref||v.claims?.workflow_ref||'').includes('/.github/workflows/cloudflare-central-deploy.yml@'))
      return json({ok:false,error:'unauthorized'},401);
    return json(await queueStub(env).cleanupCortesLegacy());
  }
"""
s=s.replace(route,insertion+route,1)
p.write_text(s,encoding='utf-8')
print('CORTES_LEGACY_CLEANUP_PATCHED=1')
