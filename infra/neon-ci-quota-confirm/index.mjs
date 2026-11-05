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
    claims.ref!=='refs/heads/main'||claims.event_name!=='workflow_dispatch'||
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

export default {async fetch(request){
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
}};
