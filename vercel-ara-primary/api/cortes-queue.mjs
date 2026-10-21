import crypto from 'node:crypto';
import { Pool } from 'pg';

const DEVICE_HASH_BASE='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices';
const pool=new Pool({connectionString:process.env.DATABASE_URL,max:4,ssl:{rejectUnauthorized:false}});
const hashCache=new Map();
let schemaReady=false;

function reply(res,status,body){res.statusCode=status;res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');res.end(JSON.stringify(body));}
function bearer(req){const m=/^Bearer\s+(.+)$/i.exec(req.headers.authorization||'');return m?m[1]:'';}
function safeEq(a,b){const aa=Buffer.from(String(a));const bb=Buffer.from(String(b));return aa.length===bb.length&&crypto.timingSafeEqual(aa,bb);}
function sha256hex(v){return crypto.createHash('sha256').update(String(v)).digest('hex');}
function jsonBody(req){if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;if(typeof req.body==='string'){try{return JSON.parse(req.body)}catch{return {}}}return {};}
function validHex64(v){return /^[0-9a-f]{64}$/i.test(String(v||''));}
function int(v,name){const n=Number(v);if(!Number.isInteger(n)||n<0)throw new Error(`invalid_${name}`);return n;}

async function expectedDeviceHash(device){const c=hashCache.get(device);if(c&&Date.now()-c.at<60000)return c.hash;const r=await fetch(`${DEVICE_HASH_BASE}/${encodeURIComponent(device)}.sha256`,{headers:{'User-Agent':'AntharesCortesQueue/1.0','cache-control':'no-cache'}});if(!r.ok)return '';const h=(await r.text()).trim().toLowerCase();if(!validHex64(h))return '';hashCache.set(device,{hash:h,at:Date.now()});return h;}
async function deviceAuth(req){const device=String(req.headers['x-anthares-device']||'').trim();if(!/^[A-Za-z0-9_.-]{1,200}$/.test(device))return{ok:false,device:''};const token=bearer(req);if(!token)return{ok:false,device};const expected=await expectedDeviceHash(device);return{ok:!!expected&&safeEq(sha256hex(token),expected),device};}

// OIDC for the CORTES dispatcher. Only the canonical GitHub workflow on main
// can enqueue; executor operations require the independent device credential.
const PRODUCER_AUDIENCE='https://anthares-remote-primary.vercel.app/api/cortes-queue';
const PRODUCER_REPO='UniversoAnthares/anthares-clipper';
const PRODUCER_WORKFLOWS=new Set(['cortes-daily.yml','cortes-full-system-test-once.yml','cortes-neon-short-dispatch.yml','cortes-buffer-fanout-cloud.yml']);
let githubJwks=null,githubJwksUntil=0;
async function githubOidcEnqueueAuth(req,repo=PRODUCER_REPO,workflows=PRODUCER_WORKFLOWS){
 const token=bearer(req);
 if(token.length<60||token.length>16000)return false;
 const parts=token.split('.');
 if(parts.length!==3)return false;
 let header,claims;
 try{
  header=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
  claims=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
 }catch{return false;}
 if(header.alg!=='RS256'||typeof header.kid!=='string'||header.kid.length>200)return false;
 const now=Math.floor(Date.now()/1000);
 if(claims.iss!=='https://token.actions.githubusercontent.com'||claims.repository!==repo||claims.ref!=='refs/heads/main')return false;
 const aud=Array.isArray(claims.aud)?claims.aud:[claims.aud];
 if(!aud.includes(PRODUCER_AUDIENCE)||!Number.isFinite(claims.exp)||claims.exp<=now||!Number.isFinite(claims.iat)||claims.iat>now+60)return false;
 if(claims.nbf!==undefined&&(!Number.isFinite(claims.nbf)||claims.nbf>now+60))return false;
 if(!['schedule','workflow_dispatch','push'].includes(claims.event_name))return false;
 const workflow=String(claims.job_workflow_ref||claims.workflow_ref||'');
 if(![...workflows].some(name=>workflow===repo+'/.github/workflows/'+name+'@refs/heads/main'))return false;
 try{
  if(!githubJwks||Date.now()>=githubJwksUntil){
   const cfgResponse=await fetch('https://token.actions.githubusercontent.com/.well-known/openid-configuration',{signal:AbortSignal.timeout(8000)});
   if(!cfgResponse.ok) return false;
   const cfg=await cfgResponse.json();
   if(typeof cfg.jwks_uri!=='string'||!cfg.jwks_uri.startsWith('https://token.actions.githubusercontent.com/'))return false;
   const jwksResponse=await fetch(cfg.jwks_uri,{signal:AbortSignal.timeout(8000)});
   if(!jwksResponse.ok)return false;
   githubJwks=await jwksResponse.json();
   githubJwksUntil=Date.now()+300000;
  }
  const key=githubJwks.keys?.find(k=>k.kid===header.kid&&k.kty==='RSA'&&(!k.alg||k.alg==='RS256')&&(!k.use||k.use==='sig'));
  if(!key)return false;
  const pub=crypto.createPublicKey({key,format:'jwk'});
  return crypto.verify('RSA-SHA256',Buffer.from(parts[0]+'.'+parts[1]),pub,Buffer.from(parts[2],'base64url'));
 }catch{return false;}
}


function validOidcProducerPayload(body){
 // GitHub OIDC authenticates the exact trusted clipper workflow on main.
 // A strict payload validator prevents this permission from becoming a general
 // queue write endpoint for unrelated accounts or networks.
 if(!body||typeof body!=='object')return false;
 if(body.platform==='kwai'){
  return body.executor==='github'&&body.target_key==='kwai:lucasrosalem'&&String(body.expected_account||'').replace(/^@/,'').toLowerCase()==='lucasrosalem'&&/^https:\/\//.test(body.video_url||'')&&/^https:\/\/[^/]*anthares\.us\/wp-json\/anthares\/v1\/cortes\/clip-network-callback$/.test(body.cortes_callback_url||'')&&!!body.cortes_callback_token;
 }
 const destinations={'instagram':'instagram:universoanthares','pinterest':'pinterest:lucasyahn','linkedin':'linkedin:primary'};
 const platform=String(body.platform||'');
 const expectedTarget=destinations[platform];
 if(!expectedTarget||body.executor!=='social_video'||body.target_key!==expectedTarget||body.duration_class!=='short')return false;
 if(body.account_id!==expectedTarget.split(':')[1]||!Number.isInteger(Number(body.cortes_attachment_id))||Number(body.cortes_attachment_id)<=0)return false;
 const source=String(body.source_id||''),segment=String(body.segment_id||''),media=String(body.media_url||'');
 if(!source||!segment||body.video_url!==media||typeof body.title!=='string'||!body.title.trim())return false;
 if(!(Number(body.duration_seconds)>=30&&Number(body.duration_seconds)<=90))return false;
 let uri;try{uri=new URL(media)}catch{return false;}
 if(uri.protocol!=='https:'||!['anthares.us','www.anthares.us'].includes(uri.hostname)||uri.username||uri.password||uri.port||!uri.pathname.toLowerCase().endsWith('.mp4'))return false;
 const sourceStart=Number(body.source_start),sourceEnd=Number(body.source_end);
 if(!Number.isSafeInteger(sourceStart)||!Number.isSafeInteger(sourceEnd)||sourceStart<0||sourceEnd<=sourceStart)return false;
 const id='cortes-fanout-'+platform+'-'+sha256hex(source+'|'+segment+'|'+expectedTarget).slice(0,32);
 return body.id===id&&body.dedupe_key===id&&body.media_sha256===sha256hex(source+'|'+segment+'|'+media)&&body.master_id===source;
}

const BUFFER_WORKER_REPO='UniversoAnthares/anthares-kwai-runner';
const BUFFER_WORKER_WORKFLOWS=new Set(['cortes-buffer-linkedin-cloud.yml']);
const BUFFER_TARGETS={linkedin:'linkedin:primary',pinterest:'pinterest:lucasyahn',instagram:'instagram:universoanthares'};
async function bufferWorkerAuth(req){
 if(await githubOidcEnqueueAuth(req,BUFFER_WORKER_REPO,BUFFER_WORKER_WORKFLOWS))return 'linkedin';
 if(await githubOidcEnqueueAuth(req,BUFFER_WORKER_REPO,new Set(['cortes-buffer-pinterest-cloud.yml'])))return 'pinterest';
 return await githubOidcEnqueueAuth(req,BUFFER_WORKER_REPO,new Set(['cortes-buffer-instagram-cloud.yml'])) ? 'instagram' : null;
}
async function bufferWorkerAction(action,body,platform){
 const target=BUFFER_TARGETS[platform];
 if(!target)return{ok:false,error:'buffer_platform_not_allowed'};
 if(action==='lease'){
  if(body.target_key!==target)return{ok:false,error:'buffer_wrong_target'};
  // Stay below the Buffer Free ten-pending-post limit. Reconcile first.
  const pending=await pool.query(`SELECT count(*)::int AS n FROM cortes_publications
   WHERE target_key=$1 AND status='uncertain'
   AND confirmation_evidence->>'kind'='buffer_scheduled'`,[target]);
  if(Number(pending.rows[0]?.n||0)>=8)return{ok:true,job:null,buffer_pending_limit:true};
  return lease({target_key:target,owner:String(body.owner||''),lease_seconds:180});
 }
 if(action==='start'||action==='fail'){
  const entry=await pool.query('SELECT target_key FROM cortes_publications WHERE id=$1',[String(body.id||'')]);
  if(entry.rows[0]?.target_key!==target)return{ok:false,error:'buffer_wrong_job_target'};
  return transition(body,action);
 }
 if(action==='scheduled'){
  const id=String(body.id||''),owner=String(body.owner||''),gen=Number(body.lease_generation),
    bufferId=String(body.buffer_post_id||'');
  if(!id||!owner.startsWith('buffer-'+platform+':')||!Number.isInteger(gen)||gen<1||
     !/^[A-Za-z0-9_:-]{1,160}$/.test(bufferId))return{ok:false,error:'invalid_buffer_scheduled_payload'};
  const evidence={kind:'buffer_scheduled',buffer_post_id:bufferId,platform,confirmed_on_network:false};
  const r=await pool.query(`UPDATE cortes_publications SET status='uncertain',
   remote_id=$4,confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now()
   WHERE id=$1 AND status='started' AND lease_owner=$2 AND lease_generation=$3
     AND target_key=$6 RETURNING id,target_key,status,remote_id`,
   [id,owner,gen,bufferId,JSON.stringify(evidence),target]);
  return r.rowCount?{ok:true,job:r.rows[0]}:{ok:false,error:'invalid_buffer_schedule_fence'};
 }
 if(action==='pending'){
  const r=await pool.query(`SELECT id,remote_id,confirmation_evidence FROM cortes_publications
   WHERE target_key=$1 AND status='uncertain'
   AND confirmation_evidence->>'kind'='buffer_scheduled'
   ORDER BY updated_at ASC LIMIT 2`,[target]);
  return{ok:true,jobs:r.rows};
 }
 if(action==='reconcile'){
  const id=String(body.id||''),remote=String(body.remote_id||''),
    link=String(body.external_link||'');
  let u;try{u=new URL(link)}catch{return{ok:false,error:'invalid_network_evidence_url'};}
  const valid=platform==='linkedin'?(['linkedin.com','www.linkedin.com'].includes(u.hostname)&&
    (u.pathname.startsWith('/feed/update/')||u.pathname.startsWith('/posts/')||u.pathname.startsWith('/company/'))):
  platform==='pinterest'?(['pinterest.com','www.pinterest.com'].includes(u.hostname)&&/^\/pin\/[0-9]+\/?$/.test(u.pathname)):
   (['instagram.com','www.instagram.com'].includes(u.hostname)&&/^\/(reel|p)\/[A-Za-z0-9_-]+\/?$/.test(u.pathname));
  if(u.protocol!=='https:'||!valid)return{ok:false,error:'invalid_network_evidence_url'};
  const evidence={kind:'buffer_'+platform+'_sent_verified',buffer_post_id:remote,external_link:link,
    confirmed_on_network:true};
  const r=await pool.query(`UPDATE cortes_publications SET status='confirmed',
    confirmation_evidence=$3::jsonb,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$4 AND status='uncertain' AND remote_id=$2
      AND confirmation_evidence->>'kind'='buffer_scheduled'
    RETURNING id,status,remote_id`,[id,remote,JSON.stringify(evidence),target]);
  return r.rowCount?{ok:true,job:r.rows[0]}:{ok:false,error:'not_scheduled_or_id_mismatch'};
 }
 return{ok:false,error:'unsupported_buffer_action'};
}

async function ensureSchema(){if(schemaReady)return;await pool.query(`
CREATE TABLE IF NOT EXISTS cortes_publications(
 id text PRIMARY KEY,
 dedupe_key text NOT NULL UNIQUE,
 target_key text NOT NULL,
 master_id text NOT NULL,
 media_sha256 text NOT NULL,
 source_id text NOT NULL,
 source_start bigint NOT NULL,
 source_end bigint NOT NULL,
 duration_class text NOT NULL,
 payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 status text NOT NULL DEFAULT 'queued',
 lease_owner text,
 lease_generation integer NOT NULL DEFAULT 0,
 lease_until timestamptz,
 publication_started_at timestamptz,
 confirmation_evidence jsonb,
 remote_id text,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(source_end>source_start),
 CHECK(status IN ('queued','leased','started','uncertain','confirmed','failed'))
);
CREATE INDEX IF NOT EXISTS cortes_publications_pick ON cortes_publications(target_key,status,created_at);
CREATE INDEX IF NOT EXISTS cortes_publications_source ON cortes_publications(source_id,target_key,source_start,source_end);
`);schemaReady=true;}

async function reap(){await ensureSchema();await pool.query(`UPDATE cortes_publications SET status='queued',lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE status='leased' AND publication_started_at IS NULL AND lease_until<=now()`);await pool.query(`UPDATE cortes_publications SET status='uncertain',lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE status IN ('leased','started') AND publication_started_at IS NOT NULL AND lease_until<=now()`);}

async function enqueue(body){await ensureSchema();const id=String(body.id||'').trim(),dedupe=String(body.dedupe_key||'').trim(),target=String(body.target_key||'').trim(),master=String(body.master_id||'').trim(),sha=String(body.media_sha256||'').toLowerCase(),source=String(body.source_id||'').trim(),duration=String(body.duration_class||'').trim();const start=int(body.source_start,'source_start'),end=int(body.source_end,'source_end');if(!id||!dedupe||!target||!master||!source||!validHex64(sha)||end<=start||!['short','long'].includes(duration))throw new Error('invalid_enqueue_payload');const c=await pool.connect();try{await c.query('BEGIN');await c.query(`SELECT pg_advisory_xact_lock(hashtext($1))`,[`${source}\n${target}`]);const exact=await c.query(`SELECT * FROM cortes_publications WHERE dedupe_key=$1 OR id=$2 LIMIT 1`,[dedupe,id]);if(exact.rowCount){await c.query('COMMIT');return{ok:true,deduped:true,reason:'identity',job:exact.rows[0]};}const socialExactOnly=new Set(['instagram:universoanthares','pinterest:lucasyahn','linkedin:primary']);const overlap=socialExactOnly.has(target)?{rowCount:0}:await c.query(`SELECT * FROM cortes_publications WHERE source_id=$1 AND target_key=$2 AND source_start<$4 AND source_end>$3 AND status<>'failed' ORDER BY created_at LIMIT 1`,[source,target,start,end]);if(overlap.rowCount){await c.query('COMMIT');return{ok:true,deduped:true,reason:'timeline_overlap',job:overlap.rows[0]};}const r=await c.query(`INSERT INTO cortes_publications(id,dedupe_key,target_key,master_id,media_sha256,source_id,source_start,source_end,duration_class,payload) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb) RETURNING *`,[id,dedupe,target,master,sha,source,start,end,duration,JSON.stringify(body)]);await c.query('COMMIT');return{ok:true,deduped:false,job:r.rows[0]};}catch(e){await c.query('ROLLBACK');throw e;}finally{c.release();}}

async function lease(body){await reap();const owner=String(body.owner||'').trim(),target=String(body.target_key||'').trim();const seconds=Math.max(15,Math.min(Number(body.lease_seconds||90),3600));if(!owner||!target)throw new Error('missing_owner_or_target');if(target.startsWith('linkedin:')){const c=await pool.connect();try{await c.query('BEGIN');await c.query('SELECT pg_advisory_xact_lock(hashtext($1))',['cortes:linkedin-daily:'+target]);const quota=await c.query(`SELECT count(*)::int AS n FROM cortes_publications WHERE target_key=$1 AND status IN ('confirmed','leased','started','uncertain') AND updated_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')`,[target]);const used=Number(quota.rows[0]?.n||0);if(used>=50){await c.query('COMMIT');return {ok:true,job:null,daily_limit_reached:true,limit:50,count:used};}const r=await c.query(`WITH picked AS (SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued' ORDER BY CASE WHEN source_id=(SELECT source_id FROM cortes_publications WHERE target_key=$1 AND status='queued' ORDER BY created_at DESC,id DESC LIMIT 1) THEN 0 ELSE 1 END,created_at,id FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+($3||' seconds')::interval,updated_at=now() FROM picked WHERE p.id=picked.id RETURNING p.*`,[target,owner,String(seconds)]);await c.query('COMMIT');return {ok:true,job:r.rows[0]||null,limit:50,count:used};}catch(err){await c.query('ROLLBACK');throw err;}finally{c.release();}}const r=await pool.query(`WITH picked AS (SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued' ORDER BY CASE WHEN source_id=(SELECT source_id FROM cortes_publications WHERE target_key=$1 AND status='queued' ORDER BY created_at DESC,id DESC LIMIT 1) THEN 0 ELSE 1 END,created_at,id FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+($3||' seconds')::interval,updated_at=now() FROM picked WHERE p.id=picked.id RETURNING p.*`,[target,owner,String(seconds)]);return{ok:true,job:r.rows[0]||null};}

async function transition(body,kind){await ensureSchema();const id=String(body.id||'').trim(),owner=String(body.owner||'').trim(),generation=Number(body.lease_generation);if(!id||!owner||!Number.isInteger(generation)||generation<1)throw new Error('invalid_fence');if(kind==='start'){const r=await pool.query(`UPDATE cortes_publications SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now() WHERE id=$1 AND status='leased' AND lease_owner=$2 AND lease_generation=$3 AND lease_until>now() RETURNING *`,[id,owner,generation]);if(!r.rowCount)return{ok:false,error:'stale_or_invalid_lease'};return{ok:true,job:r.rows[0]};}if(kind==='confirm'){const evidence=body.confirmation_evidence||null,remote=String(body.remote_id||'').trim();if(!evidence||!remote)return{ok:false,error:'confirmation_evidence_required'};const r=await pool.query(`UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$4::jsonb,remote_id=$5,lease_until=NULL,updated_at=now() WHERE id=$1 AND status='started' AND lease_owner=$2 AND lease_generation=$3 RETURNING *`,[id,owner,generation,JSON.stringify(evidence),remote]);if(!r.rowCount)return{ok:false,error:'stale_or_invalid_fence'};return{ok:true,job:r.rows[0]};}if(kind==='fail'){const r=await pool.query(`UPDATE cortes_publications SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,lease_owner=CASE WHEN publication_started_at IS NULL THEN NULL ELSE lease_owner END,lease_until=NULL,updated_at=now() WHERE id=$1 AND lease_owner=$2 AND lease_generation=$3 AND status IN ('leased','started') RETURNING *`,[id,owner,generation]);if(!r.rowCount)return{ok:false,error:'stale_or_invalid_fence'};return{ok:true,job:r.rows[0]};}throw new Error('invalid_transition');}

async function reconcile(body){await ensureSchema();const id=String(body.id||'').trim(),evidence=body.confirmation_evidence||null,remote=String(body.remote_id||'').trim();if(!id||!evidence||!remote)return{ok:false,error:'reconciliation_evidence_required'};const r=await pool.query(`UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$2::jsonb,remote_id=$3,lease_until=NULL,updated_at=now() WHERE id=$1 AND status='uncertain' RETURNING *`,[id,JSON.stringify(evidence),remote]);if(!r.rowCount)return{ok:false,error:'not_uncertain_or_missing'};return{ok:true,job:r.rows[0]};}

async function getJob(id){await reap();const r=await pool.query(`SELECT * FROM cortes_publications WHERE id=$1`,[id]);return r.rows[0]||null;}
// Authenticated, target-scoped queue statistics for publication pacing.
// Reap first so expired, never-started leases remain eligible for publication.
async function stats(body){
 await reap();
 const target=String(body.target_key||'').trim();
 if(!target)return{ok:false,error:'missing_target_key'};
 const r=await pool.query(`SELECT
  count(*) FILTER (WHERE status='queued')::int AS pending,
  count(*) FILTER (WHERE status='confirmed' AND updated_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande'))::int AS confirmed_today,
  max(updated_at) FILTER (WHERE status='confirmed') AS last_confirmed_at
  FROM cortes_publications WHERE target_key=$1`,[target]);
 return{ok:true,target_key:target,pending:r.rows[0].pending,confirmed_today:r.rows[0].confirmed_today,last_confirmed_at:r.rows[0].last_confirmed_at};
}

async function retention(body){await ensureSchema();const source=String(body.source_id||'').trim(),master=String(body.master_id||'').trim(),targets=Array.isArray(body.planned_targets)?body.planned_targets.map(String):[];if(!source||!master||!targets.length)return{ok:false,error:'missing_source_master_targets'};const r=await pool.query(`SELECT target_key,status FROM cortes_publications WHERE source_id=$1 AND master_id=$2 AND target_key=ANY($3::text[])`,[source,master,targets]);const m=new Map(r.rows.map(x=>[x.target_key,x.status]));const safe=targets.every(t=>m.get(t)==='confirmed');return{ok:true,safe_to_delete:safe,statuses:Object.fromEntries(targets.map(t=>[t,m.get(t)||'missing']))};}

async function selfTestOnce(){
  await ensureSchema();
  const id='diag-cortes-queue-phase4-v1',target='diag:phase4-v1',source='diag-source-phase4-v1',master='diag-master-phase4-v1',owner='diag-owner-phase4-v1',dedupe='diag-dedupe-phase4-v1',sha=crypto.createHash('sha256').update('diag-cortes-queue-phase4-v1').digest('hex');
  const old=await pool.query(`SELECT status,confirmation_evidence FROM cortes_publications WHERE id=$1 LIMIT 1`,[id]);
  if(old.rowCount&&old.rows[0].status==='confirmed'&&old.rows[0].confirmation_evidence?.selftest_result)return old.rows[0].confirmation_evidence.selftest_result;
  const base={id,dedupe_key:dedupe,target_key:target,master_id:master,media_sha256:sha,source_id:source,source_start:1000,source_end:80000,duration_class:'short'};
  const a=await enqueue(base);
  if(a.job?.status==='confirmed'&&a.job?.confirmation_evidence?.selftest_result)return a.job.confirmation_evidence.selftest_result;
  const d=await enqueue(base);
  const o=await enqueue({...base,id:'diag-overlap-cortes-queue-phase4-v1',dedupe_key:'diag-overlap-dedupe-phase4-v1',source_start:70000,source_end:120000});
  const l=await lease({owner,target_key:target,lease_seconds:90});
  if(!l.job)return{ok:false,error:'diagnostic_lease_missing'};
  const stale=await transition({id,owner,lease_generation:l.job.lease_generation+1},'start');
  const st=await transition({id,owner,lease_generation:l.job.lease_generation},'start');
  const noev=await transition({id,owner,lease_generation:l.job.lease_generation},'confirm');
  const result={ok:!a.deduped&&d.deduped&&d.reason==='identity'&&o.deduped&&o.reason==='timeline_overlap'&&l.job.lease_generation===1&&stale.ok===false&&st.ok===true&&noev.ok===false,dedupe:d.reason,timeline_overlap:o.reason,lease_generation:l.job.lease_generation,stale_generation_rejected:stale.ok===false,start_fenced:st.ok===true,complete_without_evidence_rejected:noev.ok===false,backend:'vercel-neon'};
  const c=await transition({id,owner,lease_generation:l.job.lease_generation,confirmation_evidence:{kind:'phase4-selftest',selftest_result:result},remote_id:'diag-remote-phase4-v1'},'confirm');
  const ret=await retention({source_id:source,master_id:master,planned_targets:[target]});
  result.confirmation_recorded=c.ok===true;result.retention_safe_after_confirm=ret.safe_to_delete===true;result.ok=result.ok&&result.confirmation_recorded&&result.retention_safe_after_confirm;
  await pool.query(`UPDATE cortes_publications SET confirmation_evidence=$2::jsonb WHERE id=$1`,[id,JSON.stringify({kind:'phase4-selftest',selftest_result:result})]);
  return result;
}
async function selfTest(device){await ensureSchema();const stamp=crypto.randomBytes(8).toString('hex'),source=`selftest-${stamp}`,target=`kwai:selftest-${stamp}`,sha=crypto.createHash('sha256').update(stamp).digest('hex'),master=`m-${stamp}`,id=`p-${stamp}`,dedupe=`d-${stamp}`,owner=`${device}:selftest`;const base={id,dedupe_key:dedupe,target_key:target,master_id:master,media_sha256:sha,source_id:source,source_start:1000,source_end:80000,duration_class:'short'};const a=await enqueue(base);const d=await enqueue(base);const o=await enqueue({...base,id:`o-${stamp}`,dedupe_key:`od-${stamp}`,source_start:70000,source_end:120000});const l=await lease({owner,target_key:target,lease_seconds:90});const stale=await transition({id,owner,lease_generation:l.job.lease_generation+1},'start');const s=await transition({id,owner,lease_generation:l.job.lease_generation},'start');const noev=await transition({id,owner,lease_generation:l.job.lease_generation},'confirm');const c=await transition({id,owner,lease_generation:l.job.lease_generation,confirmation_evidence:{kind:'selftest'},remote_id:`remote-${stamp}`},'confirm');const ret=await retention({source_id:source,master_id:master,planned_targets:[target]});const ok=!a.deduped&&d.deduped&&d.reason==='identity'&&o.deduped&&o.reason==='timeline_overlap'&&l.job?.lease_generation===1&&stale.ok===false&&s.ok===true&&noev.ok===false&&c.ok===true&&ret.safe_to_delete===true;return{ok,dedupe:d.reason,timeline_overlap:o.reason,lease_generation:l.job?.lease_generation,stale_generation_rejected:stale.ok===false,start_fenced:s.ok===true,complete_without_evidence_rejected:noev.ok===false,confirmation_recorded:c.ok===true,retention_safe_after_confirm:ret.safe_to_delete===true,backend:'vercel-neon'};}

export default async function handler(req,res){try{const url=new URL(req.url,'https://local.invalid');const action=url.searchParams.get('action')||'';if(req.method==='GET'&&action==='health'){await ensureSchema();return reply(res,200,{ok:true,service:'anthares-cortes-queue',backend:'vercel-neon',fencing:true,dedupe:true,reconciliation:true});}if(req.method==='GET'&&action==='self-test-once'){const auth=await deviceAuth(req);if(!auth.ok)return reply(res,401,{ok:false,error:'unauthorized'});return reply(res,200,await selfTestOnce());}if(req.method==='POST'&&action.startsWith('buffer-')){
 const permitted=new Set(['lease','start','fail','scheduled','pending','reconcile']);
 const verb=action.slice('buffer-'.length);
 if(!permitted.has(verb))return reply(res,404,{ok:false,error:'buffer_action_not_found'});
 const platform=await bufferWorkerAuth(req);
 if(!platform)return reply(res,401,{ok:false,error:'unauthorized_buffer_worker'});
 const body=jsonBody(req);
 const out=await bufferWorkerAction(verb,body,platform);
 return reply(res,out.ok?200:409,out);
 }
 const isProducer=req.method==='POST'&&action==='enqueue';const auth=isProducer&&await githubOidcEnqueueAuth(req)?{ok:true,device:'github-oidc-dispatch'}:
isProducer&&await githubOidcEnqueueAuth(req,BUFFER_WORKER_REPO,new Set(['cortes-linkedin-neon-fanout.yml']))?
{ok:true,device:'github-oidc-linkedin-fanout'}:
isProducer&&await githubOidcEnqueueAuth(req,BUFFER_WORKER_REPO,new Set(['cortes-buffer-three-fanout-cloud.yml']))?
{ok:true,device:'github-oidc-buffer-three-fanout'}:await deviceAuth(req);if(!auth.ok)return reply(res,401,{ok:false,error:'unauthorized'});const body=jsonBody(req);let out;if(req.method==='POST'&&action==='enqueue'){if((['github-oidc-dispatch','github-oidc-linkedin-fanout','github-oidc-buffer-three-fanout'].includes(auth.device))&&(!validOidcProducerPayload(body)||(auth.device==='github-oidc-linkedin-fanout'&&body.target_key!=='linkedin:primary')))return reply(res,403,{ok:false,error:'invalid_cortes_producer_payload'});out=await enqueue(body);}else if(req.method==='POST'&&action==='stats')out=await stats(body);else if(req.method==='POST'&&action==='lease')out=await lease(body);else if(req.method==='POST'&&action==='start')out=await transition(body,'start');else if(req.method==='POST'&&action==='confirm')out=await transition(body,'confirm');else if(req.method==='POST'&&action==='fail')out=await transition(body,'fail');else if(req.method==='POST'&&action==='reconcile')out=await reconcile(body);else if(req.method==='POST'&&action==='retention')out=await retention(body);else if(req.method==='POST'&&action==='self-test')out=await selfTest(auth.device);else if(req.method==='GET'&&action==='job')out={ok:true,job:await getJob(String(url.searchParams.get('id')||''))};else return reply(res,404,{ok:false,error:'not_found'});return reply(res,out?.ok===false?409:200,out);}catch(e){console.error(e);return reply(res,500,{ok:false,error:String(e?.message||e)});}}
