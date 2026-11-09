import crypto from 'node:crypto';
// Canonical CORTES ledger is Neon PostgreSQL. No local queue or Vercel dependency.
// This function never publishes media and never accepts device-PC authentication.
const AUD='https://anthares-remote-primary.vercel.app/api/cortes-queue';
const TARGETS={linkedin:'linkedin:primary',instagram:'instagram:universoanthares',pinterest:'pinterest:lucasyahn'};
const BUFFER_WORKFLOWS={linkedin:'cortes-buffer-linkedin-cloud.yml',instagram:'cortes-buffer-instagram-cloud.yml',pinterest:'cortes-buffer-pinterest-cloud.yml'};
const CLIPPER_PRODUCERS=new Set(['cortes-buffer-fanout-cloud.yml','cortes-neon-short-dispatch.yml','cortes-kwai-dispatch-refill.yml','cortes-daily.yml']);
const RUNNER_PRODUCERS=new Set(['cortes-linkedin-neon-fanout.yml','cortes-buffer-three-fanout-cloud.yml']);
const PROBE_WORKFLOWS=new Set(['cortes-queue-ha-acceptance.yml','cortes-queue-cloudflare-ha.yml']);
const LIMITS={linkedin:50,instagram:50,pinterest:25};
const BUFFER_GLOBAL_DAILY=20;
const BUFFER_LOCAL_DAY="(now() AT TIME ZONE 'America/Campo_Grande')::date";
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
// Neon HTTP SQL raw text output serializes PostgreSQL booleans as strings.
// Boolean('f') === true in JavaScript; never use truthiness for DB booleans.
const dbTrue=v=>v===true||v===1||v==='t'||v==='true'||v==='1';
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
  if(wf==='cortes-buffer-instagram-windows-fallback.yml')platform='instagram';
  if(wf==='cortes-instagram-direct-cloud.yml'){role='instagram-direct';platform='instagram';}
  else if(platform)role='buffer';
  else if(RUNNER_PRODUCERS.has(wf))role='producer';
  else if(PROBE_WORKFLOWS.has(wf))role='probe';
  else if(wf==='cortes-neon-ha-oidc-proof.yml'){role='probe';platform='linkedin';}
  else if(wf==='cortes-kwai-cloud-publisher.yml'){role='kwai-publisher';platform='kwai';}
  else if(wf==='cortes-linkedin-personal-cloud.yml'||wf==='cortes-linkedin-personal-fallback-cloud.yml'){
   // Two separate hosted execution paths share one Neon ledger, identity,
   // owner lease and quota. Neither path can replay an uncertain delivery.
   role='personal';platform='linkedin';
  }
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

// Existing physical Android executor uses an RSA key kept exclusively on
// DESKTOP-FTDK0HP. Authorize this key for Kwai actions only, never other queues.
// The key below is public; the existing private signing key stays on Windows.
const KWAI_PHYSICAL_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwqMVKLsftqOwVa5U7CWq\nksPdck2z17p1sJMbFI8Ul7YeRaayxEI3l91NApPpSr5SjNZnTnZ/lmZiowXs6tdb\nVrPPcj8Ip5tiYcuuQlZ4ItBD0cfj0KuDpBiGyWJkKrtSz89GRHePP1eI6VsiBlhG\nQSUaxQ71RjAuCBB0miPcZ58iy+G4NzOP8p3PjgCq7nfVIQqJMDbORydzPjDIgLbW\nKibXLbbvIThyanJ0wgK4fr4ciUsn67ZGsWSEYpr8A303TMXjmDyvd3TFz+9mKEUh\nZYejXgb2k/0KgIUsSlXMkXe1E7lDfKoNWmKiu3z633hmu+KpTraHn1WTf2aiRPR/\ndQIDAQAB\n-----END PUBLIC KEY-----";
async function kwaiPhysicalIdentity(request,action){
 if(!action.startsWith('kwai-')||request.method!=='POST'||
    request.headers.get('x-anthares-device')!=='DESKTOP-FTDK0HP')return null;
 const ts=String(request.headers.get('x-anthares-executor-timestamp')||'');
 const nonce=String(request.headers.get('x-anthares-executor-nonce')||'');
 const signature=String(request.headers.get('x-anthares-executor-signature')||'');
 if(!/^\d{10}$/.test(ts)||Math.abs(Date.now()/1000-Number(ts))>90||
    !/^[a-f0-9]{32}$/.test(nonce)||!/^[-A-Za-z0-9+/=]{250,700}$/.test(signature))return null;
 try{
  const raw=await request.clone().text();
  if(raw.length>65536)return null;
  const u=new URL(request.url);
  const signed=ts+'\nPOST\n'+u.pathname+u.search+'\n'+nonce+'\n'+raw;
  if(!crypto.verify('RSA-SHA256',Buffer.from(signed),KWAI_PHYSICAL_PUBLIC_KEY,
                    Buffer.from(signature,'base64')))return null;
  return {role:'kwai-physical',workflow:'physical:DESKTOP-FTDK0HP',platform:'kwai'};
 }catch{return null;}
}
// Kwai HA contract, default disabled. OIDC publisher identity and media readback
// must be proven before promoting this shared Neon queue to production.
const KWAI_TARGET='kwai:lucasrosalem';
async function kwaiAction(action,b,actor){
 if(action==='kwai-physical-repair-no-post'){
  // Recover a fresh UNCERTAIN state where the physical Android publisher
  // never sent a new post: its old October on-device anti-duplicate marker
  // returned ALREADY_ATTEMPTED. Require independent recent full public feed
  // and source-frame exclusion before restoring the same canonical job.
  if(actor.role!=='kwai-physical'||actor.workflow!=='physical:DESKTOP-FTDK0HP'||
     b.target_key!==KWAI_TARGET||b.expected_account!=='lucasrosalem')
   return{ok:false,error:'KWAI_PHYSICAL_RECOVERY_IDENTITY_REQUIRED'};
  const id=String(b.id||''),p=b.proof||{},now=Date.now();
  const start=Number(p.previous_started_at_epoch_ms),verified=Number(p.verified_at_epoch_ms);
  const marker=Number(p.native_marker_epoch_ms),scan=p.public_scan||{};
  if(!/^kwai-cortes-[A-Za-z0-9_-]{10,180}$/.test(id)||
     p.kind!=='kwai_physical_no_new_post_marker_v1'||p.job_id!==id||
     p.author_handle!=='lucasrosalem'||
     p.native_rc!==3||p.native_stdout!=='ALREADY_ATTEMPTED PUBLICATION_ATTEMPTED_UNVERIFIED'||
     !/^[a-f0-9]{64}$/.test(String(p.source_sha256||''))||
     !Number.isSafeInteger(Number(b.lease_generation))||
     !Number.isFinite(start)||!Number.isFinite(verified)||verified>now+15000||
     verified<now-1800000||!Number.isFinite(marker)||marker>start-86400000||
     Number(p.source_http_code)!==200||
     Number(scan.total_distinct_posts)<1000||
     Number(scan.oldest_post_epoch_ms)>start-86400000||
     Number(scan.newest_post_epoch_ms)<start+1800000||
     Number(scan.scanned_at_epoch_ms)<start+3600000||
     Number(p.near_public_media_matches)!==0||
     Number(p.near_candidates_total)!==Number(p.near_candidates_tested)||
     Number(p.near_candidates_total)<0||
     p.recent_attempt_posted_to_android!==false)
   return{ok:false,error:'KWAI_PHYSICAL_NO_POST_RECOVERY_PROOF_INVALID'};
  const rows=await query("SELECT id,status,lease_generation,lease_owner,"+
   "publication_started_at,confirmation_evidence FROM cortes_publications "+
   "WHERE id=$1 AND target_key=$2 LIMIT 1",[id,KWAI_TARGET]);
  if(rows.length!==1)return{ok:false,error:'KWAI_NO_POST_JOB_MISSING'};
  const r=rows[0],rawPrior=r.confirmation_evidence||{};
  const prior=typeof rawPrior==='string'?JSON.parse(rawPrior):rawPrior;
  if(r.status==='queued'&&prior.kind==='kwai_historical_verified_public_absent_v1'&&
     prior.recovered_from_no_touch===true)return{ok:true,already_resolved:true,job:{id,status:'queued'}};
  if(r.status!=='uncertain'||r.lease_owner!=null||
     Number(r.lease_generation)!==Number(b.lease_generation)||
     !r.publication_started_at||
     Math.abs(new Date(r.publication_started_at).getTime()-start)>1500||
     prior.kind!=='kwai_historical_verified_public_absent_v1'||
     prior.device_signature_verified!==true||
     prior.attested_device!=='DESKTOP-FTDK0HP'||
     prior.job_id!==id||prior.source_sha256!==p.source_sha256)
   return{ok:false,error:'KWAI_PHYSICAL_NO_POST_FENCE_OR_SOURCE_MISMATCH',checks:{status:r.status,owner_null:r.lease_owner==null,lease:Number(r.lease_generation)===Number(b.lease_generation),started:Math.abs(new Date(r.publication_started_at).getTime()-start),kind:prior.kind,source_equal:prior.source_sha256===p.source_sha256,sig:prior.device_signature_verified===true,device:prior.attested_device,job:prior.job_id===id}};
  const evidence={...p,kind:'kwai_historical_verified_public_absent_v1',
    recovered_from_no_touch:true,prior_lease_generation:Number(r.lease_generation),
    attested_device:'DESKTOP-FTDK0HP',device_signature_verified:true,
    verified_at_neon:new Date().toISOString()};
  const result=await query("UPDATE cortes_publications p SET status='queued',"+
    "lease_owner=NULL,lease_until=NULL,publication_started_at=NULL,"+
    "confirmation_evidence=$4::jsonb,updated_at=now() "+
    "WHERE p.id=$1 AND p.target_key=$2 AND p.status='uncertain' "+
    "AND p.lease_owner IS NULL AND p.lease_generation=$3 "+
    "AND abs(extract(epoch FROM (p.publication_started_at-to_timestamp($5/1000.0))))<2 "+
    "AND NOT EXISTS(SELECT 1 FROM cortes_publications d WHERE "+
    "d.target_key=$2 AND d.id<>p.id AND d.status IN "+
    "('queued','leased','started','confirmed','uncertain') AND "+
    "((d.source_id=p.source_id AND d.source_start<p.source_end "+
    "AND d.source_end>p.source_start) OR d.media_sha256=p.media_sha256)) "+
    "RETURNING p.id,p.status",
    [id,KWAI_TARGET,Number(b.lease_generation),JSON.stringify(evidence),start]);
  return result.length?{ok:true,decision:'requeue_no_android_post',job:result[0]}:
   {ok:false,error:'KWAI_NO_POST_REQUEUE_CONFLICT'};
 }
 if(action==='kwai-historical-resolve'){
  // Reconcile pre-November physical-phone attempts in the existing canonical
  // queue. Only the registered phone host can sign decisions. Public matches
  // require six matched source frames; safe retries require a complete,
  // independent scan of the public author's history and zero matches.
  if(actor.role!=='kwai-physical'||actor.workflow!=='physical:DESKTOP-FTDK0HP'||
     b.target_key!==KWAI_TARGET||b.expected_account!=='lucasrosalem')
   return{ok:false,error:'KWAI_HISTORICAL_PHYSICAL_IDENTITY_REQUIRED'};
  const id=String(b.id||''),decision=String(b.decision||''),p=b.proof||{};
  const now=Date.now(),verified=Number(p.verified_at_epoch_ms);
  const started=Number(p.previous_started_at_epoch_ms);
  if(!/^kwai-cortes-[A-Za-z0-9_-]{10,180}$/.test(id)||
     p.job_id!==id||!['confirm','requeue'].includes(decision)||
     p.schema!=='kwai-historical-reconciliation-v1'||
     p.author_handle!=='lucasrosalem'||
     !Number.isFinite(verified)||verified<now-1800000||verified>now+15000||
     !Number.isFinite(started)||started<1760000000000||started>now||
     !/^[a-f0-9]{64}$/.test(String(p.source_sha256||'')))
   return{ok:false,error:'KWAI_HISTORICAL_PROOF_INVALID'};
  const prior=await query("SELECT id,status,remote_id,confirmation_evidence,lease_owner,"+
     "lease_generation,publication_started_at FROM cortes_publications "+
     "WHERE id=$1 AND target_key=$2 LIMIT 1",[id,KWAI_TARGET]);
  if(prior.length!==1)return{ok:false,error:'KWAI_HISTORICAL_JOB_MISSING'};
  const row=prior[0];
  const oldProof=row.confirmation_evidence||{};
  if((decision==='confirm'&&row.status==='confirmed'&&
       oldProof.kind==='kwai_historical_public_video_verified_v1')||
     (decision==='requeue'&&row.status==='queued'&&
       oldProof.kind==='kwai_historical_verified_public_absent_v1'))
   return{ok:true,already_resolved:true,job:{id,status:row.status,remote_id:row.remote_id}};
  if(row.status!=='uncertain'||row.lease_owner!=='physical_android:DESKTOP-FTDK0HP'||
      !row.publication_started_at||Number(row.lease_generation)<1||
      Math.abs(new Date(row.publication_started_at).getTime()-started)>1500)
   return{ok:false,error:'KWAI_HISTORICAL_FENCE_CHANGED'};
  const proofBase={...p,attested_device:'DESKTOP-FTDK0HP',
    device_signature_verified:true,verified_at_neon:new Date().toISOString(),
    prior_lease_generation:Number(row.lease_generation)};
  if(decision==='confirm'){
   const videoId=String(p.photo_id||''),url=String(p.public_url||'');
   const scores=p.media_match?.source_best_inliers||[];
   const posted=Number(p.public_post_timestamp_ms);
   const canon='https://www.kwai.com/@lucasrosalem/video/'+videoId;
   if(!/^[0-9]{16,21}$/.test(videoId)||url!==canon||
      p.public_account!=='lucasrosalem'||
      p.media_match?.kind!=='sift_source_to_public_cdn_v1'||
      !Array.isArray(scores)||scores.length!==6||
      scores.some(n=>!Number.isInteger(n)||n<240)||
      Number(p.media_match?.qualifying_distinct_frames)!==6||
      !/^[a-f0-9]{64}$/.test(String(p.public_media_sha256||''))||
      !Number.isFinite(posted)||Math.abs(posted-started)>120000)
    return{ok:false,error:'KWAI_HISTORICAL_PUBLIC_MEDIA_MATCH_INVALID'};
   const evidence={...proofBase,kind:'kwai_historical_public_video_verified_v1',
      previously_uncertain:true};
   const rows=await query("UPDATE cortes_publications SET status='confirmed',"+
      "remote_id=$3,confirmation_evidence=$4::jsonb,lease_owner=NULL,"+
      "lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 "+
      "AND status='uncertain' AND lease_owner='physical_android:DESKTOP-FTDK0HP' "+
      "AND abs(extract(epoch FROM (publication_started_at-to_timestamp($5/1000.0))))<2 "+
      "AND NOT EXISTS(SELECT 1 FROM cortes_publications d WHERE "+
      "d.target_key=$2 AND d.id<>$1 AND d.status='confirmed' AND d.remote_id=$3) "+
      "RETURNING id,status,remote_id",
      [id,KWAI_TARGET,url,JSON.stringify(evidence),started]);
   return rows.length?{ok:true,decision,job:rows[0]}:
     {ok:false,error:'KWAI_HISTORICAL_MATCH_COLLISION_OR_STALE_FENCE'};
  }
  // Retry only where the entire public profile interval is covered, the
  // original source still exists, and no public caption or media matches.
  const scan=p.public_scan||{},from=Number(scan.oldest_post_epoch_ms),
        to=Number(scan.newest_post_epoch_ms);
  if(p.kind!=='kwai_historical_verified_public_absent_v1'||
     Number(p.source_http_code)!==200||
     Number(scan.total_distinct_posts)<1000||
     !Number.isFinite(from)||!Number.isFinite(to)||
     from>started-86400000||to<started+86400000||
     Number(p.exact_caption_matches)!==0||
     Number(p.near_public_media_matches)!==0||
     Number(p.near_candidates_tested)!==Number(p.near_candidates_total)||
     !Number.isInteger(Number(p.near_candidates_total))||
     Number(p.near_candidates_total)<0)
   return{ok:false,error:'KWAI_HISTORICAL_RETRY_NOT_PROVEN_SAFE'};
  const evidence={...proofBase,kind:'kwai_historical_verified_public_absent_v1',
     previously_uncertain:true,restored_for_first_verified_republication:true};
  const rows=await query("UPDATE cortes_publications SET status='queued',"+
     "lease_owner=NULL,lease_until=NULL,publication_started_at=NULL,"+
     "confirmation_evidence=$3::jsonb,updated_at=now() "+
     "WHERE id=$1 AND target_key=$2 AND status='uncertain' "+
     "AND lease_owner='physical_android:DESKTOP-FTDK0HP' "+
     "AND abs(extract(epoch FROM (publication_started_at-to_timestamp($4/1000.0))))<2 "+
     "AND NOT EXISTS(SELECT 1 FROM cortes_publications d WHERE "+
     "d.target_key=$2 AND d.id<>$1 AND "+
     "d.status IN ('queued','leased','started','confirmed','uncertain') AND "+
     "((d.source_id=cortes_publications.source_id AND "+
     "d.source_start<cortes_publications.source_end AND "+
     "d.source_end>cortes_publications.source_start) OR "+
     "d.media_sha256=cortes_publications.media_sha256)) "+
     "RETURNING id,status",
     [id,KWAI_TARGET,JSON.stringify(evidence),started]);
  return rows.length?{ok:true,decision,job:rows[0]}:
    {ok:false,error:'KWAI_HISTORICAL_RETRY_CONFLICT_OR_STALE_FENCE'};
 }
 if(action==='kwai-uncertain-read'){
  if(actor.role!=='kwai-publisher'||actor.workflow!=='cortes-kwai-cloud-publisher.yml')return{ok:false,error:'KWAI_READ_DENIED'};
  const rows=await query("SELECT id,source_id,source_start,source_end,media_sha256,updated_at,"+
   "payload->>'segment_id' AS segment_id,payload->>'title' AS title "+
   "FROM cortes_publications WHERE target_key=$1 AND status='uncertain' "+
   "ORDER BY source_id,source_start,id LIMIT 101",[KWAI_TARGET]);
  const eligible=await query("SELECT count(*)::int AS n FROM cortes_publications p "+
   "WHERE p.target_key=$1 AND p.status='queued' AND p.publication_started_at IS NULL "+
   "AND NOT EXISTS (SELECT 1 FROM cortes_publications d WHERE "+
   "d.target_key=$1 AND d.id<>p.id AND d.status<>'failed' AND "+
   "((d.source_id=p.source_id AND d.source_start<p.source_end AND d.source_end>p.source_start) "+
   "OR d.media_sha256=p.media_sha256) AND "+
   "(d.status IN ('leased','started','confirmed','uncertain') OR "+
   "(d.status='queued' AND (d.created_at,d.id)<(p.created_at,p.id))))",[KWAI_TARGET]);
  return{ok:true,status:rows.length?'RECONCILE_REQUIRED':'READY',target_key:KWAI_TARGET,
   records:rows.slice(0,100),truncated:rows.length>100,
   eligible_count:Number(eligible[0]?.n||0),
   safe_to_retry:false};
 }
 // Cloud refill is a distinct producer. Existing UNCERTAIN work must stay held.
 if(action==='kwai-enqueue'){
  if(actor.role!=='producer'||actor.workflow!=='cortes-kwai-dispatch-refill.yml')
   return{ok:false,error:'KWAI_PRODUCER_IDENTITY_REQUIRED'};
  // Enqueue is OIDC-producer-only. The publication switch remains enforced
  // at START, while safe new-source jobs can be prepared independently.
  const source=String(b.source_id||''),segment=String(b.segment_id||'');
  const id=String(b.id||''),media=String(b.video_url||'');
  const start=Number(b.source_start),end=Number(b.source_end);
  let u;try{u=new URL(media);}catch{}
  if(b.target_key!==KWAI_TARGET||b.account_id!=='lucasrosalem'||
    b.expected_account!=='lucasrosalem'||b.executor!=='github_hosted_android'||
    b.master_id!==source||b.duration_class!=='short'||!source||!segment||
    !u||u.protocol!=='https:'||!['anthares.us','www.anthares.us'].includes(u.hostname)||
    u.username||u.password||u.port||!u.pathname.toLowerCase().endsWith('.mp4')||
    !Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<=start||
    id!=='kwai-cortes-'+source+'-'+segment.replace(/:/g,'-')||
    b.dedupe_key!==id||b.media_sha256!==sha(source+'|'+segment+'|'+media)||
    !Number.isInteger(Number(b.cortes_attachment_id))||
    Number(b.cortes_attachment_id)<=0||!String(b.cortes_callback_token||'')||
    !/^https:\/\/(www\.)?anthares\.us\/wp-json\/anthares\/v1\/cortes\/clip-network-callback$/.test(String(b.cortes_callback_url||'')))
     return{ok:false,error:'KWAI_ENQUEUE_IDENTITY_INVALID'};
  const vals=[id,id,KWAI_TARGET,source,b.media_sha256,source,start,end,'short',JSON.stringify(b)];
  const rows=await query(
   "INSERT INTO cortes_publications "+
   "(id,dedupe_key,target_key,master_id,media_sha256,source_id,"+
   "source_start,source_end,duration_class,payload) "+
   "SELECT $1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb "+
   "WHERE NOT EXISTS (SELECT 1 FROM cortes_publications p WHERE "+
   "p.target_key=$3 AND p.source_id=$6 AND p.source_start<$8 "+
   "AND p.source_end>$7 AND p.status<>'failed') "+
   "ON CONFLICT DO NOTHING RETURNING id,target_key,status",vals);
  if(rows.length)return{ok:true,deduped:false,job:rows[0]};
  const same=await query(
   "SELECT id,target_key,status,source_id,source_start,source_end,"+
   "payload FROM cortes_publications WHERE id=$1 OR dedupe_key=$2 LIMIT 1",[id,id]);
  if(same.length){
   const j=same[0];
   if(j.target_key!==KWAI_TARGET||j.source_id!==source||
      String(j.source_start)!==String(start)||String(j.source_end)!==String(end)||
      String(j.payload?.video_url||'')!==media||
      String(j.payload?.media_sha256||'')!==String(b.media_sha256))
     return{ok:false,error:'KWAI_DEDUPE_IDENTITY_COLLISION'};
   return{ok:true,deduped:true,reason:'identity',job:j};
  }
  const overlap=await query(
   "SELECT id,target_key,status,source_id,source_start,source_end,"+
   "payload FROM cortes_publications WHERE target_key=$1 AND "+
   "source_id=$2 AND source_start<$4 AND source_end>$3 "+
   "AND status<>'failed' ORDER BY created_at LIMIT 1",
   [KWAI_TARGET,source,start,end]);
  if(overlap.length)return{ok:true,deduped:true,reason:'timeline_overlap',job:overlap[0]};
  return{ok:false,error:'KWAI_UNCERTAIN_HOLD_OR_CONCURRENT_WRITE'};
 }
 const physical=actor.role==='kwai-physical'&&actor.workflow==='physical:DESKTOP-FTDK0HP';
 const cloud=actor.role==='kwai-publisher'&&actor.workflow==='cortes-kwai-cloud-publisher.yml';
 if(!physical&&!cloud)return{ok:false,error:'KWAI_PUBLISHER_ROLE_REQUIRED'};
 if(b.target_key!==KWAI_TARGET||b.expected_account!=='lucasrosalem')
  return{ok:false,error:'KWAI_ACCOUNT_IDENTITY_MISMATCH'};
 const owner=physical?'physical_android:DESKTOP-FTDK0HP':'kwai-cloud:'+actor.workflow;
 if(action==='kwai-physical-stats'){
  if(!physical)return{ok:false,error:'KWAI_DEVICE_ONLY'};
  const rows=await query("SELECT status,count(*)::int AS n FROM cortes_publications WHERE target_key=$1 GROUP BY status",[KWAI_TARGET]);
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const usage=await query("SELECT count(*)::int AS n,max(updated_at) AS latest FROM cortes_publications WHERE target_key=$1 AND status='confirmed' AND updated_at>="+day,[KWAI_TARGET]);
  const safe=await query("SELECT count(*)::int AS n FROM cortes_publications p "+
   "WHERE p.target_key=$1 AND p.status='queued' AND p.publication_started_at IS NULL "+
   "AND NOT EXISTS (SELECT 1 FROM cortes_publications d WHERE d.target_key=$1 AND d.id<>p.id "+
   "AND d.status<>'failed' AND ((d.source_id=p.source_id AND d.source_start<p.source_end "+
   "AND d.source_end>p.source_start) OR d.media_sha256=p.media_sha256) "+
   "AND (d.status IN ('leased','started','confirmed','uncertain') OR "+
   "(d.status='queued' AND (d.created_at,d.id)<(p.created_at,p.id))))",[KWAI_TARGET]);
  return{ok:true,pending:Number(safe[0]?.n||0),confirmed_today:Number(usage[0]?.n||0),
   last_confirmed_at:usage[0]?.latest||null,states:rows};
 }
 if(action==='kwai-lease'){
  const seconds=Number(b.lease_seconds||180);
  if(!Number.isSafeInteger(seconds)||seconds<60||seconds>(physical?3600:600))
   return{ok:false,error:'KWAI_TTL_INVALID'};
  // A crashed runner can leave a lease abandoned before the irreversible
  // publish start. Requeue only leases past their fencing deadline and only
  // when publication_started_at remains NULL. STARTED / UNCERTAIN are held.
  await query("UPDATE cortes_publications SET status='queued',lease_owner=NULL,"+
   "lease_until=NULL,updated_at=now() WHERE target_key=$1 AND status='leased' "+
   "AND lease_owner=$2 AND lease_until<now() "+
   "AND publication_started_at IS NULL",[KWAI_TARGET,owner]);
  // Historical UNCERTAIN rows remain quarantined. A new master/source is
  // eligible only when no unresolved item shares its source identity, and no
  // earlier active or confirmed job overlaps its exact source interval.
  // FOR UPDATE SKIP LOCKED plus status CAS prevents dual consumers.
  const sql="WITH pick AS (SELECT p.id FROM cortes_publications p "+
   "WHERE p.target_key=$1 AND p.status='queued' AND p.publication_started_at IS NULL "+
   "AND NOT EXISTS (SELECT 1 FROM cortes_publications d WHERE "+
   "d.target_key=$1 AND d.id<>p.id AND d.status<>'failed' AND "+
   "((d.source_id=p.source_id AND d.source_start<p.source_end AND d.source_end>p.source_start) "+
   "OR d.media_sha256=p.media_sha256) AND "+
   "(d.status IN ('leased','started','confirmed','uncertain') OR "+
   "(d.status='queued' AND (d.created_at,d.id)<(p.created_at,p.id)))) "+
   "ORDER BY p.created_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1) "+
   "UPDATE cortes_publications p SET status='leased',lease_owner=$2,"+
   "lease_generation=p.lease_generation+1,"+
   "lease_until=now()+($3::integer * interval '1 second'),updated_at=now() "+
   "FROM pick WHERE p.id=pick.id AND p.status='queued' AND p.publication_started_at IS NULL "+
   "RETURNING p.id,p.target_key,p.payload,p.media_sha256,p.lease_generation,p.lease_until,p.confirmation_evidence";
  const rows=await query(sql,[KWAI_TARGET,owner,seconds]);
  return{ok:true,job:rows[0]||null,uncertain_gate:'same_source_quarantined'};
 }
 const id=String(b.id||''),gen=Number(b.lease_generation);
 if(!id||id.length>200||!Number.isSafeInteger(gen)||gen<1)
  return{ok:false,error:'KWAI_FENCE_INVALID'};
 if(action==='kwai-renew'){
  const seconds=Number(b.lease_seconds||180);
  if(!Number.isSafeInteger(seconds)||seconds<60||seconds>600)
   return {ok:false,error:'KWAI_RENEW_TTL_INVALID'};
  const rows=await query("UPDATE cortes_publications SET lease_until=GREATEST(lease_until,now()+($5::integer * interval '1 second')),updated_at=now() "+
   "WHERE id=$1 AND target_key=$2 AND status IN ('leased','started') AND lease_owner=$3 "+
   "AND lease_generation=$4 AND lease_until>now() "+
   "RETURNING id,status,lease_generation,lease_until",
   [id,KWAI_TARGET,owner,gen,seconds]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_RENEW_STALE_FENCE'};
 }
 if(action==='kwai-start'){
  if(cloud&&process.env.CORTES_KWAI_CLOUD_PUBLISH_ENABLED!=='1')
   return{ok:false,error:'KWAI_PUBLISHER_NOT_ENABLED'};
  // Two existing database triggers atomically reserve account and platform caps.
  // A second reservation here would double-count the platform:kwai quota.
  const sql="UPDATE cortes_publications p SET status='started',"+
   "publication_started_at=now(),updated_at=now() "+
   "WHERE p.id=$1 AND p.target_key=$2 AND p.status='leased' "+
   "AND p.lease_owner=$3 AND p.lease_generation=$4 AND p.lease_until>now() "+
   "AND p.publication_started_at IS NULL "+
   "RETURNING p.id,p.status,p.lease_generation";
  const rows=await query(sql,[id,KWAI_TARGET,owner,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE_OR_QUOTA'};
 }
 if(action==='kwai-confirm'){
  const proof=b.confirmation_evidence||{},remote=String(b.remote_id||'');
  if(physical){
   // The existing phone signs this request with its private RSA key.
   // Accept either a fresh direct share receipt or an independently fetched
   // public author profile, caption and matching original/public CDN frames.
   const match=proof.media_match||{},scores=match.inliers||[];
   const isPublic=proof.method==='public_profile_independent_cdn_video_frame_match';
   const verified=Number(proof.verified_at_epoch_ms);
   const observed=Number(isPublic?proof.public_post_timestamp_ms:proof.share_receipt_epoch_ms);
   const now=Date.now();
   const url=String(proof.public_url||'');
   const official=isPublic?
       /^https:\/\/www\.kwai\.com\/@lucasrosalem\/video\/[0-9]{16,21}$/.test(url):
       /^https:\/\/k\.kwai\.com\/p\/[A-Za-z0-9_-]{5,100}$/.test(url);
   if(proof.kind!=='kwai_verified_public_media_v2'||
      proof.schema!=='kwai-public-media-proof-v2'||proof.ok!==true||
      proof.job_id!==String(b.id)||proof.expected_account!=='lucasrosalem'||
      proof.actual_author_handle!=='lucasrosalem'||proof.public_url!==remote||
      !official||!/^[a-f0-9]{64}$/.test(String(proof.media_sha256||''))||
      !Array.isArray(scores)||scores.length<2||Number(scores[0])<24||
      Number(scores[1])<17||!Number.isFinite(observed)||!Number.isFinite(verified)||
      observed<=0||verified<observed||verified>now+10000||now-verified>900000||
      (isPublic&&(
        proof.official_permalink!==url||
        proof.author_verified_on_external_website!==true||
        match.source_and_public_matching_frames!==true||
        !Number.isInteger(Number(match.frames_compared))||Number(match.frames_compared)<6||
        !/^[a-f0-9]{64}$/.test(String(proof.public_media_sha256||'')))))
      return{ok:false,error:'KWAI_PHYSICAL_VERIFIED_SHARE_MEDIA_PROOF_REQUIRED'};
   const evidence={...proof,attested_device:'DESKTOP-FTDK0HP',
     device_signature_verified:true,verified_at_neon:new Date().toISOString()};
   // The public site's observed upload time must agree with our permanent
   // pre-publication STARTED fence, and this exact lease generation must own it.
   const rows=await query("UPDATE cortes_publications SET status='confirmed',"+
     "remote_id=$5,confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,"+
     "updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' "+
     "AND lease_owner=$3 AND lease_generation=$4 AND publication_started_at IS NOT NULL "+
     (isPublic?"AND abs(extract(epoch from (publication_started_at-to_timestamp($7/1000.0))))<600 ":"")+
     "RETURNING id,status,remote_id",
     isPublic?[String(b.id),KWAI_TARGET,owner,Number(b.lease_generation),remote,
                JSON.stringify(evidence),observed]:
              [String(b.id),KWAI_TARGET,owner,Number(b.lease_generation),remote,
                JSON.stringify(evidence)]);
   return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_PHYSICAL_CONFIRM_STALE_FENCE'};
  }
  let u;try{u=new URL(String(proof.public_url||''));}catch{}
  const p=u?.pathname||'',h=u?.hostname||'';
  const official=(h==='k.kwai.com'&&/^\/p\/[A-Za-z0-9_-]{5,100}$/.test(p))||
   (h==='www.kwai.com'&&/^\/@lucasrosalem\/photo\/[0-9]{5,100}$/.test(p));
  if(!u||u.protocol!=='https:'||!official||u.username||u.password||
    u.port||u.search||u.hash||p.split('/').filter(Boolean).pop()!==remote||
    proof.kind!=='kwai_account_media_readback_verified'||
    !['kwai_public_deeplink_title_and_author_profile_handle',
      'physical_profile_exact_account_timestamp_and_share_ui'].includes(proof.method)||
    proof.account!=='lucasrosalem'||proof.remote_id!==remote||
    !/^[A-Za-z0-9_-]{5,100}$/.test(remote)||
    !/^[a-f0-9]{64}$/.test(String(proof.media_sha256||'')))
   return{ok:false,error:'KWAI_PUBLIC_READBACK_REQUIRED'};

  // A URL and method are claimed by the publishing client. A separate,
  // approved identity must attest the actual external Kwai readback.
  // Missing configuration always fails closed. Keep the key out of Git/logs.
  const key=process.env.CORTES_KWAI_INDEPENDENT_ATTESTATION_KEY||'';
  const signedAt=String(proof.verified_at||'');
  const stamp=Date.parse(signedAt),delta=Date.now()-stamp;
  if(key.length<32||proof.verifier_id!=='kwai-independent-account-readback-v1'||
     !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(signedAt)||
     !Number.isFinite(stamp)||delta<(-30000)||delta>600000||
     !/^[a-f0-9]{64}$/.test(String(proof.attestation_hmac||'')))
   return{ok:false,error:'KWAI_INDEPENDENT_ATTESTATION_REQUIRED'};
  const signedFields=JSON.stringify([
   'kwai-readback-v1',id,gen,KWAI_TARGET,proof.account,remote,
   proof.public_url,proof.method,proof.media_sha256,signedAt
  ]);
  const expected=crypto.createHmac('sha256',key).update(signedFields).digest();
  const provided=Buffer.from(proof.attestation_hmac,'hex');
  if(provided.length!==expected.length||!crypto.timingSafeEqual(provided,expected))
   return{ok:false,error:'KWAI_INDEPENDENT_ATTESTATION_INVALID'};

  const evidence={...proof,attestation_scheme:'hmac-sha256',
   attestation_verified_by:'neon-cortes-queue',
   attestation_verified_at:new Date().toISOString()};
  delete evidence.attestation_hmac;
  const rows=await query("UPDATE cortes_publications SET status='confirmed',"+
   "remote_id=$5,confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,"+
   "updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' "+
   "AND lease_owner=$3 AND lease_generation=$4 "+
   "RETURNING id,status,remote_id",[id,KWAI_TARGET,owner,gen,remote,
    JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE_OR_MEDIA'};
 }
 if(action==='kwai-fail'){
  const rows=await query("UPDATE cortes_publications SET status=CASE "+
   "WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,"+
   "lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 "+
   "AND target_key=$2 AND status IN ('leased','started') "+
   "AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",
   [id,KWAI_TARGET,owner,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE'};
 }
 return{ok:false,error:'KWAI_ACTION_NOT_ALLOWED'};
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
async function instagramDirectAction(verb,b){
 const target='instagram:universoanthares';
 if(verb==='lease'){
  if(b.target_key!==target||b.owner!=='instagram-direct:github-cloud-v1')
    return {ok:false,error:'DIRECT_OWNER_INVALID'};
  // Provider quota and CORTES hard daily limit are separate; both apply.
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const used=await query(`SELECT count(*)::int AS n FROM cortes_publications
    WHERE target_key=$1 AND (
      status='confirmed' AND updated_at>=${day}
      OR publication_started_at>=${day} AND status IN ('started','uncertain','confirmed')
    )`,[target]);
  if(Number(used[0]?.n||0)>=100)return {ok:true,job:null,daily_limit_reached:true,limit:100};
  const row=await query(`WITH candidate AS (
    SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued'
    ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1
   ) UPDATE cortes_publications p SET status='leased',lease_owner=$2,
    lease_generation=p.lease_generation+1,lease_until=now()+interval '20 minutes',updated_at=now()
    FROM candidate WHERE p.id=candidate.id AND p.status='queued'
    RETURNING p.id,p.target_key,p.payload,p.duration_class,p.lease_generation`,
    [target,b.owner]);
  return {ok:true,job:row[0]||null};
 }
 const id=String(b.id||''),owner=String(b.owner||''),gen=Number(b.lease_generation);
 if(!id||owner!=='instagram-direct:github-cloud-v1'||!Number.isSafeInteger(gen)||gen<1)
  return {ok:false,error:'DIRECT_FENCE_INVALID'};
 if(verb==='start'){
  const row=await query(`UPDATE cortes_publications SET status='started',
    publication_started_at=COALESCE(publication_started_at,now()),updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3
      AND lease_generation=$4 AND lease_until>now() RETURNING id,status`,
    [id,target,owner,gen]);
  return row.length?{ok:true,job:row[0]}:{ok:false,error:'DIRECT_FENCE_STALE'};
 }
 if(verb==='missing'){
  const evidence={kind:'source_media_http_404',confirmed_on_network:false,
    quarantine_at:new Date().toISOString(),discard_policy:'qa_24h_then_qa_exhaustion_required'};
  const rows=await query(`UPDATE cortes_publications SET status='uncertain',
    confirmation_evidence=$5::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3
      AND lease_generation=$4 AND publication_started_at IS NULL RETURNING id,status`,
    [id,target,owner,gen,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'DIRECT_FENCE_STALE'};
 }
 if(verb==='fail'){
  const rows=await query(`UPDATE cortes_publications SET
    status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
    confirmation_evidence=CASE WHEN publication_started_at IS NULL THEN confirmation_evidence
      ELSE jsonb_build_object('kind','instagram_direct_submission_unverified',
         'confirmed_on_network',false,'requires_manual_reconciliation',true) END,
    lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status IN ('leased','started')
      AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,
    [id,target,owner,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'DIRECT_FENCE_STALE'};
 }
 if(verb==='confirm'){
  const link=String(b.permalink||''),remote=String(b.media_id||'');
  let u;try{u=new URL(link)}catch{return {ok:false,error:'DIRECT_PERMALINK_INVALID'}};
  if(u.protocol!=='https:'||!['instagram.com','www.instagram.com'].includes(u.hostname)
       ||!/^\/(reel|p)\/[A-Za-z0-9_-]+\/?$/.test(u.pathname)
       ||u.search||u.hash||u.username||u.password||!/^\d{6,30}$/.test(remote))
    return {ok:false,error:'DIRECT_PERMALINK_INVALID'};
  const evidence={kind:'instagram_graph_reel_permalink_verified',remote_id:remote,
    permalink:link,confirmed_on_network:true};
  const rows=await query(`UPDATE cortes_publications SET status='confirmed',
    remote_id=$5,confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3
      AND lease_generation=$4 RETURNING id,status,remote_id`,
    [id,target,owner,gen,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'DIRECT_FENCE_STALE'};
 }
 return {ok:false,error:'DIRECT_ACTION_INVALID'};
}

async function bufferAction(verb,b,platform){
 const dest=target(platform),owner='buffer-'+platform+':';
 const allowed=new Set(['lease','start','fail','media-missing','editorial-invalid','rejected','scheduled','pending','reconcile','stats','retention','cooldown','cooldown-status','policy']);
 if(!allowed.has(verb))return{ok:false,error:'UNKNOWN_BUFFER_ACTION'};
 if(verb==='cooldown'||verb==='cooldown-status'){
  if(!['pinterest','instagram','linkedin'].includes(platform))return{ok:false,error:'BUFFER_COOLDOWN_SCOPE_ONLY'};
  // Persist provider rate limits across ephemeral GitHub runners. This table
  // contains no credentials, media, or personal user data.
  await query(`CREATE TABLE IF NOT EXISTS cortes_buffer_provider_cooldowns(
     provider text PRIMARY KEY, cooldown_until timestamptz NOT NULL,
     updated_at timestamptz NOT NULL DEFAULT now())`);
  if(verb==='cooldown'){
    const seconds=Number(b.seconds);
    if(!Number.isSafeInteger(seconds)||seconds<300||seconds>3600)
       return{ok:false,error:'INVALID_COOLDOWN'};
    await query(`INSERT INTO cortes_buffer_provider_cooldowns(provider,cooldown_until,updated_at)
       VALUES($1,now()+($2::int * interval '1 second'),now()),
        ('buffer_shared',
          CASE WHEN extract(hour FROM now() AT TIME ZONE 'America/Campo_Grande')>=20
            THEN ((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande')
                 + interval '1 day') AT TIME ZONE 'America/Campo_Grande')
            ELSE now()+($2::int * interval '1 second') END,now())
       ON CONFLICT(provider) DO UPDATE SET
        cooldown_until=GREATEST(cortes_buffer_provider_cooldowns.cooldown_until,
                         EXCLUDED.cooldown_until),updated_at=now()`,[platform,seconds]);
  }
  const v=await query(`SELECT cooldown_until,cooldown_until>now() AS active
      FROM cortes_buffer_provider_cooldowns WHERE provider IN ($1,'buffer_shared')
      ORDER BY cooldown_until DESC LIMIT 1`,[platform]);
  return{ok:true,active:dbTrue(v[0]?.active),
    cooldown_until:v[0]?.cooldown_until||null,shared_provider:true};
 }
 if(verb==='policy'){
  const rows=await query(`SELECT extract(isodow FROM now() AT TIME ZONE 'America/Campo_Grande')::int AS weekday,
    (SELECT count(*)::int FROM cortes_buffer_daily_slots WHERE local_day=${BUFFER_LOCAL_DAY}) AS used,
    EXISTS(SELECT 1 FROM cortes_buffer_provider_cooldowns
      WHERE provider='buffer_shared' AND cooldown_until>now()) AS provider_blocked`);
  const weekday=Number(rows[0]?.weekday||0),used=Number(rows[0]?.used||0);
  const blocked=dbTrue(rows[0]?.provider_blocked);
  return{ok:true,enabled:weekday>=1&&weekday<=5&&!blocked,
    provider_unavailable:blocked,route_decision:blocked?'own_publisher':'buffer_if_available',
    limit:BUFFER_GLOBAL_DAILY,used,remaining:Math.max(0,BUFFER_GLOBAL_DAILY-used),
    shared_across_channels:true};
 }
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
   ORDER BY updated_at ASC LIMIT 25`,[dest]);
  return{ok:true,jobs:rows};
 }
 if(verb==='lease'){
  if(b.target_key!==dest||!String(b.owner||'').startsWith(owner))return{ok:false,error:'WRONG_QUEUE_OWNER'};
  if(platform==='linkedin')await recoverExpiredLinkedin(dest);
  const weekday=await query("SELECT extract(isodow FROM now() AT TIME ZONE 'America/Campo_Grande')::int AS n");
  if(Number(weekday[0]?.n||0)>5)return{ok:true,job:null,buffer_off_day:true};
  const activeBlock=await query("SELECT EXISTS(SELECT 1 FROM cortes_buffer_provider_cooldowns WHERE provider='buffer_shared' AND cooldown_until>now()) AS blocked");
  if(dbTrue(activeBlock[0]?.blocked))return{ok:true,job:null,provider_unavailable:true,delivery_route:'own'};
  await query("DELETE FROM cortes_buffer_daily_slots s USING cortes_publications p WHERE s.job_id=p.id AND s.local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date AND p.status='queued' AND p.publication_started_at IS NULL");
  await query(`UPDATE cortes_publications SET status='failed',lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE target_key=$1 AND status='uncertain'
      AND confirmation_evidence->>'kind'='source_media_http_404'
      AND COALESCE(NULLIF(confirmation_evidence->>'quarantine_at','')::timestamptz,updated_at)
          <= now()-interval '24 hours'
      AND confirmation_evidence @> '{"qa_recovery_exhausted":true}'::jsonb`,[dest]);
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
  const cutoffForBuffer="'1970-01-01T00:00:00Z'::timestamptz";
  const candidateSql=pinterest?`SELECT p.id FROM cortes_publications p
     WHERE p.target_key=$1 AND p.status='queued'
       AND p.payload->>'editorial_policy'='anthares_editorial_transcript_v2'
       AND (COALESCE(p.confirmation_evidence->>'kind','') <> 'buffer_typed_rejection'
         OR COALESCE((p.confirmation_evidence->>'retry_after_at')::timestamptz,now())<=now())
       AND (COALESCE(p.confirmation_evidence->>'kind','') <> 'source_media_invalid'
         OR COALESCE((p.confirmation_evidence->>'retry_after_at')::timestamptz,
                (p.confirmation_evidence->>'retry_after_date')::date AT TIME ZONE 'America/Campo_Grande',
                now()) <= now())
     ORDER BY p.created_at,p.updated_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1`:
     `SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued'
       AND created_at >= ${cutoffForBuffer}
       ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1`;
  // The reservation and lease share one statement; unique (local_day,slot)
  // prevents concurrent channels reserving more than 20 global daily slots.
  const rows=await query(`WITH picked AS (${candidateSql}),
    free_slot AS (
      SELECT n::int slot FROM generate_series(1,20) AS n
      WHERE NOT EXISTS(SELECT 1 FROM cortes_buffer_daily_slots s
        WHERE s.local_day=${BUFFER_LOCAL_DAY} AND s.slot=n)
      ORDER BY n LIMIT 1
    ),
    reserved AS (
      INSERT INTO cortes_buffer_daily_slots(local_day,slot,target_key,job_id)
      SELECT ${BUFFER_LOCAL_DAY},f.slot,$1,p.id FROM picked p CROSS JOIN free_slot f
      ON CONFLICT DO NOTHING RETURNING job_id
    )
    UPDATE cortes_publications p SET status='leased',lease_owner=$2,
      lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',
      updated_at=now()
    FROM reserved r WHERE p.id=r.job_id AND p.target_key=$1 AND p.status='queued'
    RETURNING p.id,p.target_key,p.payload,p.lease_generation,p.duration_class`,
    [dest,String(b.owner)]);
    return{ok:true,job:rows[0]||null,delivery_route:rows[0]?'buffer':undefined,buffer_global_limit:BUFFER_GLOBAL_DAILY};
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
 if(verb==='editorial-invalid'){
  // The Buffer createPost action has NOT begun. Quarantine this one leased
  // clip for transcript QA instead of returning it to the front of the queue.
  const reason=String(b.reason||'');
  if(platform!=='pinterest'||!/^CORTES_[A-Z0-9_]{5,75}$/.test(reason))
    return{ok:false,error:'EDITORIAL_PROOF_INVALID'};
  const rows=await query(`UPDATE cortes_publications
     SET status='queued', lease_owner=NULL,lease_until=NULL,updated_at=now(),
       payload=jsonb_set(payload,'{editorial_policy}',to_jsonb('requires_transcript_qa'::text),true),
       confirmation_evidence=jsonb_build_object(
          'kind','editorial_invalid_qa','reason',$5::text,
          'confirmed_on_network',false,
          'detected_at',to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
     WHERE id=$1 AND target_key=$2 AND status='leased' AND remote_id IS NULL
       AND publication_started_at IS NULL AND lease_owner=$3
       AND lease_generation=$4 AND lease_until>now()
     RETURNING id,status`,[id,dest,who,fence,reason]);
  if(rows.length)
    await query("DELETE FROM cortes_buffer_daily_slots WHERE job_id=$1 AND target_key=$2 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[id,dest]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'EDITORIAL_INVALID_FENCE_REJECTED'};
 }
 if(verb==='rejected'){
  // A typed Buffer MutationError is an explicit rejection, not a transport
  // timeout. The remote action returned NO post. Requeue with backoff while
  // preserving all evidence and queue CAS protections.
  const reason=String(b.reason||'');
  if(platform!=='pinterest'||!['BOARD','MEDIA','METADATA','QUOTA','PERMISSION','UNCLASSIFIED'].includes(reason))
    return{ok:false,error:'BUFFER_REJECTED_PROOF_INVALID'};
  const rows=await query(`UPDATE cortes_publications
    SET status='queued', publication_started_at=NULL,
      lease_owner=NULL,lease_until=NULL,updated_at=now(),
      confirmation_evidence=jsonb_build_object(
        'kind','buffer_typed_rejection','classification',$5::text,
        'retry_after_at',to_char((now()+interval '120 minutes') AT TIME ZONE 'UTC',
                  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'confirmed_on_network',false)
    WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4
      AND status='started' AND remote_id IS NULL AND lease_until>now()
    RETURNING id,status`,[id,dest,who,fence,reason]);
  if(rows.length)
    await query("DELETE FROM cortes_buffer_daily_slots WHERE job_id=$1 AND target_key=$2 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[id,dest]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'BUFFER_REJECTED_FENCE_REJECTED'};
 }
 if(verb==='fail'){
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
      lease_until=NULL,updated_at=now(),lease_owner=CASE WHEN publication_started_at IS NULL THEN NULL ELSE lease_owner END
    WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4 AND status IN ('leased','started')
    RETURNING id,status`,[id,dest,who,fence]);
  if(rows[0]?.status==='queued')
    await query("DELETE FROM cortes_buffer_daily_slots WHERE job_id=$1 AND target_key=$2 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[id,dest]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'STALE_FENCE'};
 }
 if(verb==='media-missing'){
  if(platform==='pinterest'){
    const first="COALESCE((confirmation_evidence->>'first_detected_at')::timestamptz,now())";
    const rows=await query(`UPDATE cortes_publications
      SET status=CASE WHEN now() >= ${first} + interval '24 hours'
                THEN 'failed' ELSE 'queued' END,
        confirmation_evidence=jsonb_build_object(
          'kind',CASE WHEN now() >= ${first} + interval '24 hours'
               THEN 'source_media_expired_24h' ELSE 'source_media_invalid' END,
          'http_status',404,'confirmed_on_network',false,
          'first_detected_at',to_char((${first}) AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
          'expires_at',to_char((${first} + interval '24 hours') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
          'retry_after_at',to_char((now()+interval '90 minutes') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
        lease_until=NULL,lease_owner=NULL,updated_at=now()
      WHERE id=$1 AND target_key=$2 AND status='leased'
        AND publication_started_at IS NULL AND lease_owner=$3
        AND lease_generation=$4 AND lease_until>now()
      RETURNING id,status,confirmation_evidence`,[id,dest,who,fence]);
    if(rows.length)
      await query("DELETE FROM cortes_buffer_daily_slots WHERE job_id=$1 AND target_key=$2 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[id,dest]);
    return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PINTEREST_MEDIA_MISSING_FENCE_REJECTED'};
  }
  const evidence={kind:'source_media_http_404',account:dest,confirmed_on_network:false,quarantine_at:new Date().toISOString(),discard_policy:'qa_24h_then_qa_exhaustion_required'};
  const rows=await query(`UPDATE cortes_publications SET status='uncertain',
      confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now()
      WHERE id=$1 AND target_key=$2 AND status='leased'
        AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status`,
      [id,dest,who,fence,JSON.stringify(evidence)]);
  if(rows.length)
    await query("DELETE FROM cortes_buffer_daily_slots WHERE job_id=$1 AND target_key=$2 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[id,dest]);
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
 if(!['lease','start','fail','confirm','stats','media-invalid','metadata-pending','metadata-enrich','qa-media-pending','qa-media-result'].includes(verb))return{ok:false,error:'BROWSER_ACTION_DENIED'};
 if(verb==='stats'){
  const rows=await query('SELECT status,count(*)::int n FROM cortes_publications WHERE target_key=$1 GROUP BY status',[target]);
  return{ok:true,target_key:target,counts:Object.fromEntries(rows.map(x=>[x.status,Number(x.n)]))};
 }
 if(b.target_key&&b.target_key!==target)return{ok:false,error:'WRONG_TARGET'};
 if(String(b.owner||'')!==who)return{ok:false,error:'WRONG_BROWSER_OWNER'};
 if(verb==='qa-media-pending'){
   const rows=await query(`SELECT id,payload->>'media_url' AS media_url,
      confirmation_evidence->>'first_detected_at' AS first_detected_at,
      confirmation_evidence->>'expires_at' AS expires_at
      FROM cortes_publications WHERE target_key=$1 AND status='queued'
        AND confirmation_evidence->>'kind'='source_media_invalid'
        AND publication_started_at IS NULL AND remote_id IS NULL
        AND (confirmation_evidence->>'first_detected_at' IS NULL OR
             COALESCE((confirmation_evidence->>'retry_after_at')::timestamptz,now())<=now())
      ORDER BY updated_at,id LIMIT 20`,[target]);
   return{ok:true,jobs:rows};
 }
 if(verb==='qa-media-result'){
   // The trusted QA device HEAD-checked the exact permitted media URL.
   const id=String(b.id||''),src=String(b.media_url||'');
   const code=Number(b.http_status);
   if(!/^cortes-fanout-pinterest-[a-f0-9]{32}$/.test(id)||
      !/^https:\/\/anthares\.us\/wp-content\/uploads\/anthares-clips\/[^?#]+\.mp4$/.test(src)||
      ![200,404].includes(code))
       return{ok:false,error:'PINTEREST_QA_MEDIA_PROOF_INVALID'};
   const first="COALESCE((confirmation_evidence->>'first_detected_at')::timestamptz,now())";
   const rows=await query(`UPDATE cortes_publications
       SET status=CASE WHEN $3::int=404 AND now()>=${first}+interval '24 hours'
                          THEN 'failed' ELSE 'queued' END,
       confirmation_evidence=CASE WHEN $3::int=200
           THEN jsonb_build_object('kind','source_media_recovered',
                                   'confirmed_on_network',false)
           ELSE jsonb_build_object(
             'kind',CASE WHEN now()>=${first}+interval '24 hours'
                  THEN 'source_media_expired_24h' ELSE 'source_media_invalid' END,
             'http_status',404,'confirmed_on_network',false,
             'first_detected_at',to_char((${first}) AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
             'expires_at',to_char((${first}+interval '24 hours') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
             'retry_after_at',to_char((LEAST(now()+interval '90 minutes',
                                    ${first}+interval '24 hours')) AT TIME ZONE 'UTC',
                                    'YYYY-MM-DD"T"HH24:MI:SS"Z"')) END,
       updated_at=now()
       WHERE id=$1 AND target_key=$2 AND status='queued'
         AND publication_started_at IS NULL AND remote_id IS NULL
         AND payload->>'media_url'=$4
         AND confirmation_evidence->>'kind'='source_media_invalid'
       RETURNING id,status,confirmation_evidence`,[id,target,code,src]);
   return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PINTEREST_QA_MEDIA_CAS_REJECTED'};
 }

 if(verb==='metadata-pending'){
  // Read-only source titles and segment locators. No client can lease/publish.
  const rows=await query(`SELECT id,payload->>'media_url' AS media_url,
     payload->>'title' AS source_title,payload->>'segment_id' AS segment_id,
     payload->>'source_start' AS source_start,
     payload->>'duration_seconds' AS duration_seconds,
     payload->>'editorial_policy' AS editorial_policy
     FROM cortes_publications
     WHERE target_key=$1 AND status='queued'
       AND publication_started_at IS NULL AND remote_id IS NULL
       AND payload->>'segment_id' IS NOT NULL
       AND COALESCE(payload->>'editorial_policy','') <> 'anthares_editorial_transcript_v2'
       AND COALESCE(confirmation_evidence->>'kind','') <> 'source_media_invalid'
       AND ($2::text='' OR id>$2)
     ORDER BY id LIMIT 4`,[target,String(b.after_id||'')]);
  return{ok:true,jobs:rows};
 }
 if(verb==='metadata-enrich'){
  const id=String(b.id||''),title=String(b.title||'').trim();
  const description=String(b.description||'').trim();
  const keywords=b.keywords,hashtags=b.hashtags;
  const fingerprint=String(b.transcript_hash||'');
  const segment=String(b.segment_id||''),sourceTitle=String(b.original_title||'');
  if(!/^cortes-fanout-pinterest-[a-f0-9]{32}$/.test(id)||
     !/^[a-f0-9]{64}$/.test(fingerprint)||
     !/^g[0-9]+:[A-Za-z0-9_-]+:[0-9]+:[0-9]+$/.test(segment)||
     !title.endsWith(' ● Universo Anthares')||title.length<40||title.length>100||
     title===sourceTitle+' ● Universo Anthares'||
     description.length<70||description.length>500||
     !description.includes('www.anthares.us')||
     !Array.isArray(keywords)||keywords.length<3||keywords.length>12||
     !keywords.every(x=>typeof x==='string'&&x.trim().length>=3&&x.length<=65)||
     !Array.isArray(hashtags)||hashtags.length<2||hashtags.length>12||
     !hashtags.every(x=>typeof x==='string'&&/^#[\p{L}0-9_]{2,40}$/u.test(x))||
     !sourceTitle||sourceTitle.length>190)
       return{ok:false,error:'PINTEREST_STRATEGIC_TITLE_PROOF_INVALID'};
  const patch={title,video_title:title,description,text:description,
       keywords,hashtags,editorial_policy:'anthares_editorial_transcript_v2',
       editorial_transcript_hash:fingerprint,editorial_provenance:'whisper_local_ollama'};
  const row=await query(`UPDATE cortes_publications p
      SET payload=p.payload || $5::jsonb,updated_at=now(),
          confirmation_evidence=CASE WHEN p.confirmation_evidence->>'kind'='editorial_invalid_qa'
            THEN NULL ELSE p.confirmation_evidence END
      WHERE id=$1 AND target_key=$2 AND status='queued'
        AND publication_started_at IS NULL AND remote_id IS NULL
        AND p.payload->>'segment_id'=$3
        AND p.payload->>'title'=$4
        AND COALESCE(p.payload->>'editorial_policy','') <> 'anthares_editorial_transcript_v2'
      RETURNING id,status,payload->>'title' AS title`,
      [id,target,segment,sourceTitle,JSON.stringify(patch)]);
  return row.length?{ok:true,job:row[0]}:{ok:false,error:'PINTEREST_STRATEGIC_METADATA_CAS_REJECTED'};
 }

 if(verb==='lease'){
  // Recover leases abandoned by crashed local workers. Never retry a video
  // after publication started: it must remain UNCERTAIN for independent QA.
  await query(`UPDATE cortes_publications SET
     status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,
     lease_owner=NULL,lease_until=NULL,updated_at=now(),
     confirmation_evidence=CASE WHEN publication_started_at IS NULL THEN confirmation_evidence
       ELSE jsonb_build_object('kind','pinterest_expired_after_start',
                              'confirmed_on_network',false) END
     WHERE target_key=$1 AND status IN ('leased','started')
       AND lease_until < now()`,[target]);
  // Repair only prematurely discarded 404 items from the previous deployment:
  // they still have an entire next calendar day to recover their source media.
  await query(`UPDATE cortes_publications SET status='queued',lease_owner=NULL,
     lease_until=NULL,updated_at=now(),confirmation_evidence=jsonb_build_object(
       'kind','source_media_invalid','http_status',404,
       'confirmed_on_network',false,
       'retry_after_at',to_char((now()+interval '90 minutes') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
     WHERE target_key=$1 AND status='failed' AND remote_id IS NULL
       AND publication_started_at IS NULL
       AND confirmation_evidence->>'kind'='source_media_expired_next_day'
       AND (created_at AT TIME ZONE 'America/Campo_Grande')::date =
          (now() AT TIME ZONE 'America/Campo_Grande')::date - 1`,[target]);
  const cap=await query("SELECT reserved FROM cortes_daily_publication_budget WHERE target_key=$1 AND local_day=(now() AT TIME ZONE 'America/Campo_Grande')::date",[target]);
  if(Number(cap[0]?.reserved||0)>=100)return{ok:true,job:null,daily_limit_reached:true,delivery_route:'browser'};
  // A daily queue can carry work through the following local calendar day only.
  // On day 3, unposted queued items are logically discarded, never sent.
  const localDay="(now() AT TIME ZONE 'America/Campo_Grande')::date";
  const expired={kind:'pinterest_expired_after_next_day',confirmed_on_network:false};
  await query(`UPDATE cortes_publications SET status='failed',
     confirmation_evidence=$2::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now()
     WHERE target_key=$1 AND status='queued'
       AND (created_at AT TIME ZONE 'America/Campo_Grande')::date < ${localDay} - 1
       AND COALESCE(confirmation_evidence->>'kind','') <> 'source_media_invalid'`,
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
     AND p.payload->>'editorial_policy'='anthares_editorial_transcript_v2'
     AND ((p.created_at AT TIME ZONE 'America/Campo_Grande')::date
       BETWEEN (now() AT TIME ZONE 'America/Campo_Grande')::date - 1
         AND (now() AT TIME ZONE 'America/Campo_Grande')::date
       OR p.confirmation_evidence->>'kind'='source_media_invalid')
     AND ( (p.created_at AT TIME ZONE 'America/Campo_Grande')::date <
              (now() AT TIME ZONE 'America/Campo_Grande')::date
           OR r.ordinal > CASE WHEN r.weekday IN (1,2) THEN 15 ELSE 14 END
           OR extract(hour FROM now() AT TIME ZONE 'America/Campo_Grande') >= 21 )
     AND ( COALESCE(p.confirmation_evidence->>'kind','') <> 'source_media_invalid'
           OR COALESCE((p.confirmation_evidence->>'retry_after_at')::timestamptz,
               (p.confirmation_evidence->>'retry_after_date')::date AT TIME ZONE 'America/Campo_Grande',
               now()) <= now() )
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
  // Count exactly 24 consecutive hours from the FIRST observed HTTP 404,
  // never from local midnight, created_at or the most recent retry.
  const first="COALESCE((confirmation_evidence->>'first_detected_at')::timestamptz,now())";
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN now() >= ${first} + interval '24 hours'
             THEN 'failed' ELSE 'queued' END,
      confirmation_evidence=jsonb_build_object(
       'kind',CASE WHEN now() >= ${first} + interval '24 hours'
                     THEN 'source_media_expired_24h' ELSE 'source_media_invalid' END,
       'http_status',404,'confirmed_on_network',false,
       'first_detected_at',to_char((${first}) AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
       'expires_at',to_char((${first} + interval '24 hours') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
       'retry_after_at',to_char((now()+interval '90 minutes') AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
      lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='leased'
      AND publication_started_at IS NULL AND lease_owner=$3
      AND lease_generation=$4 AND lease_until>now()
    RETURNING id,status,confirmation_evidence`,[id,target,who,gen]);
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
const LINKEDIN_EXCEPTION_START="(CASE WHEN (now() AT TIME ZONE 'America/Campo_Grande') >= TIMESTAMP '2026-10-21 22:45:00' AND (now() AT TIME ZONE 'America/Campo_Grande') < TIMESTAMP '2026-10-22 05:00:00' THEN (TIMESTAMP '2026-10-21 00:00:00' AT TIME ZONE 'America/Campo_Grande') ELSE (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande') END)";
async function personalAction(verb,b){
 const id=String(b.id||''),owner=String(b.owner||'');
 if(verb==='lease'){
  if(b.target_key!==P_TARGET||owner!==P_OWNER)return{ok:false,error:'PERSONAL_TARGET_OWNER_INVALID'};
  await recoverExpiredLinkedin(P_TARGET);
  await query(`UPDATE cortes_publications SET status='failed',lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE target_key=$1 AND status='uncertain'
      AND confirmation_evidence->>'kind'='source_media_http_404'
      AND COALESCE(NULLIF(confirmation_evidence->>'quarantine_at','')::timestamptz,updated_at)
          <= now()-interval '24 hours'
      AND confirmation_evidence @> '{"qa_recovery_exhausted":true}'::jsonb`,[P_TARGET]);
  // A read-only permission can be unavailable to self-serve member apps.
  // Keep accepted-but-unverified items UNCERTAIN and never retry their IDs;
  // other distinct queued shorts must continue under the shared daily budget.
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const used=await query(`SELECT count(*)::int n FROM cortes_publications WHERE target_key=$1 AND status IN ('confirmed','leased','started','uncertain') AND updated_at >= ${day}`,[P_TARGET]);
  if(Number(used[0]?.n||0)>=P_LIMIT)return{ok:true,job:null,daily_limit_reached:true,limit:P_LIMIT};
  const rows=await query(`WITH picked AS (SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued' ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+interval '30 minutes',updated_at=now() FROM picked WHERE p.id=picked.id AND p.status='queued' RETURNING p.*`,[P_TARGET,P_OWNER]);
  return{ok:true,job:rows[0]||null,limit:P_LIMIT};
 }
 if(verb==='pending'){
  const rows=await query("SELECT id,remote_id,confirmation_evidence FROM cortes_publications WHERE target_key=$1 AND status='uncertain' AND confirmation_evidence->>'kind'='linkedin_api_201_unverified' AND remote_id IS NOT NULL ORDER BY updated_at,id LIMIT 5",[P_TARGET]);
  return{ok:true,jobs:rows};
 }
 if(verb==='reconcile-public'){
  const remote=String(b.remote_id||'');
  if(!id||!/^urn:li:(ugcPost|share):[0-9]{8,25}$/.test(remote)||b.public_status!==200||b.control_status!==404||b.proof_kind!=='linkedin_public_embed_head')return{ok:false,error:'PERSONAL_PUBLIC_PROOF_INVALID'};
  const evidence={kind:'linkedin_public_embed_http200',verified_id:remote,oauth_author_at_creation:true,public_embed_status:200,control_embed_status:404,permalink:'https://www.linkedin.com/embed/feed/update/'+remote};
  const rows=await query("UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$4::jsonb,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id=$3 AND confirmation_evidence->>'kind'='linkedin_api_201_unverified' RETURNING id,status,remote_id",[id,P_TARGET,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'PERSONAL_PUBLIC_RECONCILE_STALE'};
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
  const evidence={kind:'source_media_http_404',account:'personal',confirmed_on_network:false,quarantine_at:new Date().toISOString(),discard_policy:'qa_24h_then_qa_exhaustion_required'};
  const rows=await query("UPDATE cortes_publications SET status='uncertain',confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,P_TARGET,owner,generation,JSON.stringify(evidence)]);
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
     // Queue availability/OIDC fences do not certify SQL role isolation.
     // Real Neon catalog audit (2026-10-24): RLS disabled and runtime roles bypass it.
     network_isolation:false,rls_attested:false,
     isolation_status:'UNPROVEN_SQL_ROLE_AND_RLS_SCOPE',counts:r},200);
  }catch{return answer({ok:false,backend:'neon-functions-cortes',database_ok:false},503);}
 }
 if(request.method==='GET'&&action==='round-health'){
  try{
   const rows=await query(`SELECT target_key,status,count(*)::int AS n FROM cortes_publications
      WHERE created_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande')
                            AT TIME ZONE 'America/Campo_Grande')
        AND target_key IN ('kwai:lucasrosalem','linkedin:primary','linkedin:personal',
                           'instagram:universoanthares','pinterest:lucasyahn',
                           'threads:universoanthares')
      GROUP BY target_key,status`);
   const sourceRows=await query(`SELECT count(*)::int AS total
      FROM cortes_publications
      WHERE target_key='kwai:lucasrosalem'
        AND created_at >= (date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande')
                            AT TIME ZONE 'America/Campo_Grande')`);
   // This historical 'master' counter measures Kwai enqueue, not WordPress
   // production. Expose the distinction; do not declare zero source masters
   // merely because one platform has no new items.
   const kwaiEnqueued=Number(sourceRows[0]?.total||0);
   const otherEnqueued=rows.reduce((total,row)=>total+(
      row.target_key==='kwai:lucasrosalem'?0:Number(row.n||0)),0);
   const allEnqueued=kwaiEnqueued+otherEnqueued;
   const producerSignal=allEnqueued>0?'downstream_items_detected':'no_downstream_items';
   return answer({ok:true,backend:'neon-functions-cortes',
      round_timezone:'America/Campo_Grande',
      today_master_count:kwaiEnqueued,
      today_master_count_scope:'kwai:lucasrosalem enqueue only',
      today_any_destination_count:allEnqueued,
      producer_status:'unverified_by_queue',
      producer_signal:producerSignal,
      today_destinations:rows.map(r=>({target_key:r.target_key,status:r.status,n:Number(r.n)})),
      stalled_daily_round:kwaiEnqueued===0,
      stalled_daily_distribution:allEnqueued===0},200);
  }catch{return answer({ok:false,error:'ROUND_HEALTH_DATABASE_UNAVAILABLE'},503);}
 }
 if(request.method!=='POST')return answer({ok:false,error:'NOT_FOUND'},404);
 if(Number(request.headers.get('content-length')||0)>65536)return answer({ok:false,error:'TOO_LARGE'},413);
 const actor=action.startsWith('browser-')?
    (await authorizePinterestBrowser(request)?{role:'pinterest-browser'}:null):
    (action.startsWith('kwai-')?(await kwaiPhysicalIdentity(request,action))||await identity(request):await identity(request));
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
  if(action.startsWith('kwai-')){
   const out=await kwaiAction(action,body,actor);
   return answer(out,out.ok?200:out.error==='KWAI_PUBLISHER_NOT_ENABLED'?423:409);
  }
  if(action==='enqueue'){
   if(actor.role!=='producer')return answer({ok:false,error:'PRODUCER_ONLY'},403);
   if(actor.workflow==='cortes-linkedin-neon-fanout.yml'&&body.platform!=='linkedin')
       return answer({ok:false,error:'WORKFLOW_DESTINATION_MISMATCH'},403);
   return answer(await enqueue(body));
  }
  if(action.startsWith('instagram-direct-')){
   if(actor.role!=='instagram-direct')return answer({ok:false,error:'DIRECT_WORKER_ONLY'},403);
   const out=await instagramDirectAction(action.slice('instagram-direct-'.length),body);
   return answer(out,out.ok?200:409);
  }
  if(action.startsWith('buffer-')){
   if(actor.role!=='buffer')return answer({ok:false,error:'BUFFER_WORKER_ONLY'},403);
   const out=await bufferAction(action.slice(7),body,actor.platform);
   return answer(out,out.ok?200:409);
  }
  return answer({ok:false,error:'NOT_FOUND'},404);
 }catch{return answer({ok:false,error:'QUEUE_BACKEND_UNAVAILABLE'},503);}
}};
