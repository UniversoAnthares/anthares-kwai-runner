#!/usr/bin/env python3
"""KW-04: OIDC read-only inspection of the actual Kwai CORTES queue.

Applied to the v18 deploy snapshot immediately before Cloudflare publication.
This adds no database migration, lease, publication, claim, mutation, or namespace.
"""
from pathlib import Path

path=Path(__file__).resolve().parents[1]/"src"/"index.js"
source=path.read_text(encoding="utf-8-sig")
if "async peekKwaiMediaJob()" in source and "/github-queue-get/kw04-peek" in source:
    print("KW04_READONLY_QUEUE_PEEK_ALREADY_APPLIED=1")
    raise SystemExit(0)

method_anchor=" async stats(day){"
assert source.count(method_anchor)==1, "queue DO method insertion point changed"
method=''' async peekKwaiMediaJob(){
  // The source-of-truth queue is inspected without acquiring a lease or
  // incrementing attempts. Only a current, eligible CORTES job is returned.
  const rows=this.sql.exec("SELECT * FROM jobs WHERE platform='kwai' AND status='queued' AND attempts<? AND id LIKE 'kwai-cortes-%' AND account_id IN ('lucasrosalem','default') ORDER BY created_at,id LIMIT 100",MAX_ATTEMPTS).toArray();
  for(const r of rows){
    const j=this.row(r);
    const account=String(j.expected_account||j.account_id||"").trim().replace(/^@/,"").toLowerCase();
    if(account!=="lucasrosalem"&&account!=="default")continue;
    if(!j.video_url||!String(j.video_url).startsWith("https://"))continue;
    if(!j.source_id||!Number.isFinite(Number(j.source_start))||!Number.isFinite(Number(j.source_end))||Number(j.source_end)<=Number(j.source_start))continue;
    return {ok:true,job:{
      id:j.id,platform:"kwai",status:"queued",expected_account:"lucasrosalem",
      source_id:j.source_id,source_start:j.source_start,source_end:j.source_end,
      video_url:j.video_url,video_title:j.video_title||"",
      content_sha256:j.content_sha256||j.media_content_sha256||"",
      media_sha256:j.media_sha256||"",media_hash_kind:j.media_hash_kind||""
    }};
  }
  return {ok:true,job:null,reason:"no_eligible_current_kwai_queue_job"};
 }
'''
source=source.replace(method_anchor,method+method_anchor,1)

route_anchor='  if(url.pathname==="/github-queue-get/lease"&&request.method==="GET"){'
assert source.count(route_anchor)==1, "OIDC queue router insertion point changed"
route='''  if(url.pathname==="/github-queue-get/kw04-peek"&&request.method==="GET"){
   const auth=request.headers.get("Authorization")||"";
   const token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():"";
   const v=await verifyGithubOidc(token,env);
   const workflow=String(v.claims?.job_workflow_ref||v.claims?.workflow_ref||"");
   if(!v.ok||v.claims?.repository!=="UniversoAnthares/anthares-kwai-runner"||
     !workflow.includes("UniversoAnthares/anthares-kwai-runner/.github/workflows/kwai-real-publish.yml@refs/heads/main"))
     return json({ok:false,error:"unauthorized"},401);
   return json(await queueStub(env).peekKwaiMediaJob());
  }
'''
source=source.replace(route_anchor,route+route_anchor,1)
assert source.count("async peekKwaiMediaJob()")==1 and source.count("/github-queue-get/kw04-peek")==1
path.write_text(source,encoding="utf-8")
print("KW04_READONLY_QUEUE_PEEK_APPLIED=1")
