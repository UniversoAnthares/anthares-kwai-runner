import crypto from 'node:crypto';
// Canonical CORTES ledger is Neon PostgreSQL. No local queue or Vercel dependency.
// This function never publishes media and never accepts device-PC authentication.
const AUD='https://anthares-remote-primary.vercel.app/api/cortes-queue';
const TARGETS={linkedin:'linkedin:primary',instagram:'instagram:universoanthares',pinterest:'pinterest:lucasyahn'};
const BUFFER_WORKFLOWS={linkedin:'cortes-buffer-linkedin-cloud.yml',instagram:'cortes-buffer-instagram-cloud.yml',pinterest:'cortes-buffer-pinterest-cloud.yml'};
const CLIPPER_PRODUCERS=new Set(['cortes-buffer-fanout-cloud.yml','cortes-neon-short-dispatch.yml','cortes-daily.yml']);
const RUNNER_PRODUCERS=new Set(['cortes-linkedin-neon-fanout.yml','cortes-buffer-three-fanout-cloud.yml']);
const PROBE_WORKFLOWS=new Set(['cortes-queue-ha-acceptance.yml','cortes-queue-cloudflare-ha.yml']);
const LIMITS={linkedin:50,instagram:50,pinterest:25};
const REPO='UniversoAnthares/anthares-kwai-runner';
const CLIPPER='UniversoAnthares/anthares-clipper';
let keys=null,keyExpires=0;
const sha=s=>crypto.createHash('sha256').update(String(s)).digest('hex');
function answer(obj,status=200){return Response.json(obj,{status,headers:{'Cache-Control':'no-store'}});}
async function query(sql,params=[]){
 const conn=process.env.DATABASE_URL;
 if(!conn)throw Error('DATABASE_CONFIG_MISSING');
 const db=new URL(conn);
 if(db.protocol!=='postgresql:'&&db.protocol!=='postgres:')throw Error('DATABASE_URL_INVALID');
 if(!db.hostname.endsWith('.neon.tech'))throw Error('DATABASE_HOST_UNTRUSTED');
 const host='https://api.'+db.hostname.split('.').slice(1).join('.')+'/sql';
 const res=await fetch(host,{method:'POST',headers:{'Content-Type':'application/json',
    'Neon-Connection-String':conn,'Neon-Raw-Text-Output':'true'},
   body:JSON.stringify({query:sql,params}),signal:AbortSignal.timeout(15000)});
 if(!res.ok)throw Error('DATABASE_QUERY_HTTP_'+res.status);
 const result=await res.json();
 if(!result||!Array.isArray(result.rows))throw Error('DATABASE_RESPONSE_INVALID');
 return result.rows;
}
function target(platform){return TARGETS[platform]||null;}
function shaPayload(b){
 const src=String(b.source_id||''),seg=String(b.segment_id||''),url=String(b.media_url||'');
 return sha(src+'|'+seg+'|'+url);
}
function validJob(b){
 if(!b||typeof b!=='object')return false;
 const plat=String(b.platform||''),dest=target(plat);
 if(!dest||b.target_key!==dest||b.account_id!==dest.split(':')[1]||
   b.executor!=='social_video'||b.duration_class!=='short')return false;
 const src=String(b.source_id||''),seg=String(b.segment_id||''),media=String(b.media_url||'');
 if(!src||!seg||src.length>256||seg.length>256||!String(b.title||'').trim()||
   b.master_id!==src||b.video_url!==media||!(Number(b.duration_seconds)>=30&&Number(b.duration_seconds)<=90))return false;
 let u;try{u=new URL(media);}catch{return false;}
 if(u.protocol!=='https:'||!['anthares.us','www.anthares.us'].includes(u.hostname)||
    u.username||u.password||u.port||!u.pathname.toLowerCase().endsWith('.mp4'))return false;
 const start=Number(b.source_start),end=Number(b.source_end);
 if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<=start||
    !Number.isInteger(Number(b.cortes_attachment_id))||Number(b.cortes_attachment_id)<=0)return false;
 const id='cortes-fanout-'+plat+'-'+sha(src+'|'+seg+'|'+dest).slice(0,32);
 return b.id===id&&b.dedupe_key===id&&b.media_sha256===shaPayload(b);
}
async function identity(request){
 const m=/^Bearer\s+(.+)$/i.exec(request.headers.get('authorization')||'');
 if(!m||m[1].length<60||m[1].length>16000)return null;
 const pieces=m[1].split('.');
 if(pieces.length!==3)return null;
 let head,claims;try{
  head=JSON.parse(Buffer.from(pieces[0],'base64url').toString());
  claims=JSON.parse(Buffer.from(pieces[1],'base64url').toString());
 }catch{return null;}
 const now=Math.floor(Date.now()/1000);
 if(head.alg!=='RS256'||typeof head.kid!=='string'||head.kid.length>200||
    claims.iss!=='https://token.actions.githubusercontent.com'||claims.ref!=='refs/heads/main'||
    !['schedule','workflow_dispatch','push'].includes(claims.event_name)||
    !Number.isFinite(claims.exp)||claims.exp<=now||
    !Number.isFinite(claims.iat)||claims.iat>now+60||
    (claims.nbf!==undefined&&claims.nbf>now+60)||
    !(Array.isArray(claims.aud)?claims.aud:[claims.aud]).includes(AUD))return null;
 const repo=String(claims.repository||''),ref=String(claims.job_workflow_ref||claims.workflow_ref||'');
 const prefix=repo+'/.github/workflows/';
 if(!ref.startsWith(prefix)||!ref.endsWith('@refs/heads/main'))return null;
 const wf=ref.slice(prefix.length,-'@refs/heads/main'.length);
 let role=null,platform=null;
 if(repo===REPO){
  platform=Object.keys(BUFFER_WORKFLOWS).find(p=>BUFFER_WORKFLOWS[p]===wf);
  if(platform)role='buffer';
  else if(RUNNER_PRODUCERS.has(wf))role='producer';
  else if(wf==='cortes-linkedin-personal-cloud.yml')role='personal';
  else if(PROBE_WORKFLOWS.has(wf))role='probe';
  else if(wf==='cortes-neon-ha-oidc-proof.yml'){role='probe';platform='linkedin';}
 }else if(repo===CLIPPER&&CLIPPER_PRODUCERS.has(wf))role='producer';
 if(!role)return null;
 try{
  if(!keys||Date.now()>=keyExpires){
   const doc=await fetch('https://token.actions.githubusercontent.com/.well-known/openid-configuration',{signal:AbortSignal.timeout(8000)});
   if(!doc.ok)return null;
   const config=await doc.json();
   if(typeof config.jwks_uri!=='string'||!config.jwks_uri.startsWith('https://token.actions.githubusercontent.com/'))return null;
   const resp=await fetch(config.jwks_uri,{signal:AbortSignal.timeout(8000)});
   if(!resp.ok)return null;
   keys=(await resp.json()).keys;keyExpires=Date.now()+300000;
  }
  const jwk=keys?.find(k=>k.kid===head.kid&&k.kty==='RSA'&&(!k.alg||k.alg==='RS256')&&(!k.use||k.use==='sig'));
  if(!jwk)return null;
  const key=crypto.createPublicKey({key:jwk,format:'jwk'});
  if(!crypto.verify('RSA-SHA256',Buffer.from(pieces[0]+'.'+pieces[1]),key,Buffer.from(pieces[2],'base64url')))return null;
  return {role,platform,workflow:wf};
 }catch{return null;}
}
async function enqueue(b){
 if(!validJob(b))return{ok:false,error:'INVALID_JOB_IDENTITY'};
 const q=`INSERT INTO cortes_publications(id,dedupe_key,target_key,master_id,media_sha256,source_id,
    source_start,source_end,duration_class,payload)
    VALUES($1,$2,$3,$4,$5,$6,$7,$8,'short',$9::jsonb)
    ON CONFLICT DO NOTHING RETURNING id,target_key,status`;
 const args=[b.id,b.dedupe_key,b.target_key,b.master_id,b.media_sha256,b.source_id,
   b.source_start,b.source_end,JSON.stringify(b)];
 const created=await query(q,args);
 if(created.length)return{ok:true,deduped:false,job:created[0]};
 const found=await query('SELECT id,target_key,status,master_id,media_sha256,source_id,source_start,source_end,duration_class,dedupe_key FROM cortes_publications WHERE id=$1 OR dedupe_key=$2 LIMIT 1',[b.id,b.dedupe_key]);
 const r=found[0];
 if(!r||r.id!==b.id||r.dedupe_key!==b.dedupe_key||r.target_key!==b.target_key||
   r.media_sha256!==b.media_sha256||r.master_id!==b.master_id||
   String(r.source_start)!==String(b.source_start)||String(r.source_end)!==String(b.source_end))
   return{ok:false,error:'IDENTITY_COLLISION'};
 return{ok:true,deduped:true,reason:'identity',job:{id:r.id,target_key:r.target_key,status:r.status}};
}
async function writeProbe(body){
 const nonce=String(body.nonce||'');
 if(!/^[A-Za-z0-9_-]{8,90}$/.test(nonce))return{ok:false,error:'INVALID_PROBE_NONCE'};
 await query(`CREATE TABLE IF NOT EXISTS cortes_queue_ha_probe(
    nonce text PRIMARY KEY,
    service text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now())`);
 const r=await query(`INSERT INTO cortes_queue_ha_probe(nonce,service) VALUES($1,'neon-functions')
    ON CONFLICT (nonce) DO UPDATE SET service=EXCLUDED.service
    RETURNING nonce,service`,[nonce]);
 if(r.length!==1||r[0].nonce!==nonce||r[0].service!=='neon-functions')
    return{ok:false,error:'PROBE_WRITE_NOT_VERIFIED'};
 // Diagnostic writes never touch publication ledger, neither jobs nor posts.
 await query('DELETE FROM cortes_queue_ha_probe WHERE nonce=$1',[nonce]);
 return{ok:true,probe:'SIGNED_OIDC_NEON_WRITE_READ_DELETE',database_ok:true};
}
async function bufferAction(verb,b,platform){
 const dest=target(platform),owner='buffer-'+platform+':';
 const allowed=new Set(['lease','start','fail','scheduled','pending','reconcile','stats','retention']);
 if(!allowed.has(verb))return{ok:false,error:'UNKNOWN_BUFFER_ACTION'};
 if(verb==='stats'){
  const rows=await query(`SELECT status,count(*)::int n FROM cortes_publications
   WHERE target_key=$1 GROUP BY status`,[dest]);
  return{ok:true,target_key:dest,counts:Object.fromEntries(rows.map(r=>[r.status,Number(r.n)]))};
 }
 if(verb==='retention'){
  const id=String(b.id||'');
  const rows=await query('SELECT id,status FROM cortes_publications WHERE id=$1 AND target_key=$2',[id,dest]);
  return{ok:true,safe_to_delete:rows.length===1&&rows[0].status==='confirmed',status:rows[0]?.status||'missing'};
 }
 if(verb==='pending'){
  const rows=await query(`SELECT id,remote_id,confirmation_evidence FROM cortes_publications
   WHERE target_key=$1 AND status='uncertain'
   AND confirmation_evidence->>'kind'='buffer_scheduled'
   ORDER BY updated_at ASC LIMIT 2`,[dest]);
  return{ok:true,jobs:rows};
 }
 if(verb==='lease'){
  if(b.target_key!==dest||!String(b.owner||'').startsWith(owner))return{ok:false,error:'WRONG_QUEUE_OWNER'};
  const held=await query(`SELECT count(*)::int n FROM cortes_publications
   WHERE target_key=$1 AND status='uncertain'
   AND confirmation_evidence->>'kind'='buffer_scheduled'`,[dest]);
  if(Number(held[0]?.n||0)>=8)return{ok:true,job:null,buffer_pending_limit:true};
  const used=await query(`SELECT count(*)::int n FROM cortes_publications WHERE target_key=$1
   AND status IN ('confirmed','leased','started','uncertain') AND updated_at>now()-interval '24 hours'`,[dest]);
  if(Number(used[0]?.n||0)>=LIMITS[platform])return{ok:true,job:null,platform_daily_limit:true,limit:LIMITS[platform]};
  // Lease only current-day jobs; never silently roll yesterday's daily round forward.
  const row=await query(`WITH picked AS(
     SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued'
       AND created_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande')
                          AT TIME ZONE 'America/Campo_Grande')
     ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1)
   UPDATE cortes_publications p SET status='leased',lease_owner=$2,
       lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',updated_at=now()
   FROM picked WHERE p.id=picked.id AND p.status='queued'
   RETURNING p.id,p.target_key,p.payload,p.lease_generation,p.duration_class`,[dest,String(b.owner)]);
  return{ok:true,job:row[0]||null};
 }
 const id=String(b.id||''),fence=Number(b.lease_generation),who=String(b.owner||'');
 if(!id||!who.startsWith(owner)||!Number.isInteger(fence)||fence<1)return{ok:false,error:'INVALID_FENCE'};
 if(verb==='start'){
  const rows=await query(`UPDATE cortes_publications SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4
    AND lease_until>now() RETURNING id,status`,[id,dest,who,fence]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'STALE_FENCE'};
 }
 if(verb==='fail'){
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
      lease_until=NULL,updated_at=now(),lease_owner=CASE WHEN publication_started_at IS NULL THEN NULL ELSE lease_owner END
    WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4 AND status IN ('leased','started')
    RETURNING id,status`,[id,dest,who,fence]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'STALE_FENCE'};
 }
 if(verb==='scheduled'){
  const remote=String(b.buffer_post_id||'');
  if(!/^[A-Za-z0-9_:-]{1,160}$/.test(remote))return{ok:false,error:'INVALID_BUFFER_ID'};
  const evidence={kind:'buffer_scheduled',buffer_post_id:remote,platform,confirmed_on_network:false};
  const rows=await query(`UPDATE cortes_publications SET status='uncertain',remote_id=$5,
     confirmation_evidence=$6::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4 AND status='started'
    RETURNING id,target_key,status,remote_id`,
    [id,dest,who,fence,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'STALE_FENCE'};
 }
 if(verb==='reconcile'){
  const remote=String(b.remote_id||''),link=String(b.external_link||'');
  let url;try{url=new URL(link);}catch{return{ok:false,error:'INVALID_PUBLIC_URL'};}
  const h=url.hostname,p=url.pathname;
  if(url.username||url.password||url.port||url.search||url.hash)
    return{ok:false,error:'INVALID_PUBLIC_URL'};
  const valid=platform==='linkedin'?(h==='linkedin.com'||h==='www.linkedin.com')&&
     (p.startsWith('/feed/update/')||p.startsWith('/posts/')||/^\/company\/145345334\/posts\//.test(p)):
   platform==='instagram'?(h==='instagram.com'||h==='www.instagram.com')&&/^\/(reel|p)\/[A-Za-z0-9_-]+\/?$/.test(p):
     (h==='pinterest.com'||h==='www.pinterest.com')&&/^\/pin\/[0-9]+\/?$/.test(p);
  if(url.protocol!=='https:'||!valid||url.username||url.password)return{ok:false,error:'INVALID_PUBLIC_URL'};
  const evidence={kind:'buffer_'+platform+'_sent_verified',buffer_post_id:remote,
    external_link:link,confirmed_on_network:true};
  const rows=await query(`UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$4::jsonb,
   lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND remote_id=$3 AND status='uncertain'
     AND confirmation_evidence->>'kind'='buffer_scheduled' RETURNING id,status,remote_id`,
   [id,dest,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'UNVERIFIED_OR_DUPLICATE'};
 }
 return{ok:false,error:'ACTION_DISABLED'};
}
const LINKEDIN_PERSONAL_TARGET='linkedin:personal';
const LINKEDIN_PERSONAL_OWNER='linkedin-personal:github-cloud';
async function personalAction(action,body){
 const dest=LINKEDIN_PERSONAL_TARGET;
 const owner=String(body.owner||'');
 const id=String(body.id||'');
 const fence=Number(body.lease_generation);
 if(action==='pending'){
  const jobs=await query(`SELECT id,remote_id,confirmation_evidence FROM cortes_publications
    WHERE target_key=$1 AND status='uncertain'
    AND confirmation_evidence->>'kind'='personal_linkedin_post_uncertain'
    ORDER BY updated_at LIMIT 4`,[dest]);
  return{ok:true,jobs};
 }
 if(action==='stats'){
  const rows=await query('SELECT status,count(*)::int n FROM cortes_publications WHERE target_key=$1 GROUP BY status',[dest]);
  return{ok:true,counts:Object.fromEntries(rows.map(r=>[r.status,Number(r.n)]))};
 }
 if(action==='lease'){
  if(body.target_key!==dest||owner!==LINKEDIN_PERSONAL_OWNER)
    return{ok:false,error:'PERSONAL_OWNER_MISMATCH'};
  const rows=await query(`WITH candidate AS
   (SELECT id FROM cortes_publications
     WHERE target_key=$1 AND status='queued'
       AND created_at >= (date_trunc('day', now() AT TIME ZONE 'America/Campo_Grande')
                          AT TIME ZONE 'America/Campo_Grande')
     ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1)
   UPDATE cortes_publications p SET status='leased',lease_owner=$2,
        lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',
        updated_at=now()
    FROM candidate WHERE p.id=candidate.id AND p.status='queued'
    RETURNING p.id,p.target_key,p.duration_class,p.payload,p.lease_generation`,[dest,owner]);
  return{ok:true,job:rows[0]||null};
 }
 if(!id||owner!==LINKEDIN_PERSONAL_OWNER||!Number.isInteger(fence)||fence<1)
   return{ok:false,error:'PERSONAL_FENCE_REQUIRED'};
 if(action==='start'){
  const rows=await query(`UPDATE cortes_publications SET status='started',
    publication_started_at=coalesce(publication_started_at,now()),updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3
      AND lease_generation=$4 AND lease_until>now()
    RETURNING id,status`,[id,dest,owner,fence]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 if(action==='fail'){
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
        confirmation_evidence=CASE WHEN publication_started_at IS NULL THEN confirmation_evidence
           ELSE jsonb_build_object('kind','personal_linkedin_post_uncertain',
                                   'remote_id',COALESCE(remote_id,'')) END,
        lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status IN ('leased','started')
      AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,
     [id,dest,owner,fence]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 if(action==='uncertain'){
  const remote=String(body.remote_id||'');
  if(remote&&!/^urn:li:(?:ugcPost|share):[0-9]+$/.test(remote))
    return{ok:false,error:'PERSONAL_REMOTE_ID_INVALID'};
  const evidence={kind:'personal_linkedin_post_uncertain',remote_id:remote,confirmed:false};
  const rows=await query(`UPDATE cortes_publications SET status='uncertain',
       remote_id=NULLIF($5,''),confirmation_evidence=$6::jsonb,
       lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='started'
      AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,
    [id,dest,owner,fence,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 if(action==='confirm'){
  const remote=String(body.remote_id||'');
  const link=String(body.external_link||'');
  if(!/^urn:li:(?:ugcPost|share):[0-9]+$/.test(remote))
    return{ok:false,error:'PERSONAL_REMOTE_ID_INVALID'};
  const expected='https://www.linkedin.com/feed/update/'+remote;
  if(link!==expected)return{ok:false,error:'PERSONAL_PUBLIC_LINK_MISMATCH'};
  const evidence={kind:'personal_linkedin_post_verified',external_link:link,
      author_type:'person',remote_id:remote,confirmed:true};
  const rows=await query(`UPDATE cortes_publications SET status='confirmed',remote_id=$5,
     confirmation_evidence=$6::jsonb,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status IN ('started','uncertain')
      AND lease_generation=$4 AND
      (lease_owner=$3 OR (status='uncertain' AND remote_id=$5))
    RETURNING id,status,remote_id`,
    [id,dest,owner,fence,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_CONFIRM_STALE'};
 }
 return{ok:false,error:'PERSONAL_ACTION_UNKNOWN'};
}

export default {async fetch(request){
 const url=new URL(request.url),action=url.searchParams.get('action')||'';
 if(request.method==='GET'&&action==='health'){
  try{
   const r=await query(`SELECT target_key,status,count(*)::int n FROM cortes_publications
    WHERE target_key IN ('linkedin:primary','linkedin:personal','instagram:universoanthares','pinterest:lucasyahn')
    GROUP BY target_key,status`);
   return answer({ok:true,backend:'neon-functions-cortes',database_ok:true,
     network_isolation:true,counts:r},200);
  }catch{return answer({ok:false,backend:'neon-functions-cortes',database_ok:false},503);}
 }
 if(request.method!=='POST')return answer({ok:false,error:'NOT_FOUND'},404);
 if(Number(request.headers.get('content-length')||0)>65536)return answer({ok:false,error:'TOO_LARGE'},413);
 const actor=await identity(request);
 if(!actor)return answer({ok:false,error:'OIDC_UNAUTHORIZED'},401);
 let body;try{body=await request.json();}catch{return answer({ok:false,error:'INVALID_JSON'},400);}
 if(!body||typeof body!=='object'||Array.isArray(body))return answer({ok:false,error:'INVALID_BODY'},400);
 if(JSON.stringify(body).length>65536)return answer({ok:false,error:'TOO_LARGE'},413);
 try{
  if(action==='buffer-pending'&&actor.role==='probe')
    return answer(await bufferAction('pending',body,'linkedin'));
  if(action==='probe'){
   if(actor.role!=='probe')return answer({ok:false,error:'PROBE_WORKFLOW_ONLY'},403);
   const out=await writeProbe(body);
   return answer(out,out.ok?200:409);
  }
  if(action.startsWith('personal-')){
   if(actor.role!=='personal')return answer({ok:false,error:'MEMBER_WORKFLOW_ONLY'},403);
   const out=await personalAction(action.slice('personal-'.length),body);
   return answer(out,out.ok?200:409);
  }
  if(action==='enqueue'){
   if(actor.role!=='producer')return answer({ok:false,error:'PRODUCER_ONLY'},403);
   if(actor.workflow==='cortes-linkedin-neon-fanout.yml'&&body.platform!=='linkedin')
       return answer({ok:false,error:'WORKFLOW_DESTINATION_MISMATCH'},403);
   return answer(await enqueue(body));
  }
  if(action.startsWith('buffer-')){
   if(actor.role!=='buffer')return answer({ok:false,error:'BUFFER_WORKER_ONLY'},403);
   const out=await bufferAction(action.slice(7),body,actor.platform);
   return answer(out,out.ok?200:409);
  }
  return answer({ok:false,error:'NOT_FOUND'},404);
 }catch{return answer({ok:false,error:'QUEUE_BACKEND_UNAVAILABLE'},503);}
}};
