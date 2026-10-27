import crypto from 'node:crypto';
const TARGET='threads:universoanthares';
const DEVICE='DESKTOP-FTDK0HP';
const ENDPOINT='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/';
const HASH_URL='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices/'+DEVICE+'.sha256';
const REPO='UniversoAnthares/anthares-kwai-runner';
const WORKFLOW='cortes-threads-cloud-handoff.yml';
const ALLOWED_REFS=new Set(['refs/heads/main','refs/heads/fix/threads-cloud-handoff-20261021']);
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store'}});
let deviceHash='',deviceUntil=0,jwks=null,jwksUntil=0;
async function database(sql,params=[]){
 const connection=process.env.DATABASE_URL||'';
 if(!connection)throw Error('NEON_DATABASE_URL_MISSING');
 const c=new URL(connection);
 if(!['postgresql:','postgres:'].includes(c.protocol)||!c.hostname.endsWith('.neon.tech'))throw Error('DATABASE_ORIGIN_FORBIDDEN');
 const response=await fetch('https://api.'+c.hostname.split('.').slice(1).join('.')+'/sql',{
  method:'POST',headers:{'Content-Type':'application/json','Neon-Connection-String':connection,'Neon-Raw-Text-Output':'true'},
  body:JSON.stringify({query:sql,params}),signal:AbortSignal.timeout(18000)});
 if(!response.ok)throw Error('NEON_QUERY_HTTP_'+response.status);
 const result=await response.json();
 if(!Array.isArray(result.rows))throw Error('NEON_QUERY_BAD_RESPONSE');
 return result.rows;
}
const bearer=req=>(/^Bearer\s+(.+)$/i.exec(req.headers.get('authorization')||'')||[])[1]||'';
async function deviceAuth(request){
 if(request.headers.get('x-anthares-device')!==DEVICE)return false;
 const token=bearer(request);
 if(token.length<16||token.length>4096)return false;
 if(!deviceHash||Date.now()>deviceUntil){
  const r=await fetch(HASH_URL,{signal:AbortSignal.timeout(9000),headers:{'User-Agent':'AntharesThreadsCloudHandoff'}});
  if(!r.ok)return false;
  const h=(await r.text()).trim().toLowerCase();
  if(!/^[0-9a-f]{64}$/.test(h))return false;
  deviceHash=h;deviceUntil=Date.now()+60000;
 }
 return crypto.timingSafeEqual(Buffer.from(crypto.createHash('sha256').update(token).digest('hex'),'hex'),Buffer.from(deviceHash,'hex'));
}
async function githubAuth(request,allowPush=false){
 const token=bearer(request),parts=token.split('.');
 if(token.length<60||token.length>16000||parts.length!==3)return null;
 let header,claims;
 try{header=JSON.parse(Buffer.from(parts[0],'base64url'));claims=JSON.parse(Buffer.from(parts[1],'base64url'));}catch{return null}
 const now=Math.floor(Date.now()/1000);
 if(header.alg!=='RS256'||typeof header.kid!=='string'||header.kid.length>200||
    claims.iss!=='https://token.actions.githubusercontent.com'||
    claims.repository!==REPO||!ALLOWED_REFS.has(claims.ref)||!(['workflow_dispatch','schedule'].includes(claims.event_name)||(allowPush&&claims.event_name==='push'))||
    claims.exp<=now||claims.iat>now+60||claims.nbf>now+60)return null;
 const reference=REPO+'/.github/workflows/'+WORKFLOW+'@'+claims.ref;
 if((claims.job_workflow_ref||claims.workflow_ref)!==reference)return null;
 const audiences=Array.isArray(claims.aud)?claims.aud:[claims.aud];
 if(!audiences.includes(ENDPOINT))return null;
 try{
  if(Date.now()>jwksUntil||!jwks){
   const cfg=await fetch('https://token.actions.githubusercontent.com/.well-known/openid-configuration',{signal:AbortSignal.timeout(8000)});
   if(!cfg.ok)return null;
   const j=await cfg.json();if(!j.jwks_uri?.startsWith('https://token.actions.githubusercontent.com/'))return null;
   const response=await fetch(j.jwks_uri,{signal:AbortSignal.timeout(8000)});
   if(!response.ok)return null;
   jwks=await response.json();jwksUntil=Date.now()+300000;
  }
  const key=jwks.keys?.find(k=>k.kid===header.kid&&k.kty==='RSA'&&(!k.use||k.use==='sig'));
  if(!key)return null;
  const valid=crypto.verify('RSA-SHA256',Buffer.from(parts[0]+'.'+parts[1]),crypto.createPublicKey({key,format:'jwk'}),Buffer.from(parts[2],'base64url'));
  return valid?claims:null;
 }catch{return null}
}
const idValid=id=>/^threads:[A-Za-z0-9_-]{11}\|g[0-9]+:[A-Za-z0-9_-]{11}:[0-9]+:[0-9]+$/.test(id);
const goodUrl=u=>{
 try{const p=new URL(u);return p.protocol==='https:'&&['threads.com','www.threads.com'].includes(p.hostname)&&/^\/@universoanthares\/post\/[A-Za-z0-9_-]+\/?$/.test(p.pathname)&&!p.search&&!p.hash&&!p.username&&!p.password}catch{return false}
};
async function control(){
 const rows=await database("SELECT owner,epoch,lease_until,local_paused_at,local_pause_until,remote_confirmed_url,cloud_primary_enabled,cloud_heartbeat_at,cloud_last_success_at FROM cortes_threads_executor_handoff WHERE target_key=$1",[TARGET]);
 return rows[0]||{};
}
const daySQL="(now() AT TIME ZONE 'America/Campo_Grande')::date";
async function stats(){
 // Expiration is a review deadline, never evidence that a queued clip failed.
 // Preserve isolated records and their queue identity until independently verified.
 // The existing QA incident route is the secondary recovery path; do not replay.

 const [controlState,counts,confirmed,queued,inflight]=await Promise.all([
  control(),database('SELECT status,count(*)::int as n FROM cortes_publications WHERE target_key=$1 GROUP BY status',[TARGET]),
  database("SELECT id,remote_id FROM cortes_publications WHERE target_key=$1 AND status='confirmed' AND confirmation_evidence->>'kind'='threads_cloud_verified' ORDER BY updated_at DESC LIMIT 100",[TARGET]),database("SELECT p.id,p.payload->>'source_day' AS source_day FROM cortes_publications p WHERE p.target_key=$1 AND p.status='queued' AND NOT EXISTS (SELECT 1 FROM cortes_threads_quarantine q WHERE q.id=p.id AND q.status='isolated' AND q.expires_at>now()) ORDER BY p.created_at ASC LIMIT 200",[TARGET]),database("SELECT count(*)::int AS n FROM cortes_publications WHERE target_key=$1 AND status IN ('started','leased') AND lease_owner LIKE 'github-threads:%'",[TARGET])]);
 return{ok:true,owner:controlState.owner||'local',epoch:Number(controlState.epoch||0),
  lease_until:controlState.lease_until||null,cloud_primary_enabled:controlState.cloud_primary_enabled===true||controlState.cloud_primary_enabled==='t',cloud_heartbeat_at:controlState.cloud_heartbeat_at||null,cloud_last_success_at:controlState.cloud_last_success_at||null,cloud_inflight:Number(inflight[0]?.n||0),queued_ids:queued.map(z=>z.id),queued_rows:queued.map(z=>({id:z.id,source_day:z.source_day})),confirmed:confirmed.map(z=>({id:z.id,url:z.remote_id})),
  counts:Object.fromEntries(counts.map(z=>[z.status,Number(z.n)]))};
}
async function action(body,role,claims){
 const id=String(body?.id||''),epoch=Number(body?.epoch),run=String(claims?.run_id||'');
 if(role==='device'&&body.action==='ack-pause'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET local_paused_at=now(),local_pause_until=now()+interval '8 minutes',updated_at=now() WHERE target_key=$1 AND (owner='local' OR lease_until<now()) RETURNING epoch,owner,local_pause_until",[TARGET]);
  return rows[0]?{ok:true,ack:rows[0]}:{ok:false,error:'CLOUD_OWNER_ALREADY_ACTIVE'};
 }

 if(role==='device'&&body.action==='activate-primary'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET cloud_primary_enabled=true,cloud_heartbeat_at=now(),updated_at=now() WHERE target_key=$1 AND owner='local' AND local_paused_at>now()-interval '6 minutes' AND local_pause_until>now() RETURNING epoch,cloud_primary_enabled",[TARGET]);
  return rows[0]?{ok:true,primary:rows[0]}:{ok:false,error:'PAUSE_ACK_REQUIRED'};
 }
 if(role==='device'&&body.action==='deactivate-primary'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET cloud_primary_enabled=false,local_pause_until=NULL,updated_at=now() WHERE target_key=$1 AND owner='local' AND (cloud_heartbeat_at IS NULL OR cloud_heartbeat_at<now()-interval '18 minutes') AND NOT EXISTS (SELECT 1 FROM cortes_publications p WHERE p.target_key=$1 AND p.status IN ('leased','started') AND p.lease_owner LIKE 'github-threads:%') RETURNING cloud_primary_enabled",[TARGET]);
  return rows[0]?{ok:true,standby:rows[0]}:{ok:false,error:'CLOUD_STILL_HEALTHY_OR_ACTIVE'};
 }
 if(role!=='github')return{ok:false,error:'CLOUD_OIDC_REQUIRED'};
 if(body.action==='yield-primary'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET cloud_primary_enabled=false,updated_at=now() WHERE target_key=$1 AND owner='local' AND (cloud_last_success_at IS NULL OR cloud_last_success_at<now()-interval '16 minutes') AND NOT EXISTS (SELECT 1 FROM cortes_publications p WHERE p.target_key=$1 AND p.status IN ('leased','started') AND p.lease_owner LIKE 'github-threads:%') RETURNING cloud_primary_enabled",[TARGET]);
  return rows[0]?{ok:true,yielded:true}:{ok:false,error:'CLOUD_LEASE_ACTIVE_OR_RECENT_PROGRESS'};
 }
 if(body.action==='heartbeat'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET cloud_heartbeat_at=now(),updated_at=now() WHERE target_key=$1 AND cloud_primary_enabled=true RETURNING epoch,cloud_primary_enabled",[TARGET]);
  return rows[0]?{ok:true,heartbeat:rows[0]}:{ok:false,error:'CLOUD_PRIMARY_DISABLED'};
 }
 if(body.action==='quarantine'){
  if(!idValid(id)||!['MEDIA_HTTP_404','MEDIA_HTTP_410','MEDIA_HTTP_403','MEDIA_HTTP_5XX','MEDIA_FETCH_ERROR','MEDIA_INVALID','CAPTION_FETCH_ERROR','EDITORIAL_MISSING'].includes(String(body.reason||'')))return{ok:false,error:'INVALID_QUARANTINE'};
  const rows=await database("INSERT INTO cortes_threads_quarantine(id,target_key,reason_code,expires_at) SELECT id,target_key,$3,CASE WHEN $3='EDITORIAL_MISSING' THEN now()+interval '365 days' ELSE now()+interval '24 hours' END FROM cortes_publications WHERE id=$1 AND target_key=$2 AND status='queued' ON CONFLICT(id) DO UPDATE SET error_count=cortes_threads_quarantine.error_count+1,last_checked_at=now(),updated_at=now() WHERE cortes_threads_quarantine.status='isolated' RETURNING id,reason_code,detected_at,expires_at,error_count",[id,TARGET,body.reason]);
  return rows[0]?{ok:true,quarantine:rows[0],first_notice:Number(rows[0].error_count)===1}:{ok:false,error:'CANNOT_QUARANTINE_NONQUEUED'};
 }
 if(body.action==='claim'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET owner='cloud',epoch=epoch+1,lease_until=now()+interval '10 minutes',local_pause_until=NULL,updated_at=now() WHERE target_key=$1 AND ((cloud_primary_enabled=true AND (cloud_last_success_at IS NULL OR cloud_last_success_at<now()-interval '6 minutes')) OR (local_paused_at>now()-interval '8 minutes' AND local_pause_until>now() AND $2='workflow_dispatch')) AND (owner='local' OR lease_until<now()) RETURNING epoch,owner,lease_until",[TARGET,claims?.event_name||'']);
  return rows[0]?{ok:true,lease:rows[0]}:{ok:false,error:'NO_FRESH_LOCAL_PAUSE_ACK'};
 }
 if(!Number.isSafeInteger(epoch)||epoch<1)return{ok:false,error:'INVALID_FENCE_EPOCH'};
 if(body.action==='reserve'){
  if(!idValid(id))return{ok:false,error:'INVALID_MEDIA_ID'};
  const hash=String(body.sha256||'').toLowerCase();
  const media=String(body.media_url||'');
  if(!/^[0-9a-f]{64}$/.test(hash)||!/^https:\/\/anthares\.us\/wp-content\/uploads\/anthares-clips\/\d{4}\/\d{2}\/short_/.test(media))return{ok:false,error:'MEDIA_NOT_VERIFIED'};
  // row-level atomic update; no blind retries after a submission begins.
  const rows=await database("UPDATE cortes_publications p SET status='leased',lease_owner=$3,lease_generation=p.lease_generation+1,lease_until=now()+interval '12 minutes',media_sha256=$4,payload=p.payload||jsonb_build_object('cloud_media_url',$5),updated_at=now() WHERE p.target_key=$1 AND p.id=$2 AND p.status='queued' AND (p.payload->>'media_url'=$5 OR p.payload->>'video_url'=$5) AND (p.media_sha256='UNVERIFIED_SOURCE_HASH' OR p.media_sha256=$4) AND EXISTS (SELECT 1 FROM cortes_threads_executor_handoff h WHERE h.target_key=$1 AND h.owner='cloud' AND h.epoch=$6 AND h.lease_until>now()+interval '60 seconds') RETURNING p.id,p.lease_generation,p.status",[TARGET,id,'github-threads:'+run,hash,media,epoch]);
  return rows[0]?{ok:true,job:rows[0]}:{ok:false,error:'NOT_QUEUED_OR_CLOUD_FENCE_INVALID'};
 }
 if(body.action==='start'){
  if(!idValid(id))return{ok:false,error:'INVALID_MEDIA_ID'};
  const generation=Number(body.generation);
  const rows=await database("UPDATE cortes_publications SET status='started',publication_started_at=now(),updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 AND lease_until>now() AND EXISTS (SELECT 1 FROM cortes_threads_executor_handoff h WHERE h.target_key=$2 AND h.owner='cloud' AND h.epoch=$5 AND h.lease_until>now()) RETURNING id,status",[id,TARGET,'github-threads:'+run,generation,epoch]);
  return rows[0]?{ok:true,job:rows[0]}:{ok:false,error:'START_FENCED_OR_QUOTA_REACHED'};
 }
 if(body.action==='confirm'){
  if(!idValid(id)||!goodUrl(String(body.url||'')))return{ok:false,error:'INVALID_VERIFICATION_URL'};
  const generation=Number(body.generation);
  const rows=await database("UPDATE cortes_publications SET status='confirmed',remote_id=$5,confirmation_evidence=jsonb_build_object('kind','threads_cloud_verified','permalink',$5,'verified_at',now(),'run_id',$6),lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND lease_generation=$4 AND ((status='started' AND lease_owner=$3) OR (status='confirmed' AND remote_id=$5 AND confirmation_evidence->>'run_id'=$6)) RETURNING id,status,remote_id",[id,TARGET,'github-threads:'+run,generation,body.url,run]);
  if(rows[0])await database("UPDATE cortes_threads_executor_handoff SET remote_confirmed_url=$2,cloud_last_success_at=now(),cloud_heartbeat_at=now(),updated_at=now() WHERE target_key=$1 AND epoch=$3",[TARGET,body.url,epoch]).catch(()=>null);
  return rows[0]?{ok:true,job:rows[0]}:{ok:false,error:'CONFIRM_FENCED'};
 }
 if(body.action==='uncertain'){
  if(!idValid(id))return{ok:false,error:'INVALID_MEDIA_ID'};
  const rows=await database("UPDATE cortes_publications SET status='uncertain',confirmation_evidence=jsonb_build_object('kind','threads_cloud_unknown','marked_at',now(),'submitted_post_url',$5,'graph_post_id',$6),lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status IN ('leased','started') AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,TARGET,'github-threads:'+run,Number(body.generation),goodUrl(String(body.url||''))?String(body.url):null,/^\d{8,24}$/.test(String(body.post_id||''))?String(body.post_id):null]);
  return rows[0]?{ok:true,job:rows[0]}:{ok:false,error:'UNCERTAIN_FENCE_REJECTED'};
 }
 if(body.action==='release'){
  const rows=await database("UPDATE cortes_threads_executor_handoff SET owner='local',lease_until=NULL,local_pause_until=NULL,updated_at=now() WHERE target_key=$1 AND owner='cloud' AND epoch=$2 RETURNING epoch,owner",[TARGET,epoch]);
  return rows[0]?{ok:true,control:rows[0]}:{ok:false,error:'RELEASE_FENCE_INVALID'};
 }
 return{ok:false,error:'UNKNOWN_ACTION'};
}
export default {async fetch(request){
 const url=new URL(request.url),op=url.searchParams.get('action')||'';
 if(request.method==='GET'&&op==='health'){
  try{await database('SELECT 1 AS ok');return json({ok:true,service:'cortesthreadspub',cloud_publishing_enabled:false,database_ok:true})}catch{return json({ok:false,database_ok:false},503)}
 }
 if(request.method==='GET'&&op==='gate'){
  try{return json(await stats())}catch{return json({ok:false,error:'BACKEND_UNAVAILABLE'},503)}
 }
 if(request.method==='POST'&&op==='preflight'){
  const claims=await githubAuth(request,true);
  return claims?json({ok:true,repository:REPO,ref:claims.ref,workflow:WORKFLOW,event:claims.event_name,mutations_allowed:false}):json({ok:false,error:'OIDC_IDENTITY_REJECTED'},401);
 }
 if(request.method!=='POST'||op!=='control')return json({ok:false,error:'NOT_FOUND'},404);
 let body;try{const raw=await request.text();if(raw.length>8000)return json({ok:false,error:'BODY_TOO_LARGE'},413);body=JSON.parse(raw)}catch{return json({ok:false,error:'INVALID_BODY'},400)}
 try{
  let role=null,claims=null;
  if(['ack-pause','activate-primary','deactivate-primary'].includes(body.action)&&await deviceAuth(request))role='device';
  else{claims=await githubAuth(request);if(claims)role='github'}
  if(!role)return json({ok:false,error:'AUTH_REQUIRED'},401);
  const result=await action(body,role,claims);
  return json(result,result.ok?200:409);
 }catch(e){const reason=String(e?.message||'').match(/^(NEON_QUERY_HTTP_[0-9]{3}|NEON_QUERY_BAD_RESPONSE|NEON_DATABASE_URL_MISSING)$/)?.[0]||'INTERNAL_BACKEND_ERROR';return json({ok:false,error:'CLOUD_CONTROL_FAILED',error_class:e?.name||'Error',reason_code:reason},503)}
}};
