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
    !['schedule','workflow_dispatch','push','workflow_run'].includes(claims.event_name)||
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
  else if(PROBE_WORKFLOWS.has(wf))role='probe';
  else if(wf==='cortes-neon-ha-oidc-proof.yml'){role='probe';platform='linkedin';}
  else if(wf==='cortes-linkedin-personal-cloud.yml'){role='personal';platform='linkedin';}
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
 const allowed=new Set(['lease','start','fail','media-missing','scheduled','pending','reconcile','stats','retention']);
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
  if(platform==='linkedin')await recoverExpiredLinkedin(dest);
  const held=await query(`SELECT count(*)::int n FROM cortes_publications
   WHERE target_key=$1 AND status='uncertain'
   AND confirmation_evidence->>'kind'='buffer_scheduled'`,[dest]);
  if(Number(held[0]?.n||0)>=8)return{ok:true,job:null,buffer_pending_limit:true};
  const used=await query(`SELECT count(*)::int n FROM cortes_publications WHERE target_key=$1
   AND status IN ('confirmed','leased','started','uncertain') AND updated_at>now()-interval '24 hours'`,[dest]);
  if(Number(used[0]?.n||0)>=LIMITS[platform])return{ok:true,job:null,platform_daily_limit:true,limit:LIMITS[platform]};
  // Same stable daily rank as the Vercel route: at most 100 Buffer
  // allocations per week; remaining Pinterest clips belong to browser lane.
  const pinterest=platform==='pinterest';
  const row=await query(pinterest?`WITH ranked AS (
    SELECT id,row_number() OVER (
       PARTITION BY (created_at AT TIME ZONE 'America/Campo_Grande')::date
       ORDER BY created_at,id) ordinal,
       extract(isodow FROM created_at AT TIME ZONE 'America/Campo_Grande')::int weekday
    FROM cortes_publications WHERE target_key=$1
   ), picked AS (
     SELECT p.id FROM cortes_publications p JOIN ranked r ON r.id=p.id
      WHERE p.target_key=$1 AND p.status='queued'
       AND (p.created_at AT TIME ZONE 'America/Campo_Grande')::date =
           (now() AT TIME ZONE 'America/Campo_Grande')::date
       AND r.ordinal <= CASE WHEN r.weekday IN (1,2) THEN 15 ELSE 14 END
      ORDER BY p.created_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1
   ) UPDATE cortes_publications p SET status='leased',lease_owner=$2,
    lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',
    updated_at=now() FROM picked WHERE p.id=picked.id AND p.status='queued'
    RETURNING p.id,p.target_key,p.payload,p.lease_generation,p.duration_class`:
   `WITH picked AS(
     SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued'
       AND created_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande')
                          AT TIME ZONE 'America/Campo_Grande')
     ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1)
   UPDATE cortes_publications p SET status='leased',lease_owner=$2,
       lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',updated_at=now()
   FROM picked WHERE p.id=picked.id AND p.status='queued'
   RETURNING p.id,p.target_key,p.payload,p.lease_generation,p.duration_class`,[dest,String(b.owner)]);
  return{ok:true,job:row[0]||null,delivery_route:pinterest?'buffer':undefined};
 }
 const id=String(b.id||''),fence=Number(b.lease_generation),who=String(b.owner||'');
 // Reconciliation is OIDC-authenticated and CAS-protected by id, remote_id,
// target and buffer_scheduled evidence. It has no active lease by design:
// buffer-scheduled explicitly clears lease_owner and lease_until.
if(!id)return{ok:false,error:'INVALID_ID'};
if(verb!=='reconcile'&&(!who.startsWith(owner)||!Number.isInteger(fence)||fence<1))
  return{ok:false,error:'INVALID_FENCE'};
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
 if(verb==='media-missing'){
  const evidence={kind:'source_media_http_404',account:dest,confirmed_on_network:false};
  const rows=await query(`UPDATE cortes_publications SET status='failed',
      confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now()
      WHERE id=$1 AND target_key=$2 AND status='leased'
        AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,
      [id,dest,who,fence,JSON.stringify(evidence)]);
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

/** Device-authenticated Pinterest browser surplus lane; no other target enabled. */
let deviceHash='',deviceHashUntil=0;
async function authorizePinterestBrowser(request){
 if((request.headers.get('x-anthares-device')||'')!=='DESKTOP-FTDK0HP')return false;
 const token=/^Bearer\s+([^\s]+)$/i.exec(request.headers.get('authorization')||'')?.[1]||'';
 if(token.length<40||token.length>4096)return false;
 try{
  if(!deviceHash||Date.now()>deviceHashUntil){
   const url='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices/DESKTOP-FTDK0HP.sha256';
   const r=await fetch(url,{headers:{'User-Agent':'AntharesCortesPinterestLocal/1.0','Cache-Control':'no-cache'},signal:AbortSignal.timeout(8000)});
   if(!r.ok)return false;
   const hash=(await r.text()).trim().toLowerCase();
   if(!/^[a-f0-9]{64}$/.test(hash))return false;
   deviceHash=hash;deviceHashUntil=Date.now()+60000;
  }
  const candidate=crypto.createHash('sha256').update(token).digest();
  const expected=Buffer.from(deviceHash,'hex');
  return expected.length===candidate.length&&crypto.timingSafeEqual(candidate,expected);
 }catch{return false}
}
async function pinterestBrowserAction(verb,b){
 const target='pinterest:lucasyahn',who='pinterest-browser:DESKTOP-FTDK0HP';
 if(!['lease','start','fail','confirm','stats','media-invalid'].includes(verb))return{ok:false,error:'BROWSER_ACTION_DENIED'};
 if(verb==='stats'){
  const rows=await query('SELECT status,count(*)::int n FROM cortes_publications WHERE target_key=$1 GROUP BY status',[target]);
  return{ok:true,target_key:target,counts:Object.fromEntries(rows.map(x=>[x.status,Number(x.n)]))};
 }
 if(b.target_key&&b.target_key!==target)return{ok:false,error:'WRONG_TARGET'};
 if(String(b.owner||'')!==who)return{ok:false,error:'WRONG_BROWSER_OWNER'};
 if(verb==='lease'){
  const cap=await query("SELECT reserved FROM cortes_daily_publication_budget WHERE target_key=$1 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[target]);
  if(Number(cap[0]?.reserved||0)>=100)return{ok:true,job:null,daily_limit_reached:true,delivery_route:'browser'};
  // A daily queue can carry work through the following local calendar day only.
  // On day 3, unposted queued items are logically discarded, never sent.
  const localDay="(now() AT TIME ZONE 'America/Campo_Grande')::date";
  const expired={kind:'pinterest_expired_after_next_day',confirmed_on_network:false};
  await query(`UPDATE cortes_publications SET status='failed',
     confirmation_evidence=$2::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now()
     WHERE target_key=$1 AND status='queued'
       AND (created_at AT TIME ZONE 'America/Campo_Grande')::date < ${localDay} - 1`,
    [target,JSON.stringify(expired)]);
  const sql=`WITH ranked AS (
   SELECT id,row_number() OVER (
      PARTITION BY (created_at AT TIME ZONE 'America/Campo_Grande')::date
      ORDER BY created_at,id) AS ordinal,
      extract(isodow FROM created_at AT TIME ZONE 'America/Campo_Grande')::int AS weekday
   FROM cortes_publications WHERE target_key=$1
  ), picked AS (
   SELECT p.id FROM cortes_publications p JOIN ranked r ON r.id=p.id
   WHERE p.target_key=$1 AND p.status='queued'
     AND (p.created_at AT TIME ZONE 'America/Campo_Grande')::date
       BETWEEN (now() AT TIME ZONE 'America/Campo_Grande')::date - 1
         AND (now() AT TIME ZONE 'America/Campo_Grande')::date
     AND ( (p.created_at AT TIME ZONE 'America/Campo_Grande')::date <
              (now() AT TIME ZONE 'America/Campo_Grande')::date
           OR r.ordinal > CASE WHEN r.weekday IN (1,2) THEN 15 ELSE 14 END )
     AND ( COALESCE(p.confirmation_evidence->>'kind','') <> 'source_media_invalid'
           OR (p.confirmation_evidence->>'retry_after_date')::date <=
                (now() AT TIME ZONE 'America/Campo_Grande')::date )
   ORDER BY p.created_at,p.updated_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1
  ) UPDATE cortes_publications p SET status='leased',lease_owner=$2,
     lease_generation=p.lease_generation+1,lease_until=now()+interval '15 minutes',updated_at=now()
    FROM picked WHERE p.id=picked.id AND p.status='queued'
    RETURNING p.id,p.target_key,p.payload,p.lease_generation,p.duration_class`;
  const rows=await query(sql,[target,who]);
  return{ok:true,job:rows[0]||null,delivery_route:'browser'};
 }
 const id=String(b.id||''),gen=Number(b.lease_generation);
 if(!id||id.length>200||!Number.isSafeInteger(gen)||gen<1)
   return{ok:false,error:'INVALID_BROWSER_FENCE'};
 if(verb==='start'){
  const rows=await query(`UPDATE cortes_publications
    SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4
      AND lease_until>now() RETURNING id,status`,[id,target,who,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'BROWSER_FENCE_EXPIRED'};
 }
 if(verb==='media-invalid'){
  // The request is permitted ONLY before the publishing phase. This fence
  // guarantees that a missing file cannot create a duplicate submission.
  const today="(now() AT TIME ZONE 'America/Campo_Grande')::date";
  const evidence={kind:'source_media_invalid',http_status:404,confirmed_on_network:false,
    retry_after_date:null};
  const rows=await query(`UPDATE cortes_publications
     SET status=CASE WHEN (created_at AT TIME ZONE 'America/Campo_Grande')::date < ${today}
                       THEN 'failed' ELSE 'queued' END,
         confirmation_evidence=jsonb_build_object(
           'kind',CASE WHEN (created_at AT TIME ZONE 'America/Campo_Grande')::date < ${today}
                        THEN 'source_media_expired_next_day' ELSE 'source_media_invalid' END,
           'http_status',404,'confirmed_on_network',false,
           'retry_after_date',to_char(${today} + 1,'YYYY-MM-DD')),
         lease_owner=NULL,lease_until=NULL,updated_at=now()
     WHERE id=$1 AND target_key=$2 AND status='leased'
       AND publication_started_at IS NULL AND lease_owner=$3
       AND lease_generation=$4 AND lease_until>now()
     RETURNING id,status`,[id,target,who,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'MEDIA_INVALID_FENCE_REJECTED'};
 }
 if(verb==='fail'){
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
        lease_until=NULL,updated_at=now(),
        lease_owner=CASE WHEN publication_started_at IS NULL THEN NULL ELSE lease_owner END
    WHERE id=$1 AND target_key=$2 AND status IN ('leased','started')
      AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,[id,target,who,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'BROWSER_FENCE_EXPIRED'};
 }
 const pin=String(b.remote_id||''),link=String(b.confirmation_evidence?.permalink||'');
 if(!/^[0-9]{6,25}$/.test(pin)||link!=='https://br.pinterest.com/pin/'+pin+'/')
   return{ok:false,error:'BROWSER_PIN_PROOF_INVALID'};
 if(b.confirmation_evidence?.kind!=='pinterest_browser_verified_pin'||
    String(b.confirmation_evidence.verified_id||'')!==pin)
   return{ok:false,error:'BROWSER_PIN_PROOF_MISMATCH'};
 const evidence={kind:'pinterest_browser_verified_pin',verified_id:pin,
   permalink:link,route:'browser',confirmed_on_network:true};
 const rows=await query(`UPDATE cortes_publications
   SET status='confirmed',remote_id=$5,confirmation_evidence=$6::jsonb,
       lease_until=NULL,lease_owner=NULL,updated_at=now()
   WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3
     AND lease_generation=$4 AND publication_started_at IS NOT NULL
   RETURNING id,status,remote_id`,[id,target,who,gen,pin,JSON.stringify(evidence)]);
 return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'BROWSER_CONFIRM_REJECTED'};
}
// Personal member publishing is exclusively authorized by the signed main-branch
// GitHub workflow. Company Buffer workflows cannot operate on this queue.
const P_TARGET='linkedin:personal',P_OWNER='linkedin-personal:github-cloud-v1',P_LIMIT=50;
// Recover crashed leasing transactions. A post that reached 'started' may
// have been accepted externally: quarantine as UNCERTAIN, never blind-repost.
async function recoverExpiredLinkedin(targetKey){
 const evidence={kind:'expired_after_publication_started',confirmed_on_network:false};
 return await query(`UPDATE cortes_publications SET
    status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
    confirmation_evidence=CASE WHEN publication_started_at IS NULL THEN confirmation_evidence ELSE $2::jsonb END,
    lease_owner=NULL,lease_until=NULL,updated_at=now()
   WHERE target_key=$1 AND status IN ('leased','started')
     AND lease_until IS NOT NULL AND lease_until<now() RETURNING id,status`,
   [targetKey,JSON.stringify(evidence)]);
}
async function personalAction(verb,b){
 const id=String(b.id||''),owner=String(b.owner||'');
 if(verb==='lease'){
  if(b.target_key!==P_TARGET||owner!==P_OWNER)return{ok:false,error:'PERSONAL_TARGET_OWNER_INVALID'};
  await recoverExpiredLinkedin(P_TARGET);
  // A read-only permission can be unavailable to self-serve member apps.
  // Keep accepted-but-unverified items UNCERTAIN and never retry their IDs;
  // other distinct queued shorts must continue under the shared daily budget.
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const used=await query(`SELECT count(*)::int n FROM cortes_publications WHERE target_key=$1 AND status IN ('confirmed','leased','started','uncertain') AND updated_at >= ${day}`,[P_TARGET]);
  if(Number(used[0]?.n||0)>=P_LIMIT)return{ok:true,job:null,daily_limit_reached:true,limit:P_LIMIT};
  const rows=await query(`WITH picked AS (SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued' AND created_at >= ${day} ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+interval '30 minutes',updated_at=now() FROM picked WHERE p.id=picked.id AND p.status='queued' RETURNING p.*`,[P_TARGET,P_OWNER]);
  return{ok:true,job:rows[0]||null,limit:P_LIMIT};
 }
 if(!['start','fail','media-missing','accepted','confirmed'].includes(verb))return{ok:false,error:'PERSONAL_ACTION_DENIED'};
 const generation=Number(b.lease_generation);
 if(!id||owner!==P_OWNER||!Number.isInteger(generation)||generation<1)return{ok:false,error:'PERSONAL_INVALID_FENCE'};
 if(verb==='start'){
  const r=await query("UPDATE cortes_publications SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 AND lease_until>now() RETURNING id,status",[id,P_TARGET,owner,generation]);
  return r.length?{ok:true,job:r[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 if(verb==='fail'){
  const r=await query("UPDATE cortes_publications SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status IN ('leased','started') AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,P_TARGET,owner,generation]);
  return r.length?{ok:true,job:r[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 if(verb==='media-missing'){
  const evidence={kind:'source_media_http_404',account:'personal',confirmed_on_network:false};
  const rows=await query("UPDATE cortes_publications SET status='failed',confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,P_TARGET,owner,generation,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
 }
 const remote=String(b.remote_id||'');
 if(!/^urn:li:(share|ugcPost):[0-9]{8,25}$/.test(remote))return{ok:false,error:'PERSONAL_REMOTE_INVALID'};
 if(verb==='confirmed'&&(b.confirmation_evidence?.kind!=='linkedin_author_readback_verified'||b.confirmation_evidence?.verified_id!==remote||b.confirmation_evidence?.author_verified!==true))return{ok:false,error:'PERSONAL_READBACK_REQUIRED'};
 const evidence=verb==='confirmed'?b.confirmation_evidence:{kind:'linkedin_api_201_unverified',verified_id:remote,account:'personal'};
 const status=verb==='confirmed'?'confirmed':'uncertain';
 const r=await query("UPDATE cortes_publications SET status=$5,remote_id=$6,confirmation_evidence=$7::jsonb,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status,remote_id",[id,P_TARGET,owner,generation,status,remote,JSON.stringify(evidence)]);
 return r.length?{ok:true,job:r[0]}:{ok:false,error:'PERSONAL_STALE_FENCE'};
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
 const actor=action.startsWith('browser-')?
    (await authorizePinterestBrowser(request)?{role:'pinterest-browser'}:null):
    await identity(request);
 if(!actor)return answer({ok:false,error:'PUBLISHER_AUTH_UNAUTHORIZED'},401);
 let body;try{body=await request.json();}catch{return answer({ok:false,error:'INVALID_JSON'},400);}
 if(!body||typeof body!=='object'||Array.isArray(body))return answer({ok:false,error:'INVALID_BODY'},400);
 if(JSON.stringify(body).length>65536)return answer({ok:false,error:'TOO_LARGE'},413);
 try{
  if(action.startsWith('browser-')){
   if(actor.role!=='pinterest-browser')return answer({ok:false,error:'BROWSER_DEVICE_ONLY'},403);
   const out=await pinterestBrowserAction(action.slice('browser-'.length),body);
   return answer(out,out.ok?200:409);
  }
  if(action==='buffer-pending'&&actor.role==='probe')
    return answer(await bufferAction('pending',body,'linkedin'));
  if(action==='probe'){
   if(actor.role!=='probe')return answer({ok:false,error:'PROBE_WORKFLOW_ONLY'},403);
   const out=await writeProbe(body);
   return answer(out,out.ok?200:409);
  }
  if(action.startsWith('personal-')){
   if(actor.role!=='personal')return answer({ok:false,error:'PERSONAL_WORKFLOW_ONLY'},403);
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
