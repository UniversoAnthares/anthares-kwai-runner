// Dedicated TikTok Neon Function, Vercel-independent, generated from canonical fenced queue contract.
// Independent Neon queue for CORTES TikTok, isolated from the Kwai publication ledger.
// Two Github OIDC roles: Anthares Clipper produces, public kwai-runner consumes.
// No static credentials travel between repos, and no unverified upload is retried.
import crypto from 'node:crypto';


const QUEUE_URL='https://anthares-remote-primary.vercel.app/api/cortes-tiktok';
const AUDIENCE=QUEUE_URL;
const CLIPPER='UniversoAnthares/anthares-clipper';
const RUNNER='UniversoAnthares/anthares-kwai-runner';
const SOURCE_WF='anthares-tiktok-owned-youtube.yml';
const CONSUMER_WF='cortes-tiktok-publisher.yml';
const TARGET='tiktok:universo.anthares';
// Neon Functions service: same fenced SQL ledger as Vercel, with no pg socket.
 // For this service each SQL request is a single transaction. The database
 // BEFORE UPDATE trigger enforces the 100/day cap atomically across providers.
const pool={async query(statement,params=[]){
 const conn=process.env.DATABASE_URL;
 if(!conn)throw new Error('DATABASE_CONFIG_MISSING');
 const u=new URL(conn);
 if(!['postgres:','postgresql:'].includes(u.protocol)||!u.hostname.endsWith('.neon.tech'))throw new Error('DATABASE_HOST_INVALID');
 const base='https://api.'+u.hostname.split('.').slice(1).join('.')+'/sql';
 const response=await fetch(base,{
   method:'POST',
   headers:{'Content-Type':'application/json','Neon-Connection-String':conn,'Neon-Raw-Text-Output':'true'},
   body:JSON.stringify({query:statement,params}),
   signal:AbortSignal.timeout(15000)
 });
 if(!response.ok)throw new Error('NEON_SQL_HTTP_'+response.status);
 const result=await response.json();
 if(!Array.isArray(result?.rows))throw new Error('NEON_SQL_RESPONSE_INVALID');
 return {rows:result.rows,rowCount:Number(result.rowCount??result.rows.length)};
}};
let ready=false;
let jwks=null;
let jwksUntil=0;

function reply(res,status,data){res.statusCode=status;res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));}
function fail(msg){throw new Error(msg);}
function clean(v){return String(v||'').trim();}
function validTime(v){const n=Number(v);return Number.isInteger(n)&&n>=0&&n<=86400*120?n:null;}
function digest(v){return crypto.createHash('sha256').update(v).digest('hex');}
function body(req){if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;if(typeof req.body==='string'){try{return JSON.parse(req.body)}catch{}}return{};}
function token(req){const m=/^Bearer\s+(.+)$/i.exec(String(req.headers.authorization||''));return m?m[1]:'';}

async function githubRole(req) {
 const jwt=token(req);
 if(jwt.length<200||jwt.length>16000)return'';
 const fragments=jwt.split('.');
 if(fragments.length!==3)return'';
 let header,claims;
 try{header=JSON.parse(Buffer.from(fragments[0],'base64url').toString('utf8'));claims=JSON.parse(Buffer.from(fragments[1],'base64url').toString('utf8'));}catch{return'';}
 if(header.alg!=='RS256'||!/^[A-Za-z0-9_.-]{1,200}$/.test(header.kid||''))return'';
 const now=Math.floor(Date.now()/1000),aud=Array.isArray(claims.aud)?claims.aud:[claims.aud];
 if(claims.iss!=='https://token.actions.githubusercontent.com'||!aud.includes(AUDIENCE)||claims.ref!=='refs/heads/main')return'';
 if(!Number.isFinite(claims.exp)||claims.exp<=now||!Number.isFinite(claims.iat)||claims.iat>now+60)return'';
 if(claims.nbf!==undefined&&Number(claims.nbf)>now+60)return'';
 if(!['schedule','push','workflow_dispatch','workflow_run'].includes(claims.event_name))return'';
 let role='', wf='';
 if(claims.repository===CLIPPER){role='producer';wf=CLIPPER+'/.github/workflows/'+SOURCE_WF+'@refs/heads/main';}
 if(claims.repository===RUNNER){role='consumer';wf=[CONSUMER_WF,'tiktok-central-session-read.yml','cortes-tiktok-lucasrosalem4-manifest.yml','cortes-tiktok-primary-windows-fallback.yml'].map(name=>RUNNER+'/.github/workflows/'+name+'@refs/heads/main');}
 if(!role||!(Array.isArray(wf)?wf:[wf]).includes(String(claims.job_workflow_ref||claims.workflow_ref||'')))return'';
 try{
   if(!jwks||Date.now()>jwksUntil){
     const cfg=await fetch('https://token.actions.githubusercontent.com/.well-known/openid-configuration',{signal:AbortSignal.timeout(7500)});
     if(!cfg.ok)return'';
     const meta=await cfg.json();
     if(!String(meta.jwks_uri||'').startsWith('https://token.actions.githubusercontent.com/'))return'';
     const keys=await fetch(meta.jwks_uri,{signal:AbortSignal.timeout(7500)});
     if(!keys.ok)return'';
     jwks=await keys.json();jwksUntil=Date.now()+300000;
   }
   const k=(jwks.keys||[]).find(x=>x.kid===header.kid&&x.kty==='RSA'&&(!x.alg||x.alg==='RS256'));
   if(!k)return'';
   const pub=crypto.createPublicKey({key:k,format:'jwk'});
   return crypto.verify('RSA-SHA256',Buffer.from(fragments[0]+'.'+fragments[1]),pub,Buffer.from(fragments[2],'base64url'))?role:'';
 }catch{return'';}
}

const FORGEJO_ISSUER='https://codeberg.org/api/actions';
const FORGEJO_KEYS='https://codeberg.org/api/actions/.well-known/keys';
const FORGEJO_WORKFLOW=RUNNER+'/.forgejo/workflows/tiktok-codeberg-primary.yml@refs/heads/main';
let forgejoKeys=null,forgejoKeysUntil=0;

async function codebergRole(req) {
  const jwt=token(req);
  if(jwt.length<200||jwt.length>16000)return '';
  const parts=jwt.split('.');
  if(parts.length!==3)return '';
  let header,claims;
  try {
    header=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
    claims=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
  } catch {return '';}
  if(header.alg!=='RS256'||!/^[A-Za-z0-9_.-]{1,200}$/.test(header.kid||''))return '';
  const now=Math.floor(Date.now()/1000);
  const audiences=Array.isArray(claims.aud)?claims.aud:[claims.aud];
  const subjects=[
    'repo:'+RUNNER+':ref:refs/heads/main',
    'repo:UniversoAnthares-1543245/anthares-kwai-runner-2708613:ref:refs/heads/main'
  ];
  if(claims.iss!==FORGEJO_ISSUER||!audiences.includes(AUDIENCE)||
     claims.repository!==RUNNER||Number(claims.repository_id)!==2708613||
     claims.ref!=='refs/heads/main'||claims.workflow_ref!==FORGEJO_WORKFLOW||
     !subjects.includes(claims.sub)||
     !['schedule','workflow_dispatch'].includes(claims.event_name)||
     !Number.isFinite(claims.exp)||claims.exp<=now||
     !Number.isFinite(claims.iat)||claims.iat>now+60||now-claims.iat>3600||
     (claims.nbf!==undefined&&Number(claims.nbf)>now+60))return '';
  try {
    if(!forgejoKeys||Date.now()>forgejoKeysUntil){
      const cfg=await fetch(FORGEJO_ISSUER+'/.well-known/openid-configuration',{signal:AbortSignal.timeout(7500)});
      if(!cfg.ok)return '';
      const meta=await cfg.json();
      if(meta.issuer!==FORGEJO_ISSUER||meta.jwks_uri!==FORGEJO_KEYS)return '';
      const response=await fetch(FORGEJO_KEYS,{signal:AbortSignal.timeout(7500)});
      if(!response.ok)return '';
      forgejoKeys=await response.json();
      forgejoKeysUntil=Date.now()+300000;
    }
    const jwk=(forgejoKeys.keys||[]).find(x=>x.kid===header.kid&&x.kty==='RSA'&&(!x.alg||x.alg==='RS256'));
    if(!jwk)return '';
    const key=crypto.createPublicKey({key:jwk,format:'jwk'});
    return crypto.verify('RSA-SHA256',Buffer.from(parts[0]+'.'+parts[1]),key,
                         Buffer.from(parts[2],'base64url'))?'consumer':'';
  } catch {return '';}
}

async function schema(){
 if(ready)return;
 await pool.query(
 'CREATE TABLE IF NOT EXISTS cortes_tiktok_publications ('+
 'id text PRIMARY KEY, source_id text NOT NULL, segment_id text NOT NULL UNIQUE,'+
 'source_start integer NOT NULL, source_end integer NOT NULL, media_url text NOT NULL,'+
 'duration_seconds real NOT NULL, title text NOT NULL, callback_url text NOT NULL,'+
 'callback_token text NOT NULL, attachment_id bigint NOT NULL,'+
 'status text NOT NULL DEFAULT \'queued\', lease_generation integer NOT NULL DEFAULT 0,'+
 'lease_until timestamptz, publication_started_at timestamptz, remote_id text,'+
 'confirmed_at timestamptz, last_error text, created_at timestamptz NOT NULL DEFAULT now(),'+
 'updated_at timestamptz NOT NULL DEFAULT now(),'+
 'CONSTRAINT cortes_tiktok_source_bounds CHECK(source_end>source_start),'+
 'CONSTRAINT cortes_tiktok_state CHECK(status IN (\'queued\',\'leased\',\'started\',\'uncertain\',\'confirmed\'))'+
 ')');
 await pool.query('CREATE INDEX IF NOT EXISTS cortes_tiktok_queue_ix ON cortes_tiktok_publications(status,created_at)');
 // Idempotent additive migration: failed media preflight must never monopolize the queue.
 await pool.query('ALTER TABLE cortes_tiktok_publications ADD COLUMN IF NOT EXISTS preflight_failures integer NOT NULL DEFAULT 0');
 await pool.query('ALTER TABLE cortes_tiktok_publications ADD COLUMN IF NOT EXISTS retry_not_before timestamptz');
 ready=true;
}

function allowedMedia(raw){
 try{const u=new URL(raw);return u.protocol==='https:'&&['anthares.us','www.anthares.us'].includes(u.hostname)&&u.username===''&&u.password==='';}catch{return false;}
}
function parseSourceSegment(sid,source){
 const rx=/^g[0-9]+:([A-Za-z0-9_-]{6,60}):([0-9]+):([0-9]+)$/;
 const m=rx.exec(sid);
 if(!m||m[1]!==source)return null;
 const start=validTime(m[2]),end=validTime(m[3]);
 return start!==null&&end!==null&&end>start?{start,end}:null;
}
function normalizeEnqueue(b){
 const source=clean(b.source_id),sid=clean(b.segment_id),limits=parseSourceSegment(sid,source);
 const dur=Number(b.duration_seconds),callback=clean(b.callback_url),secret=clean(b.callback_token);
 const attachment=Number(b.attachment_id),media=clean(b.media_url),title=clean(b.title);
 if(!limits||!Number.isFinite(dur)||dur<30||dur>90)fail('invalid_segment');
 if(!allowedMedia(media))fail('invalid_media_origin');
 if(callback!=='https://anthares.us/wp-json/anthares/v1/cortes/clip-network-callback')fail('invalid_callback_origin');
 if(secret.length<32||secret.length>180||!/^[A-Za-z0-9]+$/.test(secret))fail('invalid_callback_proof');
 if(!Number.isSafeInteger(attachment)||attachment<1)fail('invalid_attachment');
 if(title.length<8||title.length>260)fail('invalid_title');
 const id='tt-'+digest(source+'|'+sid).slice(0,32);
 return{id,source,sid,start:limits.start,end:limits.end,media,dur,title,callback,secret,attachment};
}
async function enqueue(b){
 const x=normalizeEnqueue(b);
 await schema();
 const q=await pool.query('INSERT INTO cortes_tiktok_publications'+
 '(id,source_id,segment_id,source_start,source_end,media_url,duration_seconds,title,callback_url,callback_token,attachment_id)'+
 ' VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) ON CONFLICT(segment_id) DO NOTHING RETURNING id',
 [x.id,x.source,x.sid,x.start,x.end,x.media,x.dur,x.title,x.callback,x.secret,x.attachment]);
 // Retitle only safely queued jobs. Started, uncertain and confirmed media
 // retain their immutable publication metadata and fencing.
 const retitle=await pool.query(
  'UPDATE cortes_tiktok_publications SET title=$2,updated_at=now() WHERE segment_id=$1 AND status=\'queued\' AND title IS DISTINCT FROM $2 RETURNING id',
  [x.sid,x.title]);
 const status=await pool.query('SELECT id,status,remote_id FROM cortes_tiktok_publications WHERE segment_id=$1',[x.sid]);
 return{ok:true,created:q.rowCount===1,updated_title:retitle.rowCount===1,job:status.rows[0]||null};
}
async function reaper(){
 await schema();
 await pool.query('UPDATE cortes_tiktok_publications SET status=\'queued\',lease_until=NULL,updated_at=now() WHERE status=\'leased\' AND lease_until<now() AND publication_started_at IS NULL');
 await pool.query('UPDATE cortes_tiktok_publications SET status=\'uncertain\',lease_until=NULL,updated_at=now() WHERE status IN (\'leased\',\'started\') AND lease_until<now() AND publication_started_at IS NOT NULL');
}
async function getNext(){
 await reaper();
 const concurrent=await pool.query('SELECT id FROM cortes_tiktok_publications WHERE status=\'leased\' AND lease_until>now() LIMIT 1');
 if(concurrent.rowCount)return{ok:true,job:null,mode:'busy'};

 // Keep an uncertain upload isolated for reconciliation without starving safe queued clips.
 const uncertain=await pool.query('SELECT * FROM cortes_tiktok_publications WHERE status IN (\'uncertain\',\'started\') ORDER BY created_at LIMIT 1');
 const cadence=await pool.query("SELECT COUNT(*) FILTER (WHERE publication_started_at IS NOT NULL AND (publication_started_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date)::int AS daily, MAX(publication_started_at) AS last_post, COUNT(*) FILTER (WHERE status='queued')::int AS pending FROM cortes_tiktok_publications");
 const daily=Number(cadence.rows[0]?.daily||0);
 const pending=Number(cadence.rows[0]?.pending||0);
 const last=cadence.rows[0]?.last_post;
 // Same-day catch-up: three-minute verified minimum, four-minute preferred.
 // Never overlap leases, exceed 100 publication starts/day or fabricate confirmation.
 const boundary=await pool.query("SELECT ((now() AT TIME ZONE 'America/Campo_Grande')::date + time '23:45:00') AT TIME ZONE 'America/Campo_Grande' AS deadline_utc");
 const remaining=Math.max(0,new Date(boundary.rows[0].deadline_utc).getTime()-Date.now());
 const dueSeconds=Math.floor(Math.max(0,remaining-120000)/Math.max(1,pending)/1000);
 const paceSeconds=Math.max(180,Math.min(240,dueSeconds));
 if(pending>0&&remaining<pending*180000)console.warn('CORTES_SAME_DAY_CAPACITY_RISK platform=tiktok pending='+pending+' window_seconds='+Math.floor(remaining/1000));
 const paced=Boolean(last&&Date.now()-new Date(last).getTime()<paceSeconds*1000);

 // Preserve the 100/day cap and adaptive same-day safe cadence. An ambiguous earlier upload
 // never returns to the publish state; the 29 confirmed-safe queued clips can proceed.
 if(daily<100&&!paced){
  const q=await pool.query(
   'WITH gate AS (SELECT pg_try_advisory_xact_lock(19283746501001::bigint) AS ok), candidate AS (SELECT id FROM cortes_tiktok_publications WHERE status=\'queued\' AND (retry_not_before IS NULL OR retry_not_before<=now()) '+
   'AND (SELECT ok FROM gate) AND NOT EXISTS(SELECT 1 FROM cortes_tiktok_publications WHERE status=\'leased\' AND lease_until>now()) '+
   'ORDER BY CASE WHEN source_id=(SELECT source_id FROM cortes_tiktok_publications WHERE status=\'queued\' ORDER BY created_at DESC,id DESC LIMIT 1) THEN 0 ELSE 1 END,created_at,id '+
   'FOR UPDATE SKIP LOCKED LIMIT 1)'+
   ' UPDATE cortes_tiktok_publications p SET status=\'leased\',lease_generation=p.lease_generation+1,'+
   'lease_until=now()+interval \'8 minutes\',updated_at=now() FROM candidate WHERE p.id=candidate.id RETURNING p.*');
  if(q.rowCount)return{ok:true,job:q.rows[0],mode:'publish'};
 }
 if(uncertain.rowCount)return{ok:true,job:uncertain.rows[0],mode:'reconcile'};
 if(daily>=100)return{ok:true,job:null,mode:'cap'};
 if(paced)return{ok:true,job:null,mode:'paced'};
 return{ok:true,job:null,mode:'idle'};
}
async function start(b){
 await schema();
 const id=clean(b.id),gen=Number(b.lease_generation);
 if(!id||!Number.isSafeInteger(gen)||gen<1)return {ok:false,error:'invalid_fence'};
 // One fenced SQL operation. A production PostgreSQL trigger reserves the
 // daily slot atomically before changing status, including across Vercel.
 const r=await pool.query(
  "UPDATE cortes_tiktok_publications SET status='started',publication_started_at=now(),updated_at=now() WHERE id=$1 AND status='leased' AND lease_generation=$2 AND lease_until>now() AND publication_started_at IS NULL RETURNING id,status,lease_generation",
  [id,gen]);
 return r.rowCount?{ok:true,job:r.rows[0]}:{ok:false,error:'stale_fence'};
}
async function finish(b){
 await schema();
 const id=clean(b.id),gen=Number(b.lease_generation),remote=clean(b.remote_id);
 if(!/^[0-9]{12,25}$/.test(remote))return{ok:false,error:'invalid_tiktok_remote_id'};
 const r=await pool.query('UPDATE cortes_tiktok_publications SET status=\'confirmed\',remote_id=$3,'+
 'confirmed_at=now(),lease_until=NULL,updated_at=now()'+
 ' WHERE id=$1 AND lease_generation=$2 AND status IN (\'started\',\'uncertain\') RETURNING id,status,remote_id',[id,gen,remote]);
 return r.rowCount?{ok:true,job:r.rows[0]}:{ok:false,error:'stale_or_already_confirmed'};
}
async function markFail(b){
 await schema();
 const id=clean(b.id),gen=Number(b.lease_generation);
 const reason=clean(b.error).slice(0,100);
 // Only pre-STARTED failure can return to queued. Apply an exponentially
 // bounded cooldown (2,4,8,16,32 minutes) and allow other queued clips through.
 // Once STARTED, remain UNCERTAIN until a remote-profile confirmation exists.
 const r=await pool.query(
 "UPDATE cortes_tiktok_publications SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,"+
 " lease_until=NULL,last_error=$3,updated_at=now(),"+
 " preflight_failures=CASE WHEN publication_started_at IS NULL THEN LEAST(preflight_failures+1,5) ELSE preflight_failures END,"+
 " retry_not_before=CASE WHEN publication_started_at IS NULL THEN now()+(LEAST(32,POWER(2,LEAST(preflight_failures+1,5)))::int * interval '1 minute') ELSE retry_not_before END"+
 " WHERE id=$1 AND lease_generation=$2 AND status IN ('leased','started') RETURNING id,status,preflight_failures,retry_not_before",
 [id,gen,reason]);
 return r.rowCount?{ok:true,job:r.rows[0]}:{ok:false,error:'stale_fence'};
}

async function handler(req,res){
 try{
  const u=new URL(req.url,'https://local.invalid'),action=u.searchParams.get('action')||'';
  if(req.method==='GET'&&action==='health'){
    await schema();
    const check=await pool.query('SELECT count(*)::int AS total FROM public.cortes_tiktok_publications');
    if(!check.rows.length || !Number.isInteger(Number(check.rows[0].total)))
      return reply(res,503,{ok:false,error:'neon_ledger_count_unverified'});
    return reply(res,200,{ok:true,service:'cortes-tiktok-neon',
      isolation:'separate_from_kwai',fencing:true,
      db_ledger_total:Number(check.rows[0].total)});
  }
  const role=(await githubRole(req))||(await codebergRole(req));
  if(!role)return reply(res,401,{ok:false,error:'unauthorized_oidc'});
  const b=body(req);
  if(req.method==='POST'&&action==='enqueue'&&role==='producer')return reply(res,200,await enqueue(b));
  if(req.method==='GET'&&action==='source-manifest'&&role==='consumer'){
   await schema();
   const rows=await pool.query(
    "SELECT segment_id,source_id,media_url,title,duration_seconds FROM cortes_tiktok_publications "+
    "WHERE status='confirmed' AND confirmed_at IS NOT NULL "+
    "AND (confirmed_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date "+
    "ORDER BY confirmed_at ASC,id ASC LIMIT 100");
   const day=await pool.query("SELECT to_char(now() AT TIME ZONE 'America/Campo_Grande','YYYY-MM-DD') AS local_day");
   return reply(res,200,{ok:true,account:'lucasrosalem4',date:day.rows[0].local_day,clip_count:rows.rows.length,clips:rows.rows});
  }
  if(req.method==='GET'&&action==='status'){
   await schema();
   const q=await pool.query('SELECT status,count(*)::int AS count FROM cortes_tiktok_publications GROUP BY status');
   const daily=await pool.query("SELECT count(*) FILTER(WHERE publication_started_at IS NOT NULL AND (publication_started_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date)::int AS started_today,count(*) FILTER(WHERE confirmed_at IS NOT NULL AND (confirmed_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date)::int AS confirmed_today FROM cortes_tiktok_publications");
   const counts=daily.rows[0];
   return reply(res,200,{ok:true,count:Object.fromEntries(q.rows.map(x=>[x.status,Number(x.count)])),daily:{started_today:counts.started_today,confirmed_today:counts.confirmed_today,remaining_today:Math.max(0,100-counts.started_today)}});
  }
  if(role==='consumer'){
   let result;
   if(req.method==='POST'&&action==='claim')result=await getNext();
   else if(req.method==='POST'&&action==='start')result=await start(b);
   else if(req.method==='POST'&&action==='confirm')result=await finish(b);
   else if(req.method==='POST'&&action==='fail')result=await markFail(b);
   else return reply(res,404,{ok:false,error:'not_found'});
   return reply(res,result.ok?200:409,result);
  }
  return reply(res,403,{ok:false,error:'role_forbidden'});
 }catch(e){console.error('cortes-tiktok',String(e?.message||e).slice(0,120));return reply(res,500,{ok:false,error:'queue_internal_failure'});}
}

function standardResponse(status,payload){
 return Response.json(payload,{status,headers:{'Cache-Control':'no-store'}});
}
export default {async fetch(request){
 const u=new URL(request.url);
 const ct=(request.headers.get('content-type')||'').toLowerCase();
 const size=Number(request.headers.get('content-length')||0);
 if(size>131072)return standardResponse(413,{ok:false,error:'body_too_large'});
 if(request.method==='POST'&&!ct.includes('application/json'))return standardResponse(415,{ok:false,error:'json_required'});
 let requestBody={};
 if(request.method==='POST'){
   const raw=await request.text();
   if(raw.length>131072)return standardResponse(413,{ok:false,error:'body_too_large'});
   try{requestBody=JSON.parse(raw);}catch{return standardResponse(400,{ok:false,error:'invalid_json'});}
   if(!requestBody||typeof requestBody!=='object'||Array.isArray(requestBody))
     return standardResponse(400,{ok:false,error:'invalid_json_object'});
 }
 const headers={};
 let out='',status=200;
 const response={
   set statusCode(code){status=code;},
   setHeader(name,value){headers[String(name).toLowerCase()]=String(value);},
   end(value){out=String(value||'');}
 };
 await handler({url:u.pathname+u.search,method:request.method,
   headers:{authorization:request.headers.get('authorization')||''},body:requestBody},response);
 let body;
 try{body=JSON.parse(out);}catch{return standardResponse(502,{ok:false,error:'backend_response_invalid'});}
 return Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Anthares-TikTok-Control':'neon-independent'}});
}};
