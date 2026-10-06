import { DurableObject } from "cloudflare:workers";

﻿const memory = new Map();
const CONTROL_VERSION="2026-10-05-queue-fencing-v16";
const ROUTING_REVISION="2026-10-06-cloud-only-failover-r1";

function json(data, status=200) {
  return Response.json(data, {status, headers: {
    "cache-control":"no-store","access-control-allow-origin":"*","x-content-type-options":"nosniff"
  }});
}
function now(){ return new Date().toISOString(); }
const RENDER_SESSION_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwC4W6GV170DkktCjACQ8\nbql3gMbRF+F/+7Hup6I/ixHOCYoa7zDypZHMaxnzTYpbVoipMrSn1I4UEn/Fl/2m\nShxz1hSJ5OfUGmZ7MHZ8L+Z0mqY631m3md8UbyaBQqWMoANyE5SOUKk99X5Hz5CG\nPcm91HPst2PwsgjB+imhrguQ1EFRFqkoRUgOau0Af8do3buAUi5PPpSR/Rz4KEJV\nrcD18H754oXmRmAL+E0jFzJosW7Jvv/mK7TQasrpweLMz+OAngY7Weh6Huuttq+9\nZ5RRzjRIaU+W4NQo/1sRKJlJJtq8AChHuNQCB9/2l4rEXVLJRmJSyKqW0JLySPgY\nMQIDAQAB\n-----END PUBLIC KEY-----";
async function verifyRenderSessionSignature(request,body){
 const ts=Number(request.headers.get("X-Anthares-Render-Timestamp")||0),sig=String(request.headers.get("X-Anthares-Render-Signature")||"");
 if(!ts||Math.abs(Date.now()-ts)>300000||!sig)return false;
 try{const b64=RENDER_SESSION_PUBLIC_KEY.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\\s+/g,"");const bin=atob(b64),der=Uint8Array.from(bin,c=>c.charCodeAt(0));const key=await crypto.subtle.importKey("spki",der,{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);const raw=Uint8Array.from(atob(sig),c=>c.charCodeAt(0));const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(body));const hex=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,"0")).join("");return await crypto.subtle.verify("RSASSA-PKCS1-v1_5",key,raw,new TextEncoder().encode(String(ts)+"."+hex));}catch(e){return false;}
}
async function tiktokSessionState(request,env){
 if(request.method==="GET"){
  const token=(request.headers.get("Authorization")||"").replace(/^Bearer\s+/i,""); const auth=await verifyGithubOidc(token,env); if(!auth.ok)return json({error:"unauthorized"},401);
  const row=await read(env,"tiktok:session-state"); if(!row)return json({ok:false,available:false},404); return json({ok:true,available:true,updated_at:row.updated_at,state:row.state});
 }
 if(request.method==="POST"){
  const body=await request.text(); let trusted=await verifyRenderSessionSignature(request,body); if(!trusted){const token=(request.headers.get("Authorization")||"").replace(/^Bearer\s+/i,""); trusted=(await verifyGithubOidc(token,env)).ok;} if(!trusted)return json({error:"unauthorized"},401); let data; try{data=JSON.parse(body);}catch{return json({error:"invalid_json"},400);}
  if(!data||!Array.isArray(data.cookies)||data.cookies.length>256)return json({error:"invalid_storage_state"},400);
  await write(env,"tiktok:session-state",{updated_at:now(),state:{cookies:data.cookies,origins:Array.isArray(data.origins)?data.origins:[]}}); return json({ok:true,cookies:data.cookies.length,updated_at:now()});
 }
 return json({error:"method_not_allowed"},405);
}


function b64urlBytes(s){
  s=s.replace(/-/g,"+").replace(/_/g,"/");
  while(s.length%4)s+="=";
  const raw=atob(s),out=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);
  return out;
}
function b64urlJson(s){ return JSON.parse(atob(s.replace(/-/g,"+").replace(/_/g,"/").padEnd(Math.ceil(s.length/4)*4,"="))); }
let ghJwksCache=null,ghJwksAt=0;
async function verifyGithubOidc(token,env){
  const parts=String(token||"").split(".");
  if(parts.length!==3)return {ok:false,error:"jwt_format"};
  let header,claims;
  try{header=b64urlJson(parts[0]);claims=b64urlJson(parts[1]);}catch(e){return {ok:false,error:"jwt_decode"}}
  if(header.alg!=="RS256"||!header.kid)return {ok:false,error:"jwt_algorithm"};
  const nowSec=Math.floor(Date.now()/1000);
  if(claims.iss!=="https://token.actions.githubusercontent.com")return {ok:false,error:"jwt_issuer"};
  const aud=Array.isArray(claims.aud)?claims.aud:[claims.aud];
  if(!aud.includes("https://anthares-control.anthares1.workers.dev"))return {ok:false,error:"jwt_audience"};
  if(claims.exp<=nowSec||claims.nbf>nowSec+30)return {ok:false,error:"jwt_time"};
  if(!["UniversoAnthares/anthares-clipper","UniversoAnthares/anthares-kwai-runner"].includes(claims.repository))return {ok:false,error:"jwt_repository"};
  if(claims.ref!=="refs/heads/main")return {ok:false,error:"jwt_ref"};
  const allowedWorkflows=["anthares-cloud-failover.yml","anthares-tiktok-owned-youtube.yml","anthares-tiktok-github-hosted.yml","anthares-central-queue-smoke.yml","anthares-item5-cloud-acceptance.yml","anthares-item6-session-persistence.yml","kwai-real-publish.yml","anthares-kwai-real-seed.yml","anthares-tiktok-alt-real.yml","tiktok-real-publish.yml","tiktok-reconcile-v2.yml","tiktok-central-session-read.yml","tiktok-v15-reconcile-30.yml","tiktok-15env-replacement.yml","kwai-live-6h.yml"]; const wf=String(claims.job_workflow_ref||claims.workflow_ref||claims.workflow||""); const allowedRepo=claims.repository==="UniversoAnthares/anthares-kwai-runner"?"UniversoAnthares/anthares-kwai-runner":"UniversoAnthares/anthares-clipper"; const workflowOk=allowedWorkflows.some(name=>wf.includes(allowedRepo+"/.github/workflows/"+name+"@refs/heads/main")||wf.includes(allowedRepo+"/.github/workflows/"+name+"@")); if(!workflowOk)return {ok:false,error:"jwt_workflow"};
  if(!["schedule","workflow_dispatch","push"].includes(claims.event_name))return {ok:false,error:"jwt_event"};
  try{
    if(!ghJwksCache||Date.now()-ghJwksAt>3600000){
      const cfg=await (await fetch("https://token.actions.githubusercontent.com/.well-known/openid-configuration")).json();
      ghJwksCache=await (await fetch(cfg.jwks_uri)).json(); ghJwksAt=Date.now();
    }
    const jwk=ghJwksCache.keys.find(k=>k.kid===header.kid);
    if(!jwk)return {ok:false,error:"jwt_kid"};
    const key=await crypto.subtle.importKey("jwk",jwk,{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);
    const valid=await crypto.subtle.verify("RSASSA-PKCS1-v1_5",key,b64urlBytes(parts[2]),new TextEncoder().encode(parts[0]+"."+parts[1]));
    return valid?{ok:true,claims}:{ok:false,error:"jwt_signature"};
  }catch(e){return {ok:false,error:"jwt_verify"}}
}
function key(kind,id){ return kind+":"+id; }
async function read(env,k){ if(env.ANTHARES_STATE) return await env.ANTHARES_STATE.get(k,"json"); return memory.get(k)||null; }
async function write(env,k,v){ if(env.ANTHARES_STATE) await env.ANTHARES_STATE.put(k,JSON.stringify(v)); else memory.set(k,v); }
async function list(env,prefix){
  if(env.ANTHARES_STATE){ const l=await env.ANTHARES_STATE.list({prefix}); const rows=[]; for(const k of l.keys){ const v=await read(env,k.name); if(v) rows.push(v); } return rows; }
  return [...memory.entries()].filter(([k])=>k.startsWith(prefix)).map(([,v])=>v);
}
async function sha256(s){ const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join(""); }
const RETIRED_EXECUTORS=new Set(["local","pc","windows","oracle","google","google_compute"]);
function retiredExecutor(id){return RETIRED_EXECUTORS.has(String(id||"").toLowerCase());}
async function executorAuth(request,env,body,rawBody=""){
  const id=String(body.executor||"");
  if(retiredExecutor(id)) return false;
  const root=env.CONTROL_TOKEN||env.ANTHARES_CONTROL_HMAC_SECRET||"";
  const supplied=request.headers.get("X-Anthares-Executor-Key")||"";
  if(!root||!id||!supplied) return false;
  const expected=await sha256(root+":"+id);
  if(expected.length!==supplied.length) return false;
  let d=0; for(let i=0;i<expected.length;i++) d|=expected.charCodeAt(i)^supplied.charCodeAt(i);
  return d===0;
}
function adminAuth(request,env){ const t=env.CONTROL_TOKEN||env.ANTHARES_CONTROL_HMAC_SECRET||""; return !!t&&request.headers.get("Authorization")==="Bearer "+t; }
async function probe(url,timeoutMs=5000){
 const started=Date.now(),controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{ const r=await fetch(url,{headers:{"cache-control":"no-cache","accept":"application/json"},signal:controller.signal}); let meta={}; try{const ct=r.headers.get("content-type")||""; if(ct.includes("application/json")) meta=await r.json();}catch{} return {healthy:r.ok,status:r.status,latency_ms:Date.now()-started,checked_at:now(),ready_for_tiktok:meta.ready_for_tiktok,ready_for_cuts:meta.ready_for_cuts,session_bootstrapped:meta.session_bootstrapped}; }
 catch(e){ return {healthy:false,status:0,latency_ms:Date.now()-started,checked_at:now(),error:String(e&&e.name||"fetch_error")}; }
 finally{clearTimeout(timer);}
}
async function probeHls(url,timeoutMs=5000){
 const started=Date.now(),controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{const r=await fetch(url,{headers:{"cache-control":"no-cache","accept":"application/vnd.apple.mpegurl,*/*"},signal:controller.signal});const body=await r.text();const lm=r.headers.get("last-modified"),lmMs=lm?Date.parse(lm):NaN,staleSeconds=Number.isFinite(lmMs)?Math.max(0,Math.floor((Date.now()-lmMs)/1000)):null;const playlist=body.includes("#EXTM3U")&&body.includes("#EXTINF:");const fresh=staleSeconds!==null&&staleSeconds<=180;return {healthy:r.ok&&playlist&&fresh,status:r.status,latency_ms:Date.now()-started,checked_at:now(),playlist,fresh,last_modified:lm,stale_seconds:staleSeconds};}
 catch(e){return {healthy:false,status:0,latency_ms:Date.now()-started,checked_at:now(),error:String(e&&e.name||"fetch_error")};}
 finally{clearTimeout(timer);}
}
async function activeProbes(env){
 const targets={
  render:env.RENDER_HEALTH_URL||"https://anthares-tiktok-render-rootless.onrender.com/health",
  
 };
 const pairs=await Promise.all(Object.entries(targets).filter(([,url])=>!!url).map(async([executor,url])=>[executor,{executor,url,...await probe(url)}]));
 const hls=env.HLS_HEALTH_URL||"";
 if(hls)pairs.push(["hls_origin",{executor:"hls_origin",url:hls,...await probeHls(hls)}]);
 return Object.fromEntries(pairs);
}
async function refreshProbeState(env){ return await activeProbes(env); }
const DAILY_LIMIT=100;
const MAX_ATTEMPTS=5;
function localDay(){
 return new Intl.DateTimeFormat("en-CA",{timeZone:"America/Campo_Grande",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
}
function queueStub(env){ const id=env.ANTHARES_QUEUE.idFromName("global"); return env.ANTHARES_QUEUE.get(id); }

export class AntharesQueue extends DurableObject {
 constructor(ctx,env){
  super(ctx,env); this.sql=ctx.storage.sql;
  this.sql.exec(`CREATE TABLE IF NOT EXISTS jobs(
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    dedupe_key TEXT,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT,
    lease_until INTEGER,
    publication_started INTEGER NOT NULL DEFAULT 0,
    publication_started_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    lease_generation INTEGER NOT NULL DEFAULT 0,
    confirmed INTEGER NOT NULL DEFAULT 0,
    remote_id TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    completed_day TEXT,
    uncertain_at TEXT,
    failed_at TEXT,
    error_class TEXT,
    error_message TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_jobs_platform_status_created ON jobs(platform,status,created_at);
  CREATE INDEX IF NOT EXISTS idx_jobs_platform_dedupe ON jobs(platform,dedupe_key);
  CREATE INDEX IF NOT EXISTS idx_jobs_completed_day ON jobs(platform,completed_day,confirmed);`);
  try{this.sql.exec("ALTER TABLE jobs ADD COLUMN reserved_day TEXT")}catch{}
  try{this.sql.exec("ALTER TABLE jobs ADD COLUMN lease_generation INTEGER NOT NULL DEFAULT 0")}catch{}
  this.sql.exec("CREATE INDEX IF NOT EXISTS idx_jobs_reserved_day ON jobs(platform,reserved_day,status,publication_started);");
 }
 row(r){ if(!r)return null; let p={}; try{p=JSON.parse(r.payload||"{}")}catch{} return {...p,id:r.id,platform:r.platform,dedupe_key:r.dedupe_key,status:r.status,owner:r.owner,lease_until:r.lease_until?new Date(r.lease_until).toISOString():null,publication_started:!!r.publication_started,publication_started_at:r.publication_started_at,attempts:Number(r.attempts||0),lease_generation:Number(r.lease_generation||0),confirmed:!!r.confirmed,remote_id:r.remote_id,created_at:r.created_at,completed_at:r.completed_at,uncertain_at:r.uncertain_at,failed_at:r.failed_at,error_class:r.error_class,error_message:r.error_message}; }
 one(id){ return this.sql.exec("SELECT * FROM jobs WHERE id=?",id).toArray()[0]||null; }
 async enqueue(b){
  const e=this.one(b.id); if(e)return {ok:true,job:this.row(e),deduplicated:true};
  if(b.dedupe_key){const d=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND dedupe_key=? AND status<>'failed' ORDER BY created_at LIMIT 1",b.platform,String(b.dedupe_key)).toArray()[0];if(d)return {ok:true,job:this.row(d),deduplicated:true,dedupe_key:true};}
  const mediaSha=String(b.media_sha256||"").trim().toLowerCase();
  if(mediaSha&&/^[0-9a-f]{64}$/.test(mediaSha)){
    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status<>'failed' ORDER BY created_at",b.platform).toArray()){
      const prior=this.row(raw),priorSha=String(prior.media_sha256||"").trim().toLowerCase();
      if(priorSha===mediaSha)return {ok:true,job:prior,deduplicated:true,media_sha256:true};
    }
  }
  const sourceId=String(b.source_id||"").trim(),start=Number(b.source_start),end=Number(b.source_end);
  if(sourceId&&Number.isFinite(start)&&Number.isFinite(end)&&end>start){
    for(const raw of this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status<>'failed' ORDER BY created_at",b.platform).toArray()){
      const prior=this.row(raw);
      if(String(prior.source_id||"")!==sourceId)continue;
      const ps=Number(prior.source_start),pe=Number(prior.source_end);
      if(Number.isFinite(ps)&&Number.isFinite(pe)&&pe>ps&&Math.max(start,ps)<Math.min(end,pe)){
        return {ok:true,job:prior,deduplicated:true,timeline_overlap:true,requested:{source_id:sourceId,source_start:start,source_end:end}};
      }
    }
  }
  const created=now(); this.sql.exec("INSERT INTO jobs(id,platform,dedupe_key,payload,status,created_at) VALUES(?,?,?,?,?,?)",String(b.id),String(b.platform),b.dedupe_key?String(b.dedupe_key):null,JSON.stringify(b),"queued",created);
  return {ok:true,job:this.row(this.one(b.id))};
 }
 async lease(b,day){
  const t=Date.now();
  for(const x of this.sql.exec("SELECT id FROM jobs WHERE platform=? AND status='leased' AND lease_until<=? AND publication_started=1",b.platform,t).toArray()) this.sql.exec("UPDATE jobs SET status='uncertain',uncertain_at=?,lease_until=NULL WHERE id=?",now(),x.id);
  for(const x of this.sql.exec("SELECT id FROM jobs WHERE platform=? AND status='leased' AND lease_until<=? AND publication_started=0",b.platform,t).toArray()) this.sql.exec("UPDATE jobs SET status='queued',owner=NULL,reserved_day=NULL,lease_until=NULL WHERE id=?",x.id);
  const count=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND completed_day=? AND confirmed=1",b.platform,day).one().n||0);
  const reserved=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND reserved_day=? AND ((status='leased') OR (status='uncertain' AND publication_started=1))",b.platform,day).one().n||0);
  if(count+reserved>=DAILY_LIMIT)return {ok:true,job:null,daily_limit_reached:true,count,reserved,limit:DAILY_LIMIT};
  const j=this.sql.exec("SELECT * FROM jobs WHERE platform=? AND status='queued' AND attempts<? ORDER BY created_at LIMIT 1",b.platform,MAX_ATTEMPTS).toArray()[0];
  if(!j)return {ok:true,job:null,count,reserved,limit:DAILY_LIMIT};
  const until=t+Math.min(Math.max(Number(b.ttl_seconds)||600,60),3600)*1000;
  this.sql.exec("UPDATE jobs SET status='leased',owner=?,lease_until=?,reserved_day=?,publication_started=0,attempts=attempts+1,lease_generation=lease_generation+1 WHERE id=? AND status='queued'",b.executor,until,day,j.id);
  return {ok:true,job:this.row(this.one(j.id)),count,reserved:reserved+1,limit:DAILY_LIMIT};
 }
 async renew(b){
  const j=this.one(b.id); if(!j)return {ok:false,error:"not_found",status:404};
  if(j.owner!==b.executor)return {ok:false,error:"lease_owner_mismatch",status:409};
  if(Number(b.lease_generation)!==Number(j.lease_generation||0))return {ok:false,error:"stale_lease_generation",status:409};
  if(j.status!=="leased")return {ok:false,error:"invalid_state",status:409};
  const t=Date.now(),current=Number(j.lease_until||0);
  if(!current||current<=t)return {ok:false,error:"lease_expired",status:409};
  const ttl=Math.min(Math.max(Number(b.ttl_seconds)||600,60),3600)*1000;
  const until=Math.max(current+1000,t+ttl);
  this.sql.exec("UPDATE jobs SET lease_until=? WHERE id=? AND status='leased' AND owner=? AND lease_until>?",until,j.id,b.executor,t);
  const updated=this.one(j.id);
  if(!updated||updated.owner!==b.executor||updated.status!=="leased"||Number(updated.lease_until||0)<=current)return {ok:false,error:"lease_renew_conflict",status:409};
  return {ok:true,job:this.row(updated),previous_lease_until:new Date(current).toISOString()};
 }
 async started(b){const j=this.one(b.id);if(!j)return {ok:false,error:"not_found",status:404};if(j.owner!==b.executor||j.status!=="leased")return {ok:false,error:"lease_owner_mismatch",status:409};if(Number(b.lease_generation)!==Number(j.lease_generation||0))return {ok:false,error:"stale_lease_generation",status:409};this.sql.exec("UPDATE jobs SET publication_started=1,publication_started_at=? WHERE id=?",now(),j.id);return {ok:true,job:this.row(this.one(j.id))};}
 async complete(b,day){const j=this.one(b.id);if(!j)return {ok:false,error:"not_found",status:404};if(j.owner!==b.executor)return {ok:false,error:"lease_owner_mismatch",status:409};if(Number(b.lease_generation)!==Number(j.lease_generation||0))return {ok:false,error:"stale_lease_generation",status:409};if(j.status!=="leased")return {ok:false,error:"invalid_state",status:409};if(b.confirmed){if(!j.publication_started)return {ok:false,error:"publication_not_started",status:409};if(!String(b.remote_id||j.remote_id||b.confirmation_evidence||"").trim())return {ok:false,error:"confirmation_evidence_required",status:422};this.sql.exec("UPDATE jobs SET status='published',confirmed=1,remote_id=?,completed_at=?,completed_day=?,reserved_day=NULL,uncertain_at=NULL,lease_until=NULL WHERE id=?",b.remote_id||j.remote_id||null,now(),day,j.id);}else this.sql.exec("UPDATE jobs SET status='uncertain',confirmed=0,remote_id=?,completed_at=NULL,completed_day=NULL,reserved_day=NULL,uncertain_at=?,lease_until=NULL WHERE id=?",b.remote_id||j.remote_id||null,now(),j.id);if(b.confirmed)await this.recordSuccess(b.executor,j.platform); return {ok:true,job:this.row(this.one(j.id))};}
 async fail(b){const j=this.one(b.id);if(!j)return {ok:false,error:"not_found",status:404};if(j.owner!==b.executor)return {ok:false,error:"lease_owner_mismatch",status:409};if(Number(b.lease_generation)!==Number(j.lease_generation||0))return {ok:false,error:"stale_lease_generation",status:409};const ec=String(b.error_class||"unknown"),em=String(b.error_message||"").slice(0,500),ts=now(); await this.recordFailure(b.executor,j.platform,!!b.published_possible||!!j.publication_started);if(b.published_possible||j.publication_started)this.sql.exec("UPDATE jobs SET status='uncertain',error_class=?,error_message=?,failed_at=?,uncertain_at=?,lease_until=NULL WHERE id=?",ec,em,ts,ts,j.id);else if(Number(j.attempts||0)<MAX_ATTEMPTS)this.sql.exec("UPDATE jobs SET status='queued',owner=NULL,publication_started=0,error_class=?,error_message=?,failed_at=?,lease_until=NULL WHERE id=?",ec,em,ts,j.id);else this.sql.exec("UPDATE jobs SET status='failed',error_class=?,error_message=?,failed_at=?,lease_until=NULL WHERE id=?",ec,em,ts,j.id);return {ok:true,job:this.row(this.one(j.id))};}
 async reconcile(b,day){const j=this.one(b.id);if(!j)return {ok:false,error:"not_found",status:404};if(b.confirmed_absent&&j.status==="queued"){this.sql.exec("UPDATE jobs SET owner=NULL,lease_until=NULL,publication_started=0,confirmed=0,reserved_day=NULL,uncertain_at=NULL WHERE id=?",j.id);return {ok:true,job:this.row(this.one(j.id)),already_reconciled:true};}if(b.confirmed_absent&&j.status==="published"){return {ok:true,job:this.row(j),already_reconciled:true};}if(j.owner&&j.owner!==b.executor)return {ok:false,error:"lease_owner_mismatch",status:409,job:this.row(j)}; if(j.status==="published"&&b.confirmed_absent){return {ok:true,job:this.row(j),already_reconciled:true};} if(j.status!=="uncertain")return {ok:false,error:"invalid_state",status:409,job:this.row(j)};if(b.confirmed){if(!String(b.remote_id||j.remote_id||b.confirmation_evidence||"").trim())return {ok:false,error:"confirmation_evidence_required",status:422};this.sql.exec("UPDATE jobs SET status='published',confirmed=1,remote_id=?,completed_at=?,completed_day=?,uncertain_at=NULL,lease_until=NULL WHERE id=?",b.remote_id||j.remote_id||null,now(),day,j.id);await this.recordSuccess(b.executor,j.platform);}else if(b.confirmed_absent&&Number(j.attempts||0)<MAX_ATTEMPTS)this.sql.exec("UPDATE jobs SET status='queued',confirmed=0,owner=NULL,publication_started=0,uncertain_at=NULL,lease_until=NULL WHERE id=?",j.id);else this.sql.exec("UPDATE jobs SET status='uncertain',uncertain_at=COALESCE(uncertain_at,?),lease_until=NULL WHERE id=?",now(),j.id);return {ok:true,job:this.row(this.one(j.id))};}
 async stats(day){const counts={};for(const p of ["tiktok","kwai"])counts[p]=Number(this.sql.exec("SELECT COUNT(*) AS n FROM jobs WHERE platform=? AND completed_day=? AND confirmed=1",p,day).one().n||0);const states={};for(const r of this.sql.exec("SELECT status,COUNT(*) AS n FROM jobs GROUP BY status").toArray())states[r.status]=Number(r.n||0);const duplicateKeys=Number(this.sql.exec("SELECT COUNT(*) AS n FROM (SELECT platform,dedupe_key,COUNT(*) c FROM jobs WHERE dedupe_key IS NOT NULL AND status<>'failed' GROUP BY platform,dedupe_key HAVING c>1)").one().n||0);return {counts,total_confirmed:counts.tiktok+counts.kwai,remaining:{tiktok:Math.max(0,DAILY_LIMIT-counts.tiktok),kwai:Math.max(0,DAILY_LIMIT-counts.kwai)},dedupe:{duplicate_keys:duplicateKeys,healthy:duplicateKeys===0},jobs:{queued:states.queued||0,leased:states.leased||0,uncertain:states.uncertain||0,failed:states.failed||0,published:states.published||0}};}
 async setExecutor(row){await this.ctx.storage.put("executor:"+row.executor,row);return row;}
 async recordSuccess(executor,platform){const prev=await this.getExecutor(executor)||{executor};const today=localDay();const publishedToday=Number(prev.published_day===today?prev.published_today||0:0)+1;const row={...prev,last_success_at:now(),last_success_platform:platform,published_today:publishedToday,published_day:today,consecutive_failures:0,failures:0,disabled_until:null};await this.setExecutor(row);return row;}
 async recordFailure(executor,platform,uncertain=false){const prev=await this.getExecutor(executor)||{executor};const n=Number(prev.consecutive_failures||prev.failures||0)+1;const row={...prev,last_failure_at:now(),last_failure_platform:platform,consecutive_failures:n,failures:n};if(n>=3)row.disabled_until=new Date(Date.now()+15*60*1000).toISOString();await this.setExecutor(row);return row;}
 async getExecutor(id){return await this.ctx.storage.get("executor:"+id)||null;}
 async executors(){const m=await this.ctx.storage.list({prefix:"executor:"});return [...m.values()];}
 async setRouting(selected){const prev=await this.ctx.storage.get("routing:current")||{selected:{},switched_at:{}};const switched={...(prev.switched_at||{})};for(const [role,host] of Object.entries(selected))if((prev.selected||{})[role]!==host)switched[role]=now();const row={selected,switched_at:switched,updated_at:now()};await this.ctx.storage.put("routing:current",row);return row;}
 async selfTest(){
  const prefix="selftest-"+crypto.randomUUID(),platform="__selftest__",claimPlatform="__selftest_claim__",renewPlatform="__selftest_renew__",ids=[prefix+"-a",prefix+"-b",prefix+"-c",prefix+"-d",prefix+"-e"];
  try{
   const claimId=prefix+"-single-claim";
   await this.enqueue({id:claimId,platform:claimPlatform,dedupe_key:claimId,source_id:"selftest"});
   const [claimA,claimB]=await Promise.all([this.lease({executor:"selftest-claim-a",platform:claimPlatform,ttl_seconds:60},localDay()),this.lease({executor:"selftest-claim-b",platform:claimPlatform,ttl_seconds:60},localDay())]);
   const claimWinners=[claimA,claimB].filter(x=>x&&x.job&&x.job.id===claimId);
   if(claimWinners.length!==1)throw new Error("single_job_double_claim_failed");
   const claimLoser=[claimA,claimB].find(x=>!x||!x.job);
   if(!claimLoser)throw new Error("single_job_double_claim_no_loser");

   const renewId=prefix+"-renew";
   await this.enqueue({id:renewId,platform:renewPlatform,dedupe_key:renewId,source_id:"selftest"});
   const renewLease=await this.lease({executor:"selftest-renew-owner",platform:renewPlatform,ttl_seconds:60},localDay());
   if(!renewLease.job||renewLease.job.id!==renewId)throw new Error("renew_precondition_failed");
   const beforeRenew=Date.parse(renewLease.job.lease_until);
   const wrongOwnerRenew=await this.renew({executor:"selftest-renew-other",id:renewId,lease_generation:renewLease.job.lease_generation,ttl_seconds:60});
   if(wrongOwnerRenew.ok||wrongOwnerRenew.error!=="lease_owner_mismatch")throw new Error("renew_wrong_owner_not_rejected");
   const validRenew=await this.renew({executor:"selftest-renew-owner",id:renewId,lease_generation:renewLease.job.lease_generation,ttl_seconds:60});
   const afterRenew=Date.parse(validRenew.job?.lease_until||0);
   if(!validRenew.ok||afterRenew<=beforeRenew)throw new Error("renew_did_not_extend");
   const repeatedRenew=await this.renew({executor:"selftest-renew-owner",id:renewId,lease_generation:renewLease.job.lease_generation,ttl_seconds:60});
   if(!repeatedRenew.ok||Date.parse(repeatedRenew.job?.lease_until||0)<=afterRenew)throw new Error("repeated_renew_did_not_extend");
   this.sql.exec("UPDATE jobs SET status='queued' WHERE id=?",renewId);
   const wrongStateRenew=await this.renew({executor:"selftest-renew-owner",id:renewId,lease_generation:renewLease.job.lease_generation,ttl_seconds:60});
   if(wrongStateRenew.ok||wrongStateRenew.error!=="invalid_state")throw new Error("renew_invalid_state_not_rejected");
   this.sql.exec("UPDATE jobs SET status='leased',lease_until=? WHERE id=?",Date.now()-1000,renewId);
   const expiredRenew=await this.renew({executor:"selftest-renew-owner",id:renewId,lease_generation:renewLease.job.lease_generation,ttl_seconds:60});
   if(expiredRenew.ok||expiredRenew.error!=="lease_expired")throw new Error("renew_expired_not_rejected");
   await this.enqueue({id:ids[0],platform,dedupe_key:prefix+"-dup",source_id:"selftest"});
   const d=await this.enqueue({id:prefix+"-dup2",platform,dedupe_key:prefix+"-dup",source_id:"selftest"});
   if(!d.deduplicated||d.job.id!==ids[0])throw new Error("dedupe_failed");
   const timelineA=prefix+"-timeline-a",timelineB=prefix+"-timeline-b";
   await this.enqueue({id:timelineA,platform,dedupe_key:timelineA,source_id:"same-source",source_start:100,source_end:160});
   const timelineDup=await this.enqueue({id:timelineB,platform,dedupe_key:timelineB,source_id:"same-source",source_start:159,source_end:220});
   if(!timelineDup.deduplicated||!timelineDup.timeline_overlap||timelineDup.job.id!==timelineA)throw new Error("timeline_overlap_dedupe_failed");
   for(const id of ids.slice(1))await this.enqueue({id,platform,dedupe_key:id,source_id:"selftest"});
   const [l1,l2]=await Promise.all([this.lease({executor:"selftest-a",platform,ttl_seconds:60},localDay()),this.lease({executor:"selftest-b",platform,ttl_seconds:60},localDay())]);
   if(!l1.job||!l2.job||l1.job.id===l2.job.id)throw new Error("concurrent_lease_collision"); const prematureComplete=await this.complete({executor:l1.job.owner,id:l1.job.id,lease_generation:l1.job.lease_generation,confirmed:true,remote_id:"premature"},localDay()); if(prematureComplete.ok||prematureComplete.error!=="publication_not_started")throw new Error("premature_complete_not_rejected");
   this.sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1000,l1.job.id);
   const recovered=await this.lease({executor:"selftest-c",platform,ttl_seconds:60},localDay());
   if(!recovered.job||recovered.job.id!==l1.job.id||recovered.job.attempts<2)throw new Error("expired_lease_not_recovered");
   if(Number(recovered.job.lease_generation)<=Number(l1.job.lease_generation))throw new Error("lease_generation_not_incremented");
   const staleStart=await this.started({executor:recovered.job.owner,id:recovered.job.id,lease_generation:l1.job.lease_generation});
   if(staleStart.ok||staleStart.error!=="stale_lease_generation")throw new Error("stale_generation_start_not_rejected");
   const staleComplete=await this.complete({executor:recovered.job.owner,id:recovered.job.id,lease_generation:l1.job.lease_generation,confirmed:false},localDay());
   if(staleComplete.ok||staleComplete.error!=="stale_lease_generation")throw new Error("stale_generation_complete_not_rejected");
   const staleFail=await this.fail({executor:recovered.job.owner,id:recovered.job.id,lease_generation:l1.job.lease_generation,error_class:"stale",error_message:"stale"});
   if(staleFail.ok||staleFail.error!=="stale_lease_generation")throw new Error("stale_generation_fail_not_rejected");
   await this.started({executor:l2.job.owner,id:l2.job.id,lease_generation:l2.job.lease_generation});
   this.sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1000,l2.job.id);
   const afterStartedExpiry=await this.lease({executor:"selftest-d",platform,ttl_seconds:60},localDay());
   const protectedRow=this.row(this.one(l2.job.id));
   if(protectedRow.status!=="uncertain")throw new Error("started_expiry_not_uncertain"); const noReconcileEvidence=await this.reconcile({executor:l2.job.owner,id:l2.job.id,confirmed:true},localDay()); if(noReconcileEvidence.ok||noReconcileEvidence.error!=="confirmation_evidence_required")throw new Error("reconcile_without_evidence_not_rejected");
   if(!afterStartedExpiry.job||afterStartedExpiry.job.id===l2.job.id)throw new Error("started_job_released_again");
   const failExec="selftest-fail"; for(let k=0;k<3;k++)await this.recordFailure(failExec,platform,false); const failState=await this.getExecutor(failExec); if(!failState||Number(failState.consecutive_failures)!==3||!failState.disabled_until)throw new Error("consecutive_failure_threshold_failed"); await this.recordSuccess(failExec,platform); const resetState=await this.getExecutor(failExec); if(!resetState||Number(resetState.consecutive_failures)!==0||resetState.disabled_until)throw new Error("failure_counter_reset_failed");
   const failed=await this.fail({executor:"selftest-d",id:afterStartedExpiry.job.id,lease_generation:afterStartedExpiry.job.lease_generation,error_class:"selftest",error_message:"expected",published_possible:false});
   if(!failed.job||failed.job.status!=="queued")throw new Error("failure_not_requeued");
   const recoveredFailure=await this.lease({executor:"selftest-e",platform,ttl_seconds:60},localDay());
   if(!recoveredFailure.job||recoveredFailure.job.id!==afterStartedExpiry.job.id||recoveredFailure.job.attempts<2)throw new Error("failed_job_not_recovered");
   await this.started({executor:"selftest-e",id:recoveredFailure.job.id,lease_generation:recoveredFailure.job.lease_generation}); const missingProof=await this.complete({executor:"selftest-e",id:recoveredFailure.job.id,lease_generation:recoveredFailure.job.lease_generation,confirmed:true},localDay()); if(missingProof.ok)throw new Error("missing_confirmation_proof_accepted");
   const confirmed=await this.complete({executor:"selftest-e",id:recoveredFailure.job.id,lease_generation:recoveredFailure.job.lease_generation,confirmed:true,remote_id:"selftest-remote"},localDay());
   if(!confirmed.job||confirmed.job.status!=="published"||!confirmed.job.confirmed||confirmed.job.remote_id!=="selftest-remote")throw new Error("confirmation_not_recorded");
   const reconciled=await this.reconcile({executor:l2.job.owner,id:l2.job.id,confirmed_absent:true},localDay());
   if(!reconciled.job||reconciled.job.status!=="queued")throw new Error("uncertain_not_requeued_after_absence_confirmation");
   const recoveredUncertain=await this.lease({executor:"selftest-f",platform,ttl_seconds:60},localDay());
   if(!recoveredUncertain.job||recoveredUncertain.job.id!==l2.job.id)throw new Error("reconciled_job_not_recovered");
   await this.started({executor:"selftest-f",id:l2.job.id,lease_generation:recoveredUncertain.job.lease_generation});
   const confirmedAfterReconcile=await this.complete({executor:"selftest-f",id:l2.job.id,lease_generation:recoveredUncertain.job.lease_generation,confirmed:true,remote_id:"selftest-reconciled"},localDay());
   if(!confirmedAfterReconcile.job||confirmedAfterReconcile.job.status!=="published"||!confirmedAfterReconcile.job.confirmed)throw new Error("reconciled_confirmation_failed");
   return {ok:true,dedupe:true,timeline_overlap_dedupe:true,premature_complete_rejected:true,reconcile_without_evidence_rejected:true,complete_without_evidence_rejected:true,concurrent_unique:true,single_job_double_claim:true,lease_renew_owner_only:true,lease_renew_extended:true,lease_renew_repeated:true,lease_renew_invalid_state_rejected:true,lease_renew_expired_rejected:true,lease_generation_incremented:true,stale_generation_start_rejected:true,stale_generation_complete_rejected:true,stale_generation_fail_rejected:true,expired_unstarted_recovered:true,started_expiry_protected:true,failure_requeued:true,failed_job_recovered:true,confirmation_recorded:true,uncertain_reconciled:true,reconciled_job_recovered:true,consecutive_failure_threshold:true,failure_counter_reset:true};
  }finally{
   this.sql.exec("DELETE FROM jobs WHERE platform=? AND id LIKE ?",platform,prefix+"%");
   this.sql.exec("DELETE FROM jobs WHERE platform IN (?,?) AND id LIKE ?",claimPlatform,renewPlatform,prefix+"%");
   const xs=await this.ctx.storage.list({prefix:"executor:selftest-"});
   for(const k of xs.keys())await this.ctx.storage.delete(k);
  }
 }
}
function priorities(){return {cuts:["render","github"],tiktok:["render","github"],kwai:["github"],kwai_live:["hls_origin","github"],control:["cloudflare","github","render"]};}
const ROLE_CAPACITY={cuts:["cuts"],tiktok:["tiktok"],kwai:["kwai"],kwai_live:["kwai_live"],control:["control"]};
function capacityOk(role,e){if(!e)return false;const cap=Number(e.daily_limit??e.capacity_daily??0);const used=Number(e.published_today??0);if(cap>0&&used>=cap)return false;const caps=Array.isArray(e.capabilities)?e.capabilities:[];const required=ROLE_CAPACITY[role]||[];if(required.length&&caps.length&&!required.some(x=>caps.includes(x)))return false;return true;}
async function dailyConfirmed(env,platform){
 const today=localDay(),jobs=await list(env,"job:");
 return jobs.filter(j=>j.platform===platform&&j.confirmed&&String(j.completed_at||"").startsWith(today)).length;
}
async function persistRouting(env,selected){ return await queueStub(env).setRouting(selected); }
function selectHost(role,executors){
 const order=priorities()[role]||[],t=Date.now();
 return order.find(id=>{const e=executors.find(x=>x.executor===id); if(!e||e.disabled_until&&Date.parse(e.disabled_until)>t)return false; if(e.heartbeat_at&&t-Date.parse(e.heartbeat_at)>10*60*1000)return false; if(!capacityOk(role,e))return false; if(role==="cuts"&&id==="render"&&!(e.probe&&e.probe.ready_for_cuts===true))return false; if(role==="tiktok"){if(id==="render"){if(!(e.probe&&e.probe.ready_for_tiktok===true))return false;}else{if(!(e.ready_for_tiktok===true&&Date.parse(e.tiktok_ready_until||0)>t))return false;}} return e.healthy!==false;})||null;
}
async function publicState(env){
 const probes=await refreshProbeState(env),executors=await queueStub(env).executors(),merged=executors.map(e=>probes[e.executor]?{...e,healthy:probes[e.executor].healthy,heartbeat_at:probes[e.executor].checked_at,probe:probes[e.executor]}:e);
 for(const [id,p] of Object.entries(probes)) if(!merged.some(e=>e.executor===id)) merged.push({executor:id,healthy:p.healthy,heartbeat_at:p.checked_at,probe:p});
 const selected={cuts:selectHost("cuts",merged),tiktok:selectHost("tiktok",merged),kwai:selectHost("kwai",merged),kwai_live:selectHost("kwai_live",merged),control:"cloudflare"};
 const reasons={}; for(const role of Object.keys(selected)){const chosen=selected[role]; reasons[role]=chosen?`selected:${chosen}`:"no_eligible_executor";}
 const routing=await persistRouting(env,selected);
 return {probes,executors:merged,selected,routing,reasons};
}
async function failoverSelfTest(){
 const until=new Date(Date.now()+15*60*1000).toISOString(),hb=now(),stale=new Date(Date.now()-11*60*1000).toISOString(),disabled=until;
 const base=[
  {executor:"render",healthy:true,heartbeat_at:hb,probe:{ready_for_tiktok:true,ready_for_cuts:true},capabilities:["cuts","tiktok"],daily_limit:100,published_today:0},
  {executor:"github",healthy:true,heartbeat_at:hb,ready_for_tiktok:true,tiktok_ready_until:until,capabilities:["cuts","tiktok","kwai","kwai_live","control"],daily_limit:100,published_today:0},
  {executor:"hls_origin",healthy:true,heartbeat_at:hb,capabilities:["kwai_live"]},
  ...["local","oracle","google_compute"].map(executor=>({executor,healthy:true,heartbeat_at:hb,ready_for_tiktok:true,tiktok_ready_until:until,capabilities:["cuts","tiktok","kwai","kwai_live","control"]}))
 ];
 const withPatch=changes=>base.map(e=>changes[e.executor]?{...e,...changes[e.executor]}:e);
 const primary=selectHost("tiktok",base),github=selectHost("tiktok",withPatch({render:{healthy:false}})),none=selectHost("tiktok",withPatch({render:{healthy:false},github:{healthy:false}})),recovered=selectHost("tiktok",withPatch({render:{healthy:true,heartbeat_at:hb,disabled_until:null,published_today:0,probe:{ready_for_tiktok:true,ready_for_cuts:true}}}));
 const checks={
  primary_render:primary==="render",
  render_offline_github:github==="github",
  all_cloud_offline_null:none===null,
  stale_heartbeat_github:selectHost("tiktok",withPatch({render:{heartbeat_at:stale}}))==="github",
  circuit_breaker_github:selectHost("tiktok",withPatch({render:{disabled_until:disabled}}))==="github",
  capacity_github:selectHost("tiktok",withPatch({render:{daily_limit:100,published_today:100}}))==="github",
  readiness_github:selectHost("tiktok",withPatch({render:{probe:{ready_for_tiktok:false,ready_for_cuts:true}}}))==="github",
  recovery_returns_render:recovered==="render",
  cuts_failover:selectHost("cuts",withPatch({render:{healthy:false}}))==="github",
  kwai_github_only:selectHost("kwai",base)==="github",
  kwai_outage_null:selectHost("kwai",withPatch({github:{healthy:false}}))===null,
  live_hls_primary:selectHost("kwai_live",base)==="hls_origin",
  live_hls_failover:selectHost("kwai_live",withPatch({hls_origin:{healthy:false}}))==="github",
  retired_absent_priorities:Object.values(priorities()).flat().every(id=>!retiredExecutor(id)),
  retired_injected_never_selected:["cuts","tiktok","kwai","kwai_live"].every(role=>!retiredExecutor(selectHost(role,base)))
 };
 return {ok:Object.values(checks).every(Boolean),routing_revision:ROUTING_REVISION,checks,primary,after_render_failure:github,after_github_failure:none,recovered_primary:recovered,local_retired:true,oracle_retired:true,google_compute_retired:true,priority:priorities().tiktok};
}
export default {
 async fetch(request,env={}){
  const url=new URL(request.url);
  if(url.pathname==="/tiktok/session-state") return await tiktokSessionState(request,env);
  if(url.pathname==="/failover-self-test") return json(await failoverSelfTest());
  if(url.pathname==="/health") return json({ok:true,service:"anthares-control",provider:"cloudflare",role:"control-plane",version:CONTROL_VERSION,persistent_state:!!env.ANTHARES_STATE,queue_bound:!!env.ANTHARES_QUEUE,pc_fallback:false,routing_revision:ROUTING_REVISION,ts:now()});
  if(url.pathname==="/strategy") return json({ok:true,strategy:"split-executors-v12-no-pc-failclosed",execution_priority:priorities(),retired_executors:[...RETIRED_EXECUTORS],oracle:false,google_compute:false,routing_revision:ROUTING_REVISION});
  if(["/auth-diag","/probes","/decision","/queue-health"].includes(url.pathname)&&!adminAuth(request,env)){
   const auth=request.headers.get("Authorization")||"",token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():"",v=await verifyGithubOidc(token,env);
   if(!v.ok)return json({ok:false,error:"unauthorized"},401);
  }
  if(url.pathname==="/auth-diag") return json({ok:true,local_executor_retired:true,auth:"oidc_or_control_token"});
  if(url.pathname==="/probes"){const s=await publicState(env);return json({ok:true,ts:now(),probes:s.probes,selected:s.selected});}
  if(url.pathname==="/decision"){const s=await publicState(env);return json({ok:true,ts:now(),selected:s.selected,reasons:s.reasons,routing:s.routing});}
  if(url.pathname==="/queue-health"){const qs=await queueStub(env).stats(localDay());return json({ok:true,backend:"durable-object-sqlite",daily_limit:DAILY_LIMIT,counts:qs.counts,total_confirmed:qs.total_confirmed,remaining:qs.remaining,dedupe:qs.dedupe,jobs:qs.jobs,ts:now()});}
  if(url.pathname==="/queue-self-test"&&(request.method==="POST"||request.method==="GET")){const auth=request.headers.get("Authorization")||"";const token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():"";const v=await verifyGithubOidc(token,env);if(!v.ok)return json({ok:false,error:v.error},401);try{return json(await queueStub(env).selfTest());}catch(e){return json({ok:false,error:String(e&&e.message||e)},500);}}
  if(url.pathname.startsWith("/github-queue/")&&request.method==="POST"){
   const auth=request.headers.get("Authorization")||""; const token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():""; const v=await verifyGithubOidc(token,env); if(!v.ok)return json({ok:false,error:v.error},401);
   const b=await request.json(); b.executor="github"; const q=queueStub(env); let out; const op=url.pathname.slice("/github-queue/".length);
   if(op==="lease"){if(!["tiktok","kwai"].includes(b.platform))return json({ok:false,error:"platform_required"},400);out=await q.lease(b,localDay());}
   else if(op==="renew")out=await q.renew(b);
   else if(op==="started")out=await q.started(b);
   else if(op==="complete")out=await q.complete(b,localDay());
   else if(op==="fail")out=await q.fail(b);
   else return json({ok:false,error:"not_found"},404);
   return json(out,out.status||200);
  }
  if(url.pathname==="/github-queue-get/lease"&&request.method==="GET"){
   const auth=request.headers.get("Authorization")||""; const token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():""; const v=await verifyGithubOidc(token,env); if(!v.ok)return json({ok:false,error:v.error},401);
   const platform=url.searchParams.get("platform")||"tiktok"; const ttl=Number(url.searchParams.get("ttl_seconds")||"600"); return json(await queueStub(env).lease({executor:"github",platform,ttl_seconds:ttl},localDay()));
  }
  if(url.pathname==="/heartbeat/github-oidc"&&request.method==="POST"){
   const b=await request.json();
   const auth=request.headers.get("Authorization")||"";
   const token=auth.toLowerCase().startsWith("bearer ")?auth.slice(7).trim():"";
   const v=await verifyGithubOidc(token,env);
   if(!v.ok)return json({ok:false,error:v.error},401);
   const q=queueStub(env),prev=await q.getExecutor("github")||{},requestedReady=b.ready_for_tiktok===true,requestedUntil=requestedReady?String(b.tiktok_ready_until||""):null,validRequested=requestedReady&&requestedUntil&&Date.parse(requestedUntil)>Date.now(),until=validRequested?requestedUntil:(prev.tiktok_ready_until||null),stillReady=validRequested||(!!until&&Date.parse(until)>Date.now());
   const row={...prev,executor:"github",healthy:true,failures:Number(prev.failures||0),heartbeat_at:now(),disabled_until:prev.disabled_until&&Date.parse(prev.disabled_until)>Date.now()?prev.disabled_until:null,host:"github-actions",platform:"github",workflow:v.claims.workflow,repository:v.claims.repository,ref:v.claims.ref,capabilities:["cuts","tiktok","control"],daily_limit:100,published_today:Number(prev.published_today||0),ready_for_tiktok:stillReady,tiktok_ready_until:stillReady?until:null};
   await q.setExecutor(row);
   if(b.queue_op){let out;if(b.queue_op==="lease")out=await q.lease({...b,executor:"github"},localDay());else if(b.queue_op==="renew")out=await q.renew({...b,executor:"github"});else if(b.queue_op==="started")out=await q.started({...b,executor:"github"});else if(b.queue_op==="complete")out=await q.complete({...b,executor:"github"},localDay());else if(b.queue_op==="fail")out=await q.fail({...b,executor:"github"});else return json({ok:false,error:"queue_op_invalid"},400);return json({ok:true,state:row,queue:out});}
   return json({ok:true,state:row});
  }
  if(url.pathname==="/heartbeat"&&request.method==="POST"){
   const b=await request.json(); if(!b.executor)return json({ok:false,error:"executor_required"},400); if(retiredExecutor(b.executor))return json({ok:false,error:"retired_executor"},410); if(!(await executorAuth(request,env,b)))return json({ok:false,error:"unauthorized"},401);
   const q=queueStub(env),prev=await q.getExecutor(b.executor)||{},failures=Number(b.failures??prev.failures??0),row={...prev,...b,executor:b.executor,heartbeat_at:now(),failures};
   if(failures>=3)row.disabled_until=new Date(Date.now()+15*60*1000).toISOString(); else if(b.healthy===true && Number(row.consecutive_failures||0)===0)row.disabled_until=null;
   await q.setExecutor(row);return json({ok:true,state:row});
  }
  if(url.pathname.startsWith("/job/")&&request.method==="POST"&&url.pathname!=="/job/enqueue"&&url.pathname!=="/job/enqueue-local"){
   const rawBody=await request.text(); let b; try{b=JSON.parse(rawBody);}catch{return json({ok:false,error:"invalid_json"},400);} let authOk=await executorAuth(request,env,b,rawBody); if(!authOk&&String(b.executor)==="github"){const bearer=request.headers.get("Authorization")||"";const token=bearer.toLowerCase().startsWith("bearer ")?bearer.slice(7).trim():"";if(token){const v=await verifyGithubOidc(token,env);authOk=v.ok;}} if(!authOk)return json({ok:false,error:"unauthorized"},401); if(retiredExecutor(b.executor))return json({ok:false,error:"retired_executor"},410); const q=queueStub(env); let out;
   if(url.pathname==="/job/lease"){if(!["tiktok","kwai"].includes(b.platform))return json({ok:false,error:"platform_required"},400);out=await q.lease(b,localDay());}
   else if(url.pathname==="/job/renew")out=await q.renew(b);
   else if(url.pathname==="/job/started")out=await q.started(b);
   else if(url.pathname==="/job/complete")out=await q.complete(b,localDay());
   else if(url.pathname==="/job/fail")out=await q.fail(b);
   else if(url.pathname==="/job/reconcile")out=await q.reconcile(b,localDay());
   else return json({ok:false,error:"not_found"},404);
   return json(out,out.status||200);
  }
  if(url.pathname==="/job/enqueue-local") return json({ok:false,error:"local_executor_retired"},410);
  if(url.pathname==="/job/enqueue"&&request.method==="POST"){const rawBody=await request.text();let b;try{b=JSON.parse(rawBody);}catch{return json({ok:false,error:"invalid_json"},400);}let ok=adminAuth(request,env);if(!ok&&String(b.executor)==="github"){const bearer=request.headers.get("Authorization")||"";const token=bearer.toLowerCase().startsWith("bearer ")?bearer.slice(7).trim():"";if(token){const v=await verifyGithubOidc(token,env);ok=v.ok;}}if(!ok)return json({ok:false,error:"unauthorized"},401);if(retiredExecutor(b.executor))return json({ok:false,error:"retired_executor"},410);if(!b.id||!["tiktok","kwai"].includes(b.platform))return json({ok:false,error:"id_and_platform_required"},400);return json(await queueStub(env).enqueue(b));}
  if(!adminAuth(request,env))return json({ok:false,error:"unauthorized"},401);
  if(url.pathname==="/status"){const s=await publicState(env),qs=await queueStub(env).stats(localDay());return json({ok:true,ts:now(),executors:s.executors,counts:qs.counts,remaining:qs.remaining,daily_limit:DAILY_LIMIT,selected:s.selected,routing:s.routing,jobs:qs.jobs});}
  return json({ok:false,error:"not_found"},404);
 },
 async scheduled(event,env,ctx){ctx.waitUntil(publicState(env));}
};

