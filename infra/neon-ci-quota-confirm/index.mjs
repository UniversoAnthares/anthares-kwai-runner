import crypto from 'node:crypto';

// One-time authenticated reconciliation of an already successful, historical
// GitHub CI rescue. Does not dispatch, publish, cancel or retry any job.
const REPO='UniversoAnthares/anthares-kwai-runner';
const AUD='anthares-ci-quota-controller';
const WORKFLOW=REPO+'/.github/workflows/gitlab-quota-watcher.yml@refs/heads/main';
const ATTEMPT='gitlab:87307248:3005500025';
const SHA='94ba06e628d0b1ba0bdfeabbdfd9a00b86508759';
const RUN='40942048873';
const PROJECT='87307248', PIPELINE='3005500025', COMPONENT='cortes';
const STATUS_URL='https://api.github.com/repos/'+REPO+'/actions/runs/'+RUN;
const JWKS_URL='https://token.actions.githubusercontent.com/.well-known/jwks';

function reply(status,body){return Response.json(body,{status,headers:{
 'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});}
function reject(status,code){return reply(status,{ok:false,code});}

function decodeJwt(token){
 if(typeof token!=='string'||token.length<120||token.length>16000)return null;
 const p=token.split('.');
 if(p.length!==3||p.some(x=>!x||!/^[\w-]+$/.test(x)))return null;
 try {
  const hdr=JSON.parse(Buffer.from(p[0],'base64url').toString('utf8'));
  const claims=JSON.parse(Buffer.from(p[1],'base64url').toString('utf8'));
  return {p,hdr,claims};
 }catch{return null;}
}
async function verifiedIdentity(req){
 const m=/^Bearer\s+(\S+)$/i.exec(req.headers.get('Authorization')||'');
 if(!m)return false;
 const jwt=decodeJwt(m[1]);if(!jwt)return false;
 const {p,hdr,claims}=jwt;
 const now=Math.floor(Date.now()/1000);
 if(hdr.alg!=='RS256'||hdr.typ&&hdr.typ!=='JWT'||typeof hdr.kid!=='string'||
    hdr.kid.length<4||hdr.kid.length>250||
    claims.iss!=='https://token.actions.githubusercontent.com'||
    !(Array.isArray(claims.aud)?claims.aud:[claims.aud]).includes(AUD)||
    claims.repository!==REPO||claims.workflow_ref!==WORKFLOW||
    claims.ref!=='refs/heads/main'||!['workflow_dispatch','schedule','workflow_run'].includes(claims.event_name)||
    !Number.isFinite(claims.iat)||claims.iat>now+30||claims.iat<now-600||
    !Number.isFinite(claims.exp)||claims.exp<=now||claims.exp>now+900||
    (claims.nbf!==undefined&&(!Number.isFinite(claims.nbf)||claims.nbf>now+30)))return false;
 try {
  const r=await fetch(JWKS_URL,{signal:AbortSignal.timeout(7000),
   headers:{'Accept':'application/json'}});
  if(!r.ok)return false;
  const jwks=await r.json();
  const matches=(Array.isArray(jwks.keys)?jwks.keys:[]).filter(k=>
   k.kid===hdr.kid&&k.kty==='RSA'&&(!k.use||k.use==='sig')&&
   (!k.alg||k.alg==='RS256'));
  if(matches.length!==1)return false;
  const pub=crypto.createPublicKey({key:matches[0],format:'jwk'});
  return crypto.verify('RSA-SHA256',Buffer.from(p[0]+'.'+p[1]),pub,
    Buffer.from(p[2],'base64url'));
 }catch{return false;}
}

function database(){
 const conn=process.env.DATABASE_URL;if(!conn)throw Error('NO_DATABASE');
 const u=new URL(conn);
 if(!['postgres:','postgresql:'].includes(u.protocol)||
    !u.hostname.endsWith('.neon.tech'))throw Error('DATABASE_NOT_NEON');
 return {conn,sql:'https://api.'+u.hostname.split('.').slice(1).join('.')+'/sql'};
}
async function query(statement,params=[]){
 const db=database();
 const res=await fetch(db.sql,{method:'POST',headers:{
  'Content-Type':'application/json',
  'Neon-Connection-String':db.conn,
  'Neon-Raw-Text-Output':'true'},
  body:JSON.stringify({query:statement,params}),signal:AbortSignal.timeout(12000)});
 if(!res.ok)throw Error('DATABASE_UNAVAILABLE');
 const j=await res.json();if(!Array.isArray(j?.rows))throw Error('DATABASE_BAD_REPLY');
 return j.rows;
}

async function checkGitHubRun(token){
 if(!/^.{20,4096}$/.test(token))return false;
 try {
  const r=await fetch(STATUS_URL,{headers:{
   'Accept':'application/vnd.github+json','User-Agent':'Anthares-CI-Receipt-Neon/1.0',
   'Authorization':'Bearer '+token},signal:AbortSignal.timeout(9000)});
  if(!r.ok)return false;
  const run=await r.json();
  return run.id===Number(RUN)&&run.repository?.full_name===REPO&&
    run.status==='completed'&&run.conclusion==='success'&&
    run.event==='workflow_dispatch'&&
    String(run.path||'').endsWith('/gitlab-quota-fallback.yml')&&
    String(run.display_title||'').includes('quota-rescue-cortes-glsha-'+SHA);
 }catch{return false;}
}

async function legacyRequest(request){
 const path=new URL(request.url).pathname;
 if(!['/','/api/gitlab-confirm'].includes(path))return reject(404,'NOT_FOUND');
 if(request.method==='GET'){
  if(path!=='/')return reject(405,'METHOD_NOT_ALLOWED');
  try{
   const rows=await query("SELECT state,data->>'successor_run_id' AS successor_run_id FROM public.anthares_ci_quota_attempts WHERE attempt_id=$1",[ATTEMPT]);
   return reply(200,{ok:true,mode:'exact_oidc_receipt_only',state:rows[0]?.state||'MISSING',ready:true});
  }catch{return reject(503,'LEDGER_UNAVAILABLE');}
 }
 if(request.method!=='POST')return reject(405,'METHOD_NOT_ALLOWED');
 if(!(await verifiedIdentity(request)))return reject(401,'OIDC_REQUIRED_OR_INVALID');
 let body;try{body=await request.json();}catch{return reject(400,'INVALID_JSON');}
 if(!body||String(body.project_id)!==PROJECT||String(body.pipeline_id)!==PIPELINE||
    String(body.component)!==COMPONENT||String(body.sha)!==SHA||
    String(body.github_run_id)!==RUN)return reject(403,'TUPLE_NOT_ALLOWLISTED');
 const token=request.headers.get('X-Github-Actions-Token')||'';
 if(!(await checkGitHubRun(token)))return reject(409,'SUCCESS_RECEIPT_UNVERIFIED');
 try {
  const patch={state:'FALLBACK_CONFIRMED',successor_dispatched:true,
   successor_run_id:RUN,successor_conclusion:'success',receipt_confirmed:true};
  const updated=await query(
   "UPDATE public.anthares_ci_quota_attempts SET state='FALLBACK_CONFIRMED', data=data || $5::jsonb, lease_generation=lease_generation+1, updated_at=now() "+
   "WHERE attempt_id=$1 AND state='FALLBACK_SUBMITTED' AND lease_generation=2 AND data->>'sha'=$2 AND data->>'component'=$3 "+
   "AND data->>'pipeline'=$4 AND data->>'dispatch_workflow'='gitlab-quota-fallback.yml' "+
   "AND data->>'remote_terminal'='true' AND data->>'dispatch_accepted'='true' RETURNING attempt_id,lease_generation",
   [ATTEMPT,SHA,COMPONENT,PIPELINE,JSON.stringify(patch)]);
  if(updated.length===1)return reply(200,{ok:true,state:'FALLBACK_CONFIRMED',attempt:ATTEMPT,successor_run_id:RUN});
  const existing=await query("SELECT state,data->>'successor_run_id' AS id FROM public.anthares_ci_quota_attempts WHERE attempt_id=$1",[ATTEMPT]);
  if(existing.length===1&&existing[0].state==='FALLBACK_CONFIRMED'&&existing[0].id===RUN)
   return reply(200,{ok:true,state:'ALREADY_CONFIRMED',attempt:ATTEMPT,successor_run_id:RUN});
  return reject(409,'RESERVATION_NOT_RECONCILABLE');
 }catch{return reject(503,'LEDGER_UNAVAILABLE');}
}

const PROJECTS={'87307248':'cortes','87361774':'clipper','87361776':'wordpress'};
const ACTIVE_EVENTS=new Set(['workflow_dispatch','schedule','workflow_run']);
function getClaims(req){
 const match=/^Bearer\s+(\S+)$/i.exec(req.headers.get('Authorization')||'');
 return match?decodeJwt(match[1])?.claims:null;
}
function identity(body){
 if(!body||typeof body!=='object'||Array.isArray(body))return null;
 const project=String(body.project_id||''),pipeline=String(body.pipeline_id||'');
 const component=String(body.component||''),sha=String(body.sha||'');
 if(PROJECTS[project]!==component||!/^[0-9]{1,20}$/.test(pipeline)||
   !/^[a-f0-9]{40}$/.test(sha))return null;
 return {project,pipeline,component,sha,attempt:'gitlab:'+project+':'+pipeline};
}
async function jsonBody(request){
 const raw=await request.text();
 if(raw.length>16384)throw Error('OVERSIZE');
 return JSON.parse(raw);
}
async function remoteJson(url,token,header){
 const response=await fetch(url,{headers:{
  [header]:token,'Accept':'application/json','User-Agent':'Anthares-Neon-Quota-Control/2'},
  signal:AbortSignal.timeout(8500)});
 if(!response.ok)throw Error('UPSTREAM_UNAVAILABLE');
 return response.json();
}
async function verifyQuotaSource(x,token){
 if(typeof token!=='string'||token.length<12)return false;
 try{
  const url='https://gitlab.com/api/v4/projects/'+x.project+'/pipelines/'+x.pipeline;
  const p=await remoteJson(url,token,'PRIVATE-TOKEN');
  const jobs=await remoteJson(url+'/jobs?per_page=100',token,'PRIVATE-TOKEN');
  if(p.id!==Number(x.pipeline)||p.sha!==x.sha||p.ref!=='main'||
   !['failed','canceled'].includes(p.status)||!Array.isArray(jobs)||
   jobs.length>=100)return false;
  const quota=jobs.some(j=>j.failure_reason==='ci_quota_exceeded'&&
    j.status==='failed'&&!j.started_at);
  const active=jobs.some(j=>['running','pending','created','preparing',
    'waiting_for_resource'].includes(j.status));
  return quota&&!active;
 }catch{return false;}
}
async function verifyRescue(x,runId,token){
 if(!/^[0-9]{1,20}$/.test(String(runId))||typeof token!=='string'||
    token.length<20)return false;
 try{
  const run=await remoteJson('https://api.github.com/repos/'+REPO+
    '/actions/runs/'+runId,token,'Authorization');
  const want=x.component==='cortes'?'gitlab-quota-fallback.yml':
    'private-ci-quota-rescue.yml';
  return run.id===Number(runId)&&run.repository?.full_name===REPO&&
   run.status==='completed'&&run.conclusion==='success'&&
   run.event==='workflow_dispatch'&&
   String(run.path||'').endsWith('/'+want)&&
   String(run.display_title||'').includes(
     'quota-rescue-'+x.component+'-glsha-'+x.sha);
 }catch{return false;}
}
async function generalRequest(request,path){
 if(request.method!=='POST')return reject(405,'METHOD_NOT_ALLOWED');
 if(!(await verifiedIdentity(request)))return reject(401,'OIDC_REQUIRED_OR_INVALID');
 const claims=getClaims(request);
 if(!claims||!ACTIVE_EVENTS.has(claims.event_name))return reject(403,'EVENT_DENIED');
 let body;
 try{body=await jsonBody(request);}catch{return reject(400,'INVALID_JSON');}
 const x=identity(body);if(!x)return reject(400,'EVENT_IDENTITY_INVALID');

 if(path==='/api/gitlab-reserve'){
  const gitlab=request.headers.get('X-Gitlab-Token')||'';
  if(gitlab.length<12)return reject(401,'GITLAB_TOKEN_REQUIRED');
  if(!(await verifyQuotaSource(x,gitlab)))return reject(409,'SOURCE_QUOTA_UNVERIFIED');
  const owner=crypto.randomUUID();
  const record={provider:'gitlab_ci',component:x.component,project:x.project,
    pipeline:x.pipeline,sha:x.sha,state:'FALLBACK_RESERVED',
    remote_terminal:true,successor_dispatched:false};
  try{
   const rows=await query(
    "INSERT INTO public.anthares_ci_quota_attempts "+
    "(attempt_id,owner_token,state,data,lease_until) "+
    "VALUES($1,$2::uuid,'FALLBACK_RESERVED',$3::jsonb,now()+interval '90 seconds') "+
    "ON CONFLICT (attempt_id) DO NOTHING RETURNING attempt_id",
    [x.attempt,owner,JSON.stringify(record)]);
   return rows.length===1?reply(200,{ok:true,state:'FALLBACK_RESERVED',
     attempt:x.attempt,may_dispatch_one_successor:true}):
     reject(409,'ALREADY_RESERVED');
  }catch{return reject(503,'LEDGER_UNAVAILABLE');}
 }

 if(path==='/api/gitlab-ack'){
  const watcher=String(body.watcher_run_id||'');
  if(!/^[0-9]{1,20}$/.test(watcher)||
    watcher!==String(claims.run_id||''))return reject(403,'WATCHER_RUN_UNVERIFIED');
  const destination=x.component==='cortes'?'gitlab-quota-fallback.yml':
    'private-ci-quota-rescue.yml';
  const patch={state:'FALLBACK_SUBMITTED',successor_dispatched:true,
    dispatch_accepted:true,dispatch_http_status:204,
    dispatch_watcher_run_id:watcher,dispatch_workflow:destination};
  try{
   const rows=await query(
    "UPDATE public.anthares_ci_quota_attempts "+
    "SET state='FALLBACK_SUBMITTED',data=data || $5::jsonb, "+
    "lease_generation=lease_generation+1,updated_at=now() "+
    "WHERE attempt_id=$1 AND state='FALLBACK_RESERVED' "+
    "AND data->>'sha'=$2 AND data->>'component'=$3 AND "+
    "data->>'pipeline'=$4 AND lease_until>now() "+
    "RETURNING attempt_id,lease_generation",
    [x.attempt,x.sha,x.component,x.pipeline,JSON.stringify(patch)]);
   return rows.length===1?reply(200,{ok:true,state:'FALLBACK_SUBMITTED',
      attempt:x.attempt,dispatch_acceptance_recorded:true}):
      reject(409,'RESERVATION_MISSING_OR_USED');
  }catch{return reject(503,'LEDGER_UNAVAILABLE');}
 }

 if(path==='/api/gitlab-confirm'){
  const runId=String(body.github_run_id||'');
  const token=request.headers.get('X-Github-Actions-Token')||'';
  if(!(await verifyRescue(x,runId,token)))
    return reject(409,'SUCCESS_RECEIPT_UNVERIFIED');
  const dest=x.component==='cortes'?'gitlab-quota-fallback.yml':
    'private-ci-quota-rescue.yml';
  const patch={state:'FALLBACK_CONFIRMED',successor_dispatched:true,
    successor_run_id:runId,successor_conclusion:'success',receipt_confirmed:true};
  try{
   const rows=await query(
    "UPDATE public.anthares_ci_quota_attempts "+
    "SET state='FALLBACK_CONFIRMED',data=data || $6::jsonb, "+
    "lease_generation=lease_generation+1,updated_at=now() "+
    "WHERE attempt_id=$1 AND state='FALLBACK_SUBMITTED' "+
    "AND data->>'sha'=$2 AND data->>'component'=$3 "+
    "AND data->>'pipeline'=$4 AND data->>'dispatch_workflow'=$5 "+
    "AND data->>'remote_terminal'='true' "+
    "AND data->>'dispatch_accepted'='true' "+
    "RETURNING attempt_id,lease_generation",
    [x.attempt,x.sha,x.component,x.pipeline,dest,JSON.stringify(patch)]);
   if(rows.length===1)return reply(200,{ok:true,state:'FALLBACK_CONFIRMED',
     attempt:x.attempt,successor_run_id:runId});
   const prev=await query(
    "SELECT state,data->>'successor_run_id' AS confirmed_run "+
    "FROM public.anthares_ci_quota_attempts WHERE attempt_id=$1",
    [x.attempt]);
   if(prev.length===1&&prev[0].state==='FALLBACK_CONFIRMED'&&
      prev[0].confirmed_run===runId)
      return reply(200,{ok:true,state:'ALREADY_CONFIRMED',
        attempt:x.attempt,successor_run_id:runId});
   return reject(409,'RESERVATION_NOT_RECONCILABLE');
  }catch{return reject(503,'LEDGER_UNAVAILABLE');}
 }
 return reject(404,'NOT_FOUND');
}
export default {async fetch(request){
 const path=new URL(request.url).pathname;
 if(path==='/'||path==='/api/legacy-exact-confirm')
    return legacyRequest(request);
 if(['/api/gitlab-reserve','/api/gitlab-ack','/api/gitlab-confirm'].includes(path))
    return generalRequest(request,path);
 return reject(404,'NOT_FOUND');
}};
