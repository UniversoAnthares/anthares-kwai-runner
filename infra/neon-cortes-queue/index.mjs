import crypto from 'node:crypto';
import {kwaiPersistentCloudIdentity,localBlockedByCloudCutover} from './kwai-persistent-cloud-identity.mjs';
import {deriveKwaiPacing,KWAI_PACING_VERSION} from './kwai-pacing-policy.mjs';
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
  else if(wf==='cortes-linkedin-company-direct-cloud.yml'){role='linkedin-company';platform='linkedin';}
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
 }else if(repo===CLIPPER&&wf==='cortes-instagram-authenticated-scan.yml'){role='instagram-profile';platform='instagram';}
 else if(repo===CLIPPER&&CLIPPER_PRODUCERS.has(wf))role='producer';
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
// KW-09: device-specific bearer for the existing secondary Kwai queue only.
const KWAI_MOBILE_TOKEN_HASH='e67ce56a65791266af49f5318a85d35d8b78fcfcbf5fcb41ae0d4ae155da031e';
// KW-09: independent, device-bound authorization for the primary account.
// Store only a SHA-256 digest; the random token exists solely on the Redmi 9.
const KWAI_MOBILE_PRIMARY_TOKEN_HASH='7dc4d0485f8472ac618ba000bad92739762e0cdb3c07c4514fd8df859f0740f8';
// Additional device-local authorization for the Macrodroid primary publisher.
const KWAI_MOBILE_PRIMARY_MACRO_HASH='7a4db5fb3429c7faf96d9f72f8e3588b5dc4393054c40f0004fc9b8792e7612c';
// Android-local credential generated by MacroDroid via the existing HID control (no key transfer).
const KWAI_MOBILE_PRIMARY_ENROLLED_HASH='769f27f182554e81efc6b304b075aa83fb5e7f3e643d9c49058fea3fca35f724';
async function kwaiMobileIdentity(request,action){
 if(request.method!=='POST'||!['kwai-physical-stats','kwai-lease','kwai-renew','kwai-start','kwai-confirm','kwai-fail'].includes(action))return null;
 const m=/^Bearer ([A-Za-z0-9_-]{43})$/.exec(request.headers.get('authorization')||'');
 if(!m)return null;
 const actual=Buffer.from(sha(m[1]),'hex');
 const secondary=Buffer.from(KWAI_MOBILE_TOKEN_HASH,'hex');
 const primary=Buffer.from(KWAI_MOBILE_PRIMARY_TOKEN_HASH,'hex');
 const primaryMacro=Buffer.from(KWAI_MOBILE_PRIMARY_MACRO_HASH,'hex');
 const primaryEnrolled=Buffer.from(KWAI_MOBILE_PRIMARY_ENROLLED_HASH,'hex');
 if(actual.length!==32)return null;
 if(crypto.timingSafeEqual(actual,secondary))
  return {role:'kwai-mobile',workflow:'mobile:M2004J19C:universoanthares',platform:'kwai'};
 if(crypto.timingSafeEqual(actual,primary)||crypto.timingSafeEqual(actual,primaryMacro)||crypto.timingSafeEqual(actual,primaryEnrolled))
  return {role:'kwai-mobile-primary',workflow:'mobile:M2004J19C:lucasrosalem',platform:'kwai'};
 return null;
}
// Kwai HA contract, default disabled. OIDC publisher identity and media readback
// must be proven before promoting this shared Neon queue to production.
const KWAI_TARGET='kwai:lucasrosalem';
async function kwaiAction(action,b,actor){
 if(b.target_key==='kwai:universoanthares')return kwaiSecondaryAction(action,b,actor);
 if(action==='kwai-unproven')return kwaiUnprovenAction(b,actor,'kwai:lucasrosalem');
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
   "publication_started_at,"+
   "confirmation_evidence->>'kind' AS proof_kind,"+
   "confirmation_evidence->>'job_id' AS proof_job,"+
   "confirmation_evidence->>'source_sha256' AS proof_sha,"+
   "confirmation_evidence->>'attested_device' AS proof_device,"+
   "confirmation_evidence->>'device_signature_verified' AS proof_signed "+
   "FROM cortes_publications WHERE id=$1 AND target_key=$2 LIMIT 1",[id,KWAI_TARGET]);
  if(rows.length!==1)return{ok:false,error:'KWAI_NO_POST_JOB_MISSING'};
  const r=rows[0],prior={kind:r.proof_kind,job_id:r.proof_job,
   source_sha256:r.proof_sha,attested_device:r.proof_device,
   device_signature_verified:dbTrue(r.proof_signed)};
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
 const persistentCloud=actor.role==='kwai-persistent-cloud'&&actor.workflow==='cloud:android:redroid';
 const mobilePrimary=actor.role==='kwai-mobile-primary'&&actor.workflow==='mobile:M2004J19C:lucasrosalem';
 if(!physical&&!cloud&&!mobilePrimary&&!persistentCloud)return{ok:false,error:'KWAI_PUBLISHER_ROLE_REQUIRED'};
 if(localBlockedByCloudCutover(actor,action))return{ok:false,error:'KWAI_LOCAL_CUTOVER_ACTIVE'};
 if(b.target_key!==KWAI_TARGET||b.expected_account!=='lucasrosalem')
  return{ok:false,error:'KWAI_ACCOUNT_IDENTITY_MISMATCH'};
 const owner=physical?'physical_android:DESKTOP-FTDK0HP':mobilePrimary?'mobile_android:M2004J19C:lucasrosalem':'kwai-cloud:'+actor.workflow;
 if(action==='kwai-physical-stats'){
  if(!physical&&!mobilePrimary)return{ok:false,error:'KWAI_DEVICE_ONLY'};
  const rows=await query("SELECT status,count(*)::int AS n FROM cortes_publications WHERE target_key=$1 GROUP BY status",[KWAI_TARGET]);
  const pacing=await kwaiDeadlinePacing(KWAI_TARGET,100);
  return {ok:true,...pacing,states:rows};
 }
 if(action==='kwai-lease'){
  const pacing=await kwaiDeadlinePacing(String(b.target_key||''),100);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
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
   // Atomic start fence: even a lease issued by an older runtime cannot
   // start outside the owner's 06:00–23:00 operational window.
   "AND (now() AT TIME ZONE 'America/Campo_Grande')::time >= time '06:00' "+
   "AND (now() AT TIME ZONE 'America/Campo_Grande')::time < time '23:00' "+
   "RETURNING p.id,p.status,p.lease_generation";
  const rows=await query(sql,[id,KWAI_TARGET,owner,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE_OR_QUOTA'};
 }
 if(action==='kwai-confirm'){
  if(mobilePrimary){
   // The Android returns an official in-app Kwai share URL after pressing Publish.
   // Resolve it independently on Neon; bind author, job, generation and source
   // identity, and reject any URL already confirmed for a different job.
   const short=String(b.remote_id||''),proof=b.confirmation_evidence||{};
   const captured=Date.parse(String(proof.receipt_captured_at||''));
   const now=Date.now();
   if(!/^https:\/\/k\.kwai\.com\/p\/[A-Za-z0-9_-]{5,100}$/.test(short)||
      proof.kind!=='kwai-mobile-official-share-v1'||proof.job_id!==id||
      proof.account!=='lucasrosalem'||proof.share_url!==short||
      !/^[a-f0-9]{64}$/.test(String(proof.media_sha256||''))||
      !Number.isFinite(captured)||captured<now-900000||captured>now+15000)
    return{ok:false,error:'KWAI_PRIMARY_MOBILE_OFFICIAL_RECEIPT_REQUIRED'};
   const existing=await query("SELECT status,media_sha256,publication_started_at FROM cortes_publications WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4 LIMIT 1",
    [id,KWAI_TARGET,owner,gen]);
   if(existing.length!==1||existing[0].status!=='started'||
      existing[0].media_sha256!==proof.media_sha256||
      !existing[0].publication_started_at||
      captured<new Date(existing[0].publication_started_at).getTime()-30000)
    return{ok:false,error:'KWAI_PRIMARY_MOBILE_SOURCE_FENCE_INVALID'};
   let actual;
   try{
    const response=await fetch(short,{redirect:'follow',
      headers:{'User-Agent':'Mozilla/5.0'},signal:AbortSignal.timeout(15000)});
    if(!response.ok)return{ok:false,error:'KWAI_PRIMARY_MOBILE_PUBLIC_LINK_UNAVAILABLE'};
    actual=new URL(response.url);
   }catch{return{ok:false,error:'KWAI_PRIMARY_MOBILE_PUBLIC_LINK_UNAVAILABLE'};}
   const match=/^\/@lucasrosalem\/video\/([0-9]{16,21})$/.exec(actual.pathname);
   const photo=actual.searchParams.get('photoId'),author=actual.searchParams.get('authorKwaiId');
   if(actual.protocol!=='https:'||actual.host!=='www.kwai.com'||!match||
      (photo&&photo!==match[1])||(author&&author!=='lucasrosalem'))
    return{ok:false,error:'KWAI_PRIMARY_MOBILE_PUBLIC_ACCOUNT_MISMATCH'};
   const canonical='https://www.kwai.com/@lucasrosalem/video/'+match[1];
   const evidence={kind:'kwai_primary_mobile_official_receipt_v1',
     account:'lucasrosalem',job_id:id,source_sha256:proof.media_sha256,
     short_url:short,public_url:canonical,receipt_captured_at:proof.receipt_captured_at,
     receipt_resolved_by:'neon-cortesqueue',verified_at:new Date().toISOString()};
   const rows=await query("UPDATE cortes_publications SET status='confirmed',remote_id=$5,confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3 AND lease_generation=$4 AND publication_started_at IS NOT NULL AND NOT EXISTS (SELECT 1 FROM cortes_publications d WHERE d.target_key=$2 AND d.id<>$1 AND d.status='confirmed' AND d.remote_id=$5) RETURNING id,status,remote_id",
    [id,KWAI_TARGET,owner,gen,canonical,JSON.stringify(evidence)]);
   return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_PRIMARY_MOBILE_STALE_FENCE_OR_DUPLICATE'};
  }
  const proof=b.confirmation_evidence||{},remote=String(b.remote_id||'');
  if(physical){
   if(proof.kind==='kwai_public_profile_source_frame_proof_v1')
    return kwaiPhysicalSourceFrameConfirm(KWAI_TARGET,owner,b,proof,remote);
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
   "WHEN publication_started_at IS NULL AND $5::boolean=FALSE THEN 'queued' ELSE 'uncertain' END,"+
   "lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 "+
   "AND target_key=$2 AND status IN ('leased','started') "+
   "AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",
   [id,KWAI_TARGET,owner,gen,b.published_possible===true]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE'};
 }
 return{ok:false,error:'KWAI_ACTION_NOT_ALLOWED'};
}

// Terminal no-retry disposition for the owner's "reconcile once, then disregard"
// policy. The RSA-attested physical publisher is the only caller. Cancelling
// retains the ledger's source identity so the same clip stays deduplicated.
// A separately source-matched, captionless physical Kwai video may lack an
// in-app share receipt. The signed physical job still owns STARTED and
// independently proves four visual correspondences to its exact source URL.
async function kwaiPhysicalSourceFrameConfirm(target,owner,b,proof,remote){
 const account=target.split(':')[1],job=String(b.id||''),photo=String(proof.photo_id||'');
 const source=String(proof.source_video_url||'');
 const publicUrl='https://www.kwai.com/@'+account+'/video/'+photo;
 const scores=proof.media_match?.source_best_inliers;
 const evidenceTime=Number(proof.verified_at_epoch_ms);
 const postTime=Number(proof.public_post_timestamp_ms),now=Date.now();
 const gen=Number(b.lease_generation);
 if(!/^[a-z]+:[A-Za-z0-9_.-]{2,100}$/.test(target)||
    !/^kwai-cortes-[A-Za-z0-9_.:-]{12,180}$/.test(job)||
    proof.kind!=='kwai_public_profile_source_frame_proof_v1'||
    proof.ok!==true||proof.verified_publication_job_id!==job||
    proof.job_id!==job||proof.expected_account!==account||
    proof.actual_author_handle!==account||proof.caption!==''||
    proof.caption_optional!==true||proof.title_match!==true||
    !['','...'].includes(String(proof.actual_public_caption||''))||
    !/^\d{16,21}$/.test(photo)||proof.public_url!==publicUrl||
    remote!==publicUrl||!/^[a-f0-9]{64}$/.test(String(proof.media_sha256||''))||
    proof.source_media_sha256!==proof.media_sha256||
    typeof source!=='string'||!/^https:\/\/(?:www\.)?anthares\.us\/wp-content\/uploads\/anthares-clips\/[A-Za-z0-9_.\/-]+\.mp4$/.test(source)||
    !Number.isInteger(proof.source_media_bytes)||proof.source_media_bytes<2048||
    !Number.isSafeInteger(postTime)||!Number.isSafeInteger(evidenceTime)||
    evidenceTime<postTime||evidenceTime>now+30000||now-evidenceTime>24*3600000||
    !Number.isSafeInteger(gen)||gen<1||
    proof.media_match?.kind!=='sift_source_to_public_stream_memory_v2'||
    !Array.isArray(scores)||scores.length!==4||
    scores.some(v=>!Number.isInteger(v)||v<240||v>10000)||
    proof.media_match.qualifying_distinct_frames!==4||
    !Number.isFinite(proof.media_match.source_duration_seconds)||
    !Number.isFinite(proof.media_match.public_duration_seconds)||
    Math.abs(proof.media_match.source_duration_seconds-proof.media_match.public_duration_seconds)>2)
   return {ok:false,error:'KWAI_PHYSICAL_SOURCE_FRAMES_INVALID'};
 const evidence={...proof,
   kind:'kwai_authenticated_source_frame_media_proof_v1',
   attested_device:'DESKTOP-FTDK0HP',device_signature_verified:true,
   verified_at_neon:new Date().toISOString()};
 const rows=await query(
   "UPDATE cortes_publications p SET status='confirmed',remote_id=$5,"+
   "confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now() "+
   "WHERE p.id=$1 AND p.target_key=$2 AND p.status='started' "+
   "AND p.lease_owner=$3 AND p.lease_generation=$4 "+
   "AND p.remote_id IS NULL AND p.publication_started_at IS NOT NULL "+
   "AND p.payload->>'video_url'=$7 "+
   "AND abs(extract(epoch from (p.publication_started_at-to_timestamp($8/1000.0))))<480 "+
   "AND NOT EXISTS (SELECT 1 FROM cortes_publications d "+
   "WHERE d.id<>p.id AND d.target_key=p.target_key "+
   "AND d.status='confirmed' AND d.remote_id=$5) "+
   "RETURNING p.id,p.status,p.remote_id",
   [job,target,owner,gen,remote,JSON.stringify(evidence),source,postTime]);
 return rows.length?{ok:true,job:rows[0],public_media_proof:'FOUR_SOURCE_FRAMES'}:
   {ok:false,error:'KWAI_PHYSICAL_SOURCE_FRAME_STALE_FENCE'};
}

// Reconciled source-video confirmations also update the canonical CORTES origin.
// Read the WordPress callback token ONLY inside Neon. Never return or log it.
// Retried callbacks are idempotent; a failed callback never rolls back a real post.
async function kwaiSyncReconciledWordpress(target,jobId=''){
 const account=target.split(':')[1];
 const id=String(jobId||'');
 if(id&&!/^kwai-cortes-[A-Za-z0-9_.:-]{12,180}$/.test(id))
   return {ok:false,error:'KWAI_WP_SYNC_JOB_ID_INVALID'};
 const rows=await query(
  "SELECT p.id,p.remote_id,p.payload FROM cortes_publications p "+
  "WHERE p.target_key=$1 AND p.status='confirmed' "+
  "AND p.confirmation_evidence->>'kind'='kwai_authenticated_source_frames_reconciled_v1' "+
  "AND coalesce(p.confirmation_evidence->>'wp_callback_state','')<>'completed' "+
  (id?"AND p.id=$2 ":"")+
  "ORDER BY p.updated_at ASC LIMIT 2",id?[target,id]:[target]);
 const results=[];
 for(const row of rows){
  let media=row.payload;
  if(typeof media==='string'){try{media=JSON.parse(media);}catch{media=null;}}
  const url=String(media?.cortes_callback_url||'');
  const token=String(media?.cortes_callback_token||'');
  const remote=String(row.remote_id||'');
  let endpoint;try{endpoint=new URL(url);}catch{}
  if(!endpoint||endpoint.protocol!=='https:'||
     !['anthares.us','www.anthares.us'].includes(endpoint.hostname)||
     endpoint.port||endpoint.username||endpoint.password||endpoint.search||endpoint.hash||
     !endpoint.pathname.includes('/cortes/clip-network-callback')||
     !/^https:\/\/www\.kwai\.com\/@[A-Za-z0-9_.-]+\/video\/\d{16,21}$/.test(remote)||
     !remote.startsWith('https://www.kwai.com/@'+account+'/')||
     token.length<16||token.length>1000||
     !media?.cortes_video_id||!media?.cortes_clip_id){
    results.push({id:row.id,ok:false,reason:'WP_CALLBACK_CONTRACT_INVALID'});
    continue;
  }
  const payload={
   video_id:String(media.cortes_video_id||media.source_id||''),
   clip_id:String(media.cortes_clip_id||media.segment_id||''),
   attachment_id:Number(media.cortes_attachment_id||0),
   network:'kwai',account_id:String(media.cortes_account_id||'primary'),
   status:'completed',remote_id:remote,error:'',token
  };
  if(!Number.isSafeInteger(payload.attachment_id)||payload.attachment_id<0){
   results.push({id:row.id,ok:false,reason:'WP_ATTACHMENT_ID_INVALID'});
   continue;
  }
  let succeeded=false,reason='WP_CALLBACK_TRANSPORT_UNAVAILABLE';
  try{
   const response=await fetch(endpoint.toString(),{
    method:'POST',headers:{
      'Content-Type':'application/json','Accept':'application/json',
      'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36'},
    body:JSON.stringify(payload),signal:AbortSignal.timeout(18000)
   });
   if(response.ok){
    const answer=await response.json();
    if(answer&&answer.ok===true){succeeded=true;reason='OK';}
    else reason='WP_CALLBACK_RESPONSE_NOT_CONFIRMED';
   }else reason='WP_CALLBACK_HTTP_'+String(response.status);
  }catch{reason='WP_CALLBACK_TRANSPORT_UNAVAILABLE';}
  if(succeeded){
   const saved=await query(
    "UPDATE cortes_publications SET confirmation_evidence="+
    "confirmation_evidence||jsonb_build_object('wp_callback_state','completed',"+
    "'wp_callback_verified_at',now(),'wp_callback_transport','neon-cortesqueue') "+
    "WHERE id=$1 AND target_key=$2 AND status='confirmed' AND remote_id=$3 "+
    "AND confirmation_evidence->>'kind'='kwai_authenticated_source_frames_reconciled_v1' "+
    "RETURNING id",
    [row.id,target,remote]);
   succeeded=saved.length===1;
   if(!succeeded)reason='WP_CALLBACK_DB_ACK_PENDING';
  }
  results.push({id:row.id,ok:succeeded,reason});
 }
 return {ok:true,attempted:results.length,synced:results.filter(x=>x.ok).length,
  pending:results.filter(x=>!x.ok).length,results};
}

async function kwaiUnprovenAction(b,actor,target){
 if(actor.role!=='kwai-physical'||actor.workflow!=='physical:DESKTOP-FTDK0HP')
   return {ok:false,error:'KWAI_UNPROVEN_PHYSICAL_PUBLISHER_ONLY'};
 const account=target.split(':')[1];
 if(b.target_key!==target||b.expected_account!==account)
   return {ok:false,error:'KWAI_UNPROVEN_ACCOUNT_MISMATCH'};
 const mode=String(b.mode||'');
 const eligibility="(p.status='uncertain' OR (p.status='started' AND p.lease_until<now()-interval '30 minutes'))";
 if(mode==='wp-sync')return kwaiSyncReconciledWordpress(target,String(b.id||''));
 if(mode==='list'){
  const rows=await query("SELECT p.id,p.status,p.publication_started_at,p.lease_until,"+
    "p.payload->>'video_url' AS source_url,p.media_sha256 "+
    "FROM cortes_publications p WHERE p.target_key=$1 "+
    "AND "+eligibility+" AND p.remote_id IS NULL "+
    "AND p.publication_started_at<now()-interval '45 minutes' "+
    "ORDER BY p.publication_started_at LIMIT 5",[target]);
  return {ok:true,policy:'kwai_reconcile_then_disregard_v1',jobs:rows};
 }
 if(mode==='confirm'){
  const id=String(b.id||''),proof=b.proof||{};
  const photo=String(proof.photo_id||''),posted=Number(proof.posted_ms);
  const frameScores=proof.frame_inliers;
  if(!/^kwai-cortes-[A-Za-z0-9_.:-]{12,180}$/.test(id)||
     proof.kind!=='kwai_logged_source_to_public_four_frame_v1'||
     proof.account!==account||proof.job_id!==id||
     proof.authenticated_identity_checked!==true||
     !/^\d{16,21}$/.test(photo)||
     !Number.isSafeInteger(posted)||
     !/^[a-f0-9]{64}$/.test(String(proof.source_sha256||''))||
     !Array.isArray(frameScores)||frameScores.length!==4||
     frameScores.some(v=>!Number.isInteger(v)||v<75||v>3000)||
     !Number.isFinite(proof.source_duration_seconds)||
     !Number.isFinite(proof.public_duration_seconds)||
     Math.abs(proof.source_duration_seconds-proof.public_duration_seconds)>2||
     typeof proof.source_url!=='string'||proof.source_url.length>380||
     proof.public_url!==`https://www.kwai.com/@${account}/video/${photo}`)
    return{ok:false,error:'KWAI_UNPROVEN_MEDIA_PROOF_INVALID'};
  const checked=await query("SELECT status,publication_started_at,payload->>'video_url' AS source_url "+
     "FROM cortes_publications WHERE id=$1 AND target_key=$2 AND remote_id IS NULL LIMIT 1",
     [id,target]);
  if(checked.length!==1||!['uncertain','started'].includes(checked[0].status)||
     checked[0].source_url!==proof.source_url)
    return{ok:false,error:'KWAI_UNPROVEN_SOURCE_FENCE_CHANGED'};
  const started=Date.parse(checked[0].publication_started_at);
  if(!Number.isFinite(started)||posted<started-8*60000||posted>started+18*60000)
    return{ok:false,error:'KWAI_UNPROVEN_TIME_MISMATCH'};
  if(JSON.stringify(proof).length>2500)
    return{ok:false,error:'KWAI_UNPROVEN_MEDIA_PROOF_TOO_LARGE'};
  const rows=await query(
    "UPDATE cortes_publications p SET status='confirmed',lease_owner=NULL,lease_until=NULL,"+
    "remote_id=$3,updated_at=now(),"+
    "confirmation_evidence=$4::jsonb WHERE p.id=$1 AND p.target_key=$2 "+
    "AND p.status IN ('uncertain','started') AND p.remote_id IS NULL "+
    "AND p.publication_started_at IS NOT NULL AND "+
    "(p.lease_until IS NULL OR p.lease_until<now()) AND NOT EXISTS ("+
    "SELECT 1 FROM cortes_publications d WHERE d.id<>p.id AND d.target_key=p.target_key "+
    "AND d.status='confirmed' AND d.remote_id=$3) "+
    "RETURNING p.id,p.status,p.remote_id",
    [id,target,proof.public_url,JSON.stringify({
      ...proof,kind:'kwai_authenticated_source_frames_reconciled_v1',
      public_post_timestamp_ms:posted,
      qualified_distinct_frames:4,reconciled_at:new Date().toISOString()})]);
  if(!rows.length)return{ok:false,error:'KWAI_UNPROVEN_CONFIRM_FENCE_CHANGED'};
  const wp=await kwaiSyncReconciledWordpress(target,id);
  return{ok:true,job:rows[0],confirmed_media:true,wp_callback:wp};
 }
 if(mode!=='discard')return{ok:false,error:'KWAI_UNPROVEN_MODE_INVALID'};
 const id=String(b.id||''),proof=b.proof||{},now=Date.now();
 if(!/^kwai-cortes-[A-Za-z0-9_.:-]{12,180}$/.test(id)||
    proof.kind!=='kwai_bounded_public_scan_discard_v1'||
    proof.account!==account||proof.job_id!==id||
    !Number.isInteger(proof.scanned_at_epoch_ms)||
    Math.abs(now-proof.scanned_at_epoch_ms)>15*60000||
    proof.confirmed_public_media!==false||
    !['complete_absence','candidate_unproven','scan_failed_bounded'].includes(proof.result)||
    !Number.isInteger(proof.attempt_count)||proof.attempt_count<1||proof.attempt_count>10)
   return{ok:false,error:'KWAI_UNPROVEN_DISCARD_PROOF_INVALID'};
 const bounded=proof.result==='scan_failed_bounded';
 if(bounded&&proof.attempt_count<2)
   return{ok:false,error:'KWAI_UNPROVEN_TWO_ATTEMPTS_REQUIRED'};
 if(!bounded&&(
    proof.authenticated_identity_checked!==true||
    !Number.isInteger(proof.oldest_public_ms)||
    !Number.isInteger(proof.newest_public_ms)||
    proof.oldest_public_ms>=proof.newest_public_ms||
    !Number.isInteger(proof.scanned_items)||proof.scanned_items<2||
    !Array.isArray(proof.candidate_photo_ids)||proof.candidate_photo_ids.length>15||
    proof.candidate_photo_ids.some(x=>!/^\d{16,21}$/.test(String(x)))))
   return{ok:false,error:'KWAI_UNPROVEN_PROFILE_SCAN_INVALID'};
 if(JSON.stringify(proof).length>3000)
   return{ok:false,error:'KWAI_UNPROVEN_PROOF_TOO_LARGE'};
 const prior=await query("SELECT id,status,publication_started_at FROM cortes_publications "+
   "WHERE id=$1 AND target_key=$2 LIMIT 1",[id,target]);
 if(prior.length!==1)return{ok:false,error:'KWAI_UNPROVEN_JOB_MISSING'};
 if(prior[0].status==='cancelled')
   return{ok:true,already_discarded:true,job:{id,status:'cancelled'}};
 const started=Date.parse(prior[0].publication_started_at);
 if(!Number.isFinite(started)||started>now-45*60000||
    (bounded&&started>now-90*60000))
   return{ok:false,error:'KWAI_UNPROVEN_GRACE_PERIOD_NOT_MET'};
 if(!bounded&&(proof.oldest_public_ms>started-18*60000||
               proof.newest_public_ms<started+18*60000))
   return{ok:false,error:'KWAI_UNPROVEN_PUBLIC_WINDOW_INCOMPLETE'};
 const rows=await query("UPDATE cortes_publications p SET status='cancelled',"+
   "lease_owner=NULL,lease_until=NULL,updated_at=now(),"+
   "confirmation_evidence=coalesce(p.confirmation_evidence,'{}'::jsonb)||"+
   "jsonb_build_object('kind','kwai_reconcile_then_disregard_v1',"+
   "'no_retry',true,'possible_publication',true,'public_media_identity_proven',false,"+
   "'disregard_reason',$3::text,'proof',$4::jsonb,'disregarded_at',now()) "+
   "WHERE p.id=$1 AND p.target_key=$2 AND p.remote_id IS NULL "+
   "AND "+eligibility+" AND p.publication_started_at<now()-interval '45 minutes' "+
   (bounded?"AND p.publication_started_at<now()-interval '90 minutes' ":"")+
   "RETURNING p.id,p.status",[id,target,proof.result,JSON.stringify(proof)]);
 return rows.length?{ok:true,job:rows[0],no_retry:true}:
   {ok:false,error:'KWAI_UNPROVEN_FENCE_CHANGED_OR_ACTIVE'};
}

async function kwaiSecondaryAction(action,b,actor){
 const KWAI_TARGET='kwai:universoanthares';
 // The independent ReDroid identity is authenticated and disabled by default
 // in kwaiPersistentCloudIdentity(). Keep only the exact registered role pair.
 const secondaryCloudIdentity=actor.role==='kwai-persistent-cloud'&&
  actor.workflow==='cloud:android:redroid';
 if(!((actor.role==='kwai-physical'&&actor.workflow==='physical:DESKTOP-FTDK0HP')||
      (actor.role==='kwai-mobile'&&actor.workflow==='mobile:M2004J19C:universoanthares')||
      secondaryCloudIdentity))
  return{ok:false,error:'KWAI_SECONDARY_PUBLISHER_ONLY'};
 if(b.target_key!==KWAI_TARGET||b.expected_account!=='universoanthares')return{ok:false,error:'KWAI_SECONDARY_ACCOUNT_MISMATCH'};
 if(action==='kwai-unproven')return kwaiUnprovenAction(b,actor,KWAI_TARGET);
 if(!['kwai-physical-stats','kwai-lease','kwai-renew','kwai-start','kwai-confirm','kwai-fail'].includes(action))return{ok:false,error:'KWAI_SECONDARY_UNSUPPORTED_ACTION'};
 if(action==='kwai-physical-repair-no-post'){
  // Recover a fresh UNCERTAIN state where the physical Android publisher
  // never sent a new post: its old October on-device anti-duplicate marker
  // returned ALREADY_ATTEMPTED. Require independent recent full public feed
  // and source-frame exclusion before restoring the same canonical job.
  if(actor.role!=='kwai-physical'||actor.workflow!=='physical:DESKTOP-FTDK0HP'||
     b.target_key!==KWAI_TARGET||b.expected_account!=='universoanthares')
   return{ok:false,error:'KWAI_PHYSICAL_RECOVERY_IDENTITY_REQUIRED'};
  const id=String(b.id||''),p=b.proof||{},now=Date.now();
  const start=Number(p.previous_started_at_epoch_ms),verified=Number(p.verified_at_epoch_ms);
  const marker=Number(p.native_marker_epoch_ms),scan=p.public_scan||{};
  if(!/^kwai-cortes-[A-Za-z0-9_-]{10,180}$/.test(id)||
     p.kind!=='kwai_physical_no_new_post_marker_v1'||p.job_id!==id||
     p.author_handle!=='universoanthares'||
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
   "publication_started_at,"+
   "confirmation_evidence->>'kind' AS proof_kind,"+
   "confirmation_evidence->>'job_id' AS proof_job,"+
   "confirmation_evidence->>'source_sha256' AS proof_sha,"+
   "confirmation_evidence->>'attested_device' AS proof_device,"+
   "confirmation_evidence->>'device_signature_verified' AS proof_signed "+
   "FROM cortes_publications WHERE id=$1 AND target_key=$2 LIMIT 1",[id,KWAI_TARGET]);
  if(rows.length!==1)return{ok:false,error:'KWAI_NO_POST_JOB_MISSING'};
  const r=rows[0],prior={kind:r.proof_kind,job_id:r.proof_job,
   source_sha256:r.proof_sha,attested_device:r.proof_device,
   device_signature_verified:dbTrue(r.proof_signed)};
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
     b.target_key!==KWAI_TARGET||b.expected_account!=='universoanthares')
   return{ok:false,error:'KWAI_HISTORICAL_PHYSICAL_IDENTITY_REQUIRED'};
  const id=String(b.id||''),decision=String(b.decision||''),p=b.proof||{};
  const now=Date.now(),verified=Number(p.verified_at_epoch_ms);
  const started=Number(p.previous_started_at_epoch_ms);
  if(!/^kwai-cortes-[A-Za-z0-9_-]{10,180}$/.test(id)||
     p.job_id!==id||!['confirm','requeue'].includes(decision)||
     p.schema!=='kwai-historical-reconciliation-v1'||
     p.author_handle!=='universoanthares'||
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
   const canon='https://www.kwai.com/@universoanthares/video/'+videoId;
   if(!/^[0-9]{16,21}$/.test(videoId)||url!==canon||
      p.public_account!=='universoanthares'||
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
  if(b.target_key!==KWAI_TARGET||b.account_id!=='universoanthares'||
    b.expected_account!=='universoanthares'||b.executor!=='github_hosted_android'||
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
 const mobile=actor.role==='kwai-mobile'&&actor.workflow==='mobile:M2004J19C:universoanthares';
 const cloud=actor.role==='kwai-publisher'&&actor.workflow==='cortes-kwai-cloud-publisher.yml';
 const persistentCloud=actor.role==='kwai-persistent-cloud'&&actor.workflow==='cloud:android:redroid';
 if(!physical&&!cloud&&!mobile&&!persistentCloud)return{ok:false,error:'KWAI_PUBLISHER_ROLE_REQUIRED'};
 if(localBlockedByCloudCutover(actor,action))return{ok:false,error:'KWAI_LOCAL_CUTOVER_ACTIVE'};
 if(b.target_key!==KWAI_TARGET||b.expected_account!=='universoanthares')
  return{ok:false,error:'KWAI_ACCOUNT_IDENTITY_MISMATCH'};
 const owner=physical?'physical_android:DESKTOP-FTDK0HP':mobile?'mobile_android:M2004J19C':'kwai-cloud:'+actor.workflow;
 if(action==='kwai-physical-stats'){
  if(!physical&&!mobile)return{ok:false,error:'KWAI_DEVICE_ONLY'};
  const rows=await query("SELECT status,count(*)::int AS n FROM cortes_publications WHERE target_key=$1 GROUP BY status",[KWAI_TARGET]);
  const pacing=await kwaiDeadlinePacing(KWAI_TARGET,100);
  return {ok:true,...pacing,states:rows};
 }
 if(action==='kwai-lease'){
  const pacing=await kwaiDeadlinePacing(String(b.target_key||''),100);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
  const seconds=Number(b.lease_seconds||180);
  if(!Number.isSafeInteger(seconds)||seconds<60||seconds>((physical||mobile)?3600:600))
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
   // Atomic start fence: even a lease issued by an older runtime cannot
   // start outside the owner's 06:00–23:00 operational window.
   "AND (now() AT TIME ZONE 'America/Campo_Grande')::time >= time '06:00' "+
   "AND (now() AT TIME ZONE 'America/Campo_Grande')::time < time '23:00' "+
   "RETURNING p.id,p.status,p.lease_generation";
  const rows=await query(sql,[id,KWAI_TARGET,owner,gen]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_STALE_FENCE_OR_QUOTA'};
 }
 if(action==='kwai-confirm'){
  if(mobile){
   // A mobile signer must present a Kwai-generated in-app share URL.
   // The independent Neon backend resolves the link and binds the account.
   const id=String(b.id||''),gen=Number(b.lease_generation);
   const short=String(b.remote_id||''),proof=b.confirmation_evidence||{};
   if(!/^https:\/\/k\.kwai\.com\/p\/[A-Za-z0-9_-]{5,100}$/.test(short)||
      proof.kind!=='kwai-mobile-official-share-v1'||proof.job_id!==id||
      proof.account!=='universoanthares'||proof.share_url!==short||
      !/^[a-f0-9]{64}$/.test(String(proof.media_sha256||'')))
    return{ok:false,error:'KWAI_MOBILE_OFFICIAL_RECEIPT_REQUIRED'};
   const row=await query("SELECT id,status,media_sha256,publication_started_at FROM cortes_publications WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4 LIMIT 1",
    [id,KWAI_TARGET,owner,gen]);
   if(row.length!==1||row[0].status!=='started'||row[0].media_sha256!==proof.media_sha256||!row[0].publication_started_at)
    return{ok:false,error:'KWAI_MOBILE_MEDIA_FENCE_INVALID'};
   let actual;
   try{
    const response=await fetch(short,{redirect:'follow',headers:{'User-Agent':'Mozilla/5.0'},signal:AbortSignal.timeout(15000)});
    if(!response.ok)return{ok:false,error:'KWAI_MOBILE_PUBLIC_LINK_UNAVAILABLE'};
    actual=new URL(response.url);
   }catch{return{ok:false,error:'KWAI_MOBILE_PUBLIC_LINK_UNAVAILABLE'};}
   const match=/^\/@universoanthares\/video\/([0-9]{16,21})$/.exec(actual.pathname);
   const photo=actual.searchParams.get('photoId'),author=actual.searchParams.get('authorKwaiId');
   if(actual.protocol!=='https:'||actual.host!=='www.kwai.com'||!match||
      (photo&&photo!==match[1])||(author&&author!=='universoanthares'))
    return{ok:false,error:'KWAI_MOBILE_PUBLIC_ACCOUNT_MISMATCH'};
   const canonical='https://www.kwai.com/@universoanthares/video/'+match[1];
   const evidence={kind:'kwai_mobile_official_receipt_v1',account:'universoanthares',job_id:id,
     source_sha256:proof.media_sha256,short_url:short,public_url:canonical,
     receipt_resolved_by:'neon-cortesqueue',verified_at:new Date().toISOString()};
   const rows=await query("UPDATE cortes_publications SET status='confirmed',remote_id=$5,confirmation_evidence=$6::jsonb,lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3 AND lease_generation=$4 AND publication_started_at IS NOT NULL RETURNING id,status,remote_id",
    [id,KWAI_TARGET,owner,gen,canonical,JSON.stringify(evidence)]);
   return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'KWAI_MOBILE_STALE_FENCE'};
  }
  const proof=b.confirmation_evidence||{},remote=String(b.remote_id||'');
  if(physical){
   if(proof.kind==='kwai_public_profile_source_frame_proof_v1')
    return kwaiPhysicalSourceFrameConfirm(KWAI_TARGET,owner,b,proof,remote);
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
       /^https:\/\/www\.kwai\.com\/@universoanthares\/video\/[0-9]{16,21}$/.test(url):
       /^https:\/\/k\.kwai\.com\/p\/[A-Za-z0-9_-]{5,100}$/.test(url);
   if(proof.kind!=='kwai_verified_public_media_v2'||
      proof.schema!=='kwai-public-media-proof-v2'||proof.ok!==true||
      proof.job_id!==String(b.id)||proof.expected_account!=='universoanthares'||
      proof.actual_author_handle!=='universoanthares'||proof.public_url!==remote||
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
   (h==='www.kwai.com'&&/^\/@universoanthares\/photo\/[0-9]{5,100}$/.test(p));
  if(!u||u.protocol!=='https:'||!official||u.username||u.password||
    u.port||u.search||u.hash||p.split('/').filter(Boolean).pop()!==remote||
    proof.kind!=='kwai_account_media_readback_verified'||
    !['kwai_public_deeplink_title_and_author_profile_handle',
      'physical_profile_exact_account_timestamp_and_share_ui'].includes(proof.method)||
    proof.account!=='universoanthares'||proof.remote_id!==remote||
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
   "WHEN publication_started_at IS NULL AND $5::boolean=FALSE THEN 'queued' ELSE 'uncertain' END,"+
   "lease_owner=NULL,lease_until=NULL,updated_at=now() WHERE id=$1 "+
   "AND target_key=$2 AND status IN ('leased','started') "+
   "AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",
   [id,KWAI_TARGET,owner,gen,b.published_possible===true]);
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
// Production deadline gate for every Neon-backed account/destination. Cron and
// redundant triggers wake workers; only the computed due time authorizes lease.
// Verified public timestamps, rather than ledger updates, control Kwai pacing.
// Both accounts share this canonical server-side lease guard; the PC computes
// an independent estimate but cannot override the production lease decision.
async function kwaiDeadlinePacing(targetKey,dailyLimit=100){
 if(!['kwai:lucasrosalem','kwai:universoanthares'].includes(targetKey))
   throw Error('KWAI_PACING_UNAUTHORIZED_ACCOUNT');
 const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
 const open="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '6 hours') AT TIME ZONE 'America/Campo_Grande')";
 const end="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '23 hours') AT TIME ZONE 'America/Campo_Grande')";
 const actual="(CASE WHEN t.status='confirmed' AND (t.confirmation_evidence->>'public_post_timestamp_ms') ~ '^[0-9]{13}$' THEN to_timestamp((t.confirmation_evidence->>'public_post_timestamp_ms')::double precision/1000) WHEN t.status='confirmed' THEN t.publication_started_at ELSE NULL END)";
 const eligible="SELECT count(*)::int AS n FROM cortes_publications p WHERE p.target_key=$1 "+
   "AND p.status='queued' AND p.publication_started_at IS NULL AND "+
   "NOT EXISTS (SELECT 1 FROM cortes_publications d WHERE d.target_key=p.target_key "+
   "AND d.id<>p.id AND d.status<>'failed' AND "+
   "((d.source_id=p.source_id AND d.source_start<p.source_end AND d.source_end>p.source_start) "+
   "OR d.media_sha256=p.media_sha256) AND "+
   "(d.status IN ('leased','started','confirmed','uncertain') OR "+
   "(d.status='queued' AND (d.created_at,d.id)<(p.created_at,p.id))))";
 const sql="WITH time_bounds AS (SELECT now() AS clock, "+day+" AS start_at, "+open+" AS open_at, "+end+" AS end_at),"+
   " eligible AS ("+eligible+"),"+
   " post_history AS (SELECT t.status,t.publication_started_at,"+actual+" AS actual_at "+
   "FROM cortes_publications t WHERE t.target_key=$1) "+
   "SELECT e.n AS pending, b.clock AS server_now,b.open_at AS window_open_at,b.end_at AS deadline_at,"+
   " count(*) FILTER (WHERE h.status='confirmed' AND h.actual_at>=b.start_at AND h.actual_at<b.end_at)::int AS confirmed_today,"+
   " count(*) FILTER (WHERE (h.status='confirmed' AND h.actual_at>=b.start_at AND h.actual_at<b.end_at) OR "+
   "(h.status IN ('started','uncertain') AND h.publication_started_at>=b.start_at AND h.publication_started_at<b.end_at))::int AS used,"+
   " min(h.actual_at) FILTER (WHERE h.status='confirmed' AND h.actual_at>=b.start_at AND h.actual_at<b.end_at) AS first_confirmed,"+
   " max(h.actual_at) FILTER (WHERE h.status='confirmed' AND h.actual_at>=b.start_at AND h.actual_at<b.end_at) AS last_confirmed "+
   "FROM time_bounds b CROSS JOIN eligible e LEFT JOIN post_history h ON TRUE "+
   "GROUP BY e.n,b.clock,b.open_at,b.end_at";
 const result=await query(sql,[targetKey]);
 const row=result[0];
 if(!row)throw Error('KWAI_PACING_EMPTY_SNAPSHOT');
 return deriveKwaiPacing({target_key:targetKey,daily_limit:dailyLimit,
   pending:Number(row.pending),used:Number(row.used),
   confirmed_today:Number(row.confirmed_today),
   first_confirmed_at:row.first_confirmed,
   last_confirmed_at:row.last_confirmed,
   now:row.server_now,window_open_at:row.window_open_at,deadline:row.deadline_at});
}

async function cortesDeadlinePacing(targetKey,dailyLimit){
 if(!/^[a-z]+:[A-Za-z0-9_.@-]{2,100}$/.test(String(targetKey||''))||
    !Number.isSafeInteger(dailyLimit)||dailyLimit<1||dailyLimit>100)
   throw Error('CORTES_PACING_SCOPE_INVALID');
 const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
 const start="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '6 hours') AT TIME ZONE 'America/Campo_Grande')";
 const lastSlot="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '22 hours 59 minutes') AT TIME ZONE 'America/Campo_Grande')";
 const deadline="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '23 hours') AT TIME ZONE 'America/Campo_Grande')";
 const rows=await query(`SELECT
   count(*) FILTER (WHERE status='queued')::int AS pending,
   count(*) FILTER (WHERE (status='confirmed' AND updated_at>=${day})
     OR (publication_started_at>=${day} AND status IN ('started','uncertain','confirmed')))::int AS used,
   min(updated_at) FILTER (WHERE status='confirmed' AND updated_at>=${day}) AS first_confirmed,
   max(updated_at) FILTER (WHERE status='confirmed' AND updated_at>=${day}) AS last_confirmed,
   max(publication_started_at) FILTER (WHERE publication_started_at>=${day}) AS last_started,
   now() AS server_now, ${start} AS start_at, ${lastSlot} AS final_at,
   ${deadline} AS deadline_at
   FROM cortes_publications WHERE target_key=$1`,[targetKey]);
 const r=rows[0]||{},now=new Date(r.server_now),end=new Date(r.deadline_at),
       begin=new Date(r.start_at),finalSlot=new Date(r.final_at);
 if(!Number.isFinite(now.getTime())||!Number.isFinite(end.getTime())||
    !Number.isFinite(begin.getTime())||!Number.isFinite(finalSlot.getTime())||
    !(begin<finalSlot&&finalSlot<end))
   throw Error('CORTES_PACING_CLOCK_UNVERIFIED');
 const pending=Number(r.pending||0),used=Number(r.used||0),
       remaining=Math.min(pending,Math.max(0,dailyLimit-used));
 const plan={target_key:targetKey,daily_limit:dailyLimit,pending,started_today:used,
   remaining_today:remaining,excess_over_limit:Math.max(0,pending-remaining),
   first_confirmed_at:r.first_confirmed||null,last_confirmed_at:r.last_confirmed||null,
   start_at:begin.toISOString(),deadline_at:end.toISOString(),server_now:now.toISOString(),
   next_due_at:null,status:'IDLE'};
 if(!pending)return plan;
 if(now<begin){plan.status='WAIT_DAY_START';plan.next_due_at=begin.toISOString();return plan;}
 if(now>=end){plan.status='BLOCKED_SAME_DAY_CAPACITY';return plan;}
 if(!remaining){plan.status='BLOCKED_PLATFORM_LIMIT';return plan;}
 if(!!r.first_confirmed!==!!r.last_confirmed)
   throw Error('CORTES_PACING_CONFIRMATION_INCOMPLETE');
 const first=r.first_confirmed?new Date(r.first_confirmed):null;
 const last=r.last_confirmed?new Date(r.last_confirmed):null;
 const started=r.last_started?new Date(r.last_started):null;
 if((last&&(!Number.isFinite(first.getTime())||!Number.isFinite(last.getTime())||
    first>last||last>end||last>now))||
    (started&&(!Number.isFinite(started.getTime())||started>now||started>end)))
   throw Error('CORTES_PACING_CONFIRMATION_CLOCK_INVALID');
 const anchor=Math.max(last?.getTime()??-Infinity,started?.getTime()??-Infinity);
 if(anchor===-Infinity){plan.status='DUE';plan.next_due_at=plan.server_now;return plan;}
 if(anchor>=finalSlot.getTime()){plan.status='BLOCKED_SAME_DAY_CAPACITY';return plan;}
 const interval=(finalSlot.getTime()-anchor)/remaining;
 if(!(interval>0)){plan.status='BLOCKED_SAME_DAY_CAPACITY';return plan;}
 const due=new Date(anchor+interval);
 plan.next_due_at=due.toISOString();
 plan.interval_seconds=interval/1000;
 plan.status=now>=due?'DUE':'WAIT';
 return plan;
}

// Instagram-specific, source-of-truth deadline pacing. All triggers (cron,
// dispatch, push) are wake-ups only: only this Neon gate authorizes a slot.
// Count irreversible starts, not reconciliation timestamps (updated_at).
// Account's live rolling 24h quota is an additional bound supplied by the
// OIDC-authenticated Instagram workflow after calling Meta.
async function instagramDeadlinePacing(targetKey,dailyLimit,providerRemaining){
 if(targetKey!=='instagram:universoanthares'||dailyLimit!==100||
    !Number.isSafeInteger(providerRemaining)||providerRemaining<0||providerRemaining>100)
   throw Error('INSTAGRAM_DEADLINE_QUOTA_SCOPE_INVALID');
 const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
 const deadline="((date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') + interval '23 hours') AT TIME ZONE 'America/Campo_Grande')";
 const rows=await query(`SELECT
    count(*) FILTER (WHERE status IN ('queued','leased') AND publication_started_at IS NULL)::int AS pending,
    count(*) FILTER (WHERE status IN ('started','uncertain','confirmed')
      AND publication_started_at>=${day} AND publication_started_at<${deadline})::int AS started_today,
    max(publication_started_at) FILTER (WHERE status IN ('started','uncertain','confirmed')
      AND publication_started_at>=${day} AND publication_started_at<${deadline}) AS last_started,
    min(publication_started_at) FILTER (WHERE status IN ('started','uncertain','confirmed')
      AND publication_started_at>=${day} AND publication_started_at<${deadline}) AS first_started,
    now() AS server_now,${deadline} AS deadline_at
    FROM cortes_publications WHERE target_key=$1`,[targetKey]);
 const r=rows[0]||{},now=new Date(r.server_now),end=new Date(r.deadline_at);
 if(!Number.isFinite(now.getTime())||!Number.isFinite(end.getTime()))
   throw Error('INSTAGRAM_DEADLINE_CLOCK_UNVERIFIED');
 const pending=Number(r.pending||0),started=Number(r.started_today||0);
 const remaining=Math.min(pending,Math.max(0,dailyLimit-started),providerRemaining);
 const plan={status:'IDLE',target_key:targetKey,deadline_at:end.toISOString(),
   server_now:now.toISOString(),pending,started_today:started,
   provider_remaining:providerRemaining,remaining_today:remaining,
   carryover:Math.max(0,pending-remaining),first_started_at:r.first_started||null,
   last_started_at:r.last_started||null,next_due_at:null,interval_seconds:null};
 // Last eligible start is strictly before 23:00 local. No 23h59 grace.
 if(now>=end){plan.status='WINDOW_CLOSED';return plan;}
 if(!pending){plan.status='EMPTY';return plan;}
 if(remaining<1){plan.status='LIMIT_REACHED';return plan;}
 if(!r.last_started){
   if(r.first_started||started!==0)throw Error('INSTAGRAM_FIRST_START_INCONSISTENT');
   plan.status='DUE';plan.next_due_at=plan.server_now;return plan;
 }
 const last=new Date(r.last_started);
 if(!Number.isFinite(last.getTime())||last>now||last>=end)
   throw Error('INSTAGRAM_LAST_START_INVALID');
 // After the first submission, allocate the remaining time over the remaining
 // slots. Recalculate after each actual start and when Meta's quota changes.
 // Missed slots are carried forward: no catch-up burst and no arbitrary 65s.
 const interval=(end.getTime()-last.getTime())/remaining;
 if(!(interval>0)||!Number.isFinite(interval))throw Error('INSTAGRAM_INTERVAL_INVALID');
 const due=last.getTime()+interval;
 plan.interval_seconds=interval/1000;
 plan.next_due_at=new Date(due).toISOString();
 plan.status=now.getTime()>=due?'DUE':'WAIT';
 return plan;
}

async function instagramAuthenticatedProfileSave(actor,b){
 if(actor.role!=='instagram-profile'||actor.platform!=='instagram')
   return {ok:false,error:'PROFILE_SCANNER_ONLY'};
 if(b.profile!=='AntharesInstagram'||b.account!=='universoanthares'||
    b.authenticated!==true||b.complete!==true||
    !Array.isArray(b.posts)||b.posts.length<2||b.posts.length>250)
   return {ok:false,error:'PROFILE_SESSION_PROOF_INVALID'};
 const captured=Date.parse(String(b.captured_at||'')), first=Date.parse(String(b.first_at||''));
 if(!Number.isFinite(captured)||!Number.isFinite(first)||
    Math.abs(Date.now()-captured)>15*60*1000)
   return {ok:false,error:'PROFILE_SCAN_TIMESTAMP_INVALID'};
 for(const p of b.posts){
   if(!p||typeof p!=='object'||
      !/^https:\/\/www\.instagram\.com\/reel\/[A-Za-z0-9_-]+\/$/.test(String(p.permalink||''))||
      !Number.isFinite(Date.parse(String(p.timestamp||'')))||
      String(p.caption||'').length>300)
     return {ok:false,error:'PROFILE_POST_INVALID'};
 }
 const sorted=b.posts.map(p=>Date.parse(p.timestamp)).sort((a,b)=>a-b);
 if(sorted[0]>first-20*60000||sorted[sorted.length-1]<first+20*60000)
   return {ok:false,error:'PROFILE_SCAN_WINDOW_INCOMPLETE'};
 const run=String(b.workflow_run_id||'');
 if(!/^\d{7,25}$/.test(run))return {ok:false,error:'PROFILE_SCANNER_RUN_INVALID'};
 await query(`INSERT INTO cortes_instagram_authenticated_scans
 (profile_name,account_name,complete,authenticated,first_at,oldest_at,newest_at,
  scanned_count,posts,workflow_run_id,captured_at)
 VALUES ('AntharesInstagram','universoanthares',true,true,$1::timestamptz,
  $2::timestamptz,$3::timestamptz,$4::int,$5::jsonb,$6,$7::timestamptz)`,
 [new Date(first).toISOString(),new Date(sorted[0]).toISOString(),
  new Date(sorted[sorted.length-1]).toISOString(),b.posts.length,
  JSON.stringify(b.posts),run,new Date(captured).toISOString()]);
 return {ok:true,accepted:true,posts:b.posts.length};
}
async function instagramDirectAction(verb,b){
 const target='instagram:universoanthares';
 if(verb==='audio-confirm-one'){
  // Exact audit-only exception for the independently proven 21 Oct Reel.
  // The media asset was compared byte-to-byte via two authenticated fetches,
  // decoded to PCM, and correlated with the original audio (0.977).
  const id='cortes-fanout-instagram-2ecd394d6d76b9c1a89a4b66a3e5d3b4';
  const remote='18121626946995788';
  const permalink='https://www.instagram.com/reel/DewkE18xDD3/';
  const source='https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_fOmihuHUT1M_g1_9303_9360.mp4';
  if(b.id!==id||b.remote_id!==remote||b.proof_workflow_run!=='43266870818'
    ||b.authenticated_inventory_run!=='43266099213'
    ||b.confirmation_audio_correlation!==0.977)
    return{ok:false,error:'AUDIO_PROOF_IDENTITY_MISMATCH'};
  const original=await query(`SELECT id,source_id,status,payload->>'media_url' media_url,
    confirmation_evidence FROM cortes_publications
    WHERE id=$1 AND target_key=$2 LIMIT 1`,[id,target]);
  const row=original[0];
  if(!row||row.source_id!=='fOmihuHUT1M'||row.media_url!==source)
    return{ok:false,error:'AUDIO_PROOF_SOURCE_MISMATCH'};
  if(row.status==='confirmed')
    return{ok:true,already_confirmed:true};
  if(row.status!=='uncertain')return{ok:false,error:'AUDIO_PROOF_STATE_MISMATCH'};
  const evidence={kind:'authenticated_graph_source_audio_exact_match',
    confirmed_on_network:true,remote_id:remote,public_permalink:permalink,
    published_at_utc:'2026-10-21T13:55:41Z',audio_correlation:0.977,
    source_bytes:6464228,published_bytes:1972685,relative_shift_seconds:0,
    authenticated_inventory_run:'43266099213',
    media_proof_run:'43266870818',prior_evidence:row.confirmation_evidence,
    reviewed_at:new Date().toISOString()};
  const updated=await query(`UPDATE cortes_publications SET status='confirmed',
   remote_id=$3,confirmation_evidence=$4::jsonb,updated_at=now()
   WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id IS NULL
   AND NOT EXISTS (SELECT 1 FROM cortes_publications other
    WHERE other.target_key=$2 AND other.remote_id=$3 AND other.id<>$1)
   RETURNING id,status,remote_id`,[id,target,remote,JSON.stringify(evidence)]);
  return updated.length?{ok:true,job:updated[0]}:{ok:false,error:'AUDIO_PROOF_CAS_STALE'};
 }
 if(verb==='profile-snapshot'){
  const rows=await query(`SELECT profile_name,account_name,captured_at,first_at,
   oldest_at,newest_at,scanned_count,posts FROM cortes_instagram_authenticated_scans
   WHERE complete=true AND authenticated=true
     AND profile_name='AntharesInstagram' AND account_name='universoanthares'
     AND captured_at>now()-interval '60 minutes'
   ORDER BY captured_at DESC,id DESC LIMIT 1`);
  if(!rows.length)return{ok:true,available:false,reason:'NO_FRESH_LOGGED_PROFILE_SCAN'};
  return{ok:true,available:true,scan:rows[0]};
 }
 if(verb==='pending'){
  // The same authorized GitHub-hosted Instagram workflow may enumerate ONLY
  // its own uncertain queue. No token or credential enters the response.
  const limit=Number(b.limit||20);
  if(!Number.isSafeInteger(limit)||limit<1||limit>50)return{ok:false,error:'DIRECT_PUBLIC_LIMIT_INVALID'};
  const rows=await query(`SELECT id,payload->>'title' AS title,
     payload->>'description' AS description,publication_started_at,
     confirmation_evidence,status
     FROM cortes_publications WHERE target_key=$1 AND status='uncertain'
     ORDER BY publication_started_at DESC NULLS LAST,id LIMIT $2`,[target,limit]);
  return{ok:true,target_key:target,items:rows};
 }
 if(verb==='reconcile-legacy'){
  const id=String(b.id||''), decision=String(b.decision||''), proof=b.proof||{};
  if(!/^cortes-fanout-instagram-[a-f0-9]{32}$/.test(id)||
     !['visible','absent'].includes(decision))
    return{ok:false,error:'LEGACY_DECISION_INVALID'};
  const checks=(proof.profile_url==='https://www.instagram.com/universoanthares/reels/'
    &&proof.username==='universoanthares'&&proof.origin==='instagram_public_profile'
    &&proof.authenticated===true&&proof.complete===true&&proof.graph_complete===true
    &&Number(proof.scanned_count)>=2&&Number(proof.graph_scanned_count)>=2);
  const at=Date.parse(String(proof.observed_at||''));
  if(!checks||!Number.isFinite(at)||Math.abs(Date.now()-at)>15*60000)
    return{ok:false,error:'LEGACY_AUTHENTICATED_PROOF_INVALID'};
  const scans=await query(`SELECT id FROM cortes_instagram_authenticated_scans
      WHERE profile_name='AntharesInstagram' AND account_name='universoanthares'
       AND authenticated=true AND complete=true AND captured_at>now()-interval '60 minutes'
      ORDER BY id DESC LIMIT 1`);
  if(!scans.length)return{ok:false,error:'LEGACY_PROFILE_SNAPSHOT_MISSING'};
  const row=await query(`SELECT id,publication_started_at,confirmation_evidence
    FROM cortes_publications WHERE id=$1 AND target_key=$2 AND status='uncertain'
    LIMIT 1`,[id,target]);
  if(!row.length)return{ok:false,error:'LEGACY_ITEM_NOT_UNCERTAIN'};
  const item=row[0];let prev=item.confirmation_evidence||{};
  if(typeof prev==='string'){try{prev=JSON.parse(prev)}catch{prev={}}}
  const started=Date.parse(String(item.publication_started_at||prev.submitted_at||''));
  const oldest=Date.parse(String(proof.oldest_at||'')), newest=Date.parse(String(proof.newest_at||''));
  const graphOldest=Date.parse(String(proof.graph_oldest_at||''));
  if(!Number.isFinite(started)||!Number.isFinite(oldest)||!Number.isFinite(newest)||
     !Number.isFinite(graphOldest)||started<Date.parse('2026-10-01T00:00:00Z')||
     oldest>started-20*60000||graphOldest>started-20*60000||
     newest<started+20*60000)
    return{ok:false,error:'LEGACY_TIMELINE_UNCOVERED'};
  if(decision==='visible'){
    const remote=String(b.media_id||''),link=String(b.permalink||'');
    if(!/^\d{6,30}$/.test(remote)||
       !/^https:\/\/www\.instagram\.com\/reel\/[A-Za-z0-9_-]+\/$/.test(link)||
       proof.unique_title_match!==true||proof.graph_permalink!==link||
       proof.matched_permalink!==link||proof.graph_media_id!==remote)
      return{ok:false,error:'LEGACY_VISIBLE_IDENTITY_INCOMPLETE'};
    const evidence={kind:'instagram_logged_profile_legacy_confirmed',remote_id:remote,
       public_permalink:link,profile_snapshot_id:String(scans[0].id),
       observed_at:new Date().toISOString()};
    const rows=await query(`UPDATE cortes_publications SET status='confirmed',
      remote_id=$3,confirmation_evidence=$4::jsonb,updated_at=now()
      WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id IS NULL
      RETURNING id,status,remote_id`,[id,target,remote,JSON.stringify(evidence)]);
    return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'LEGACY_CAS_STALE'};
  }
  if(Date.now()-started<36*3600000||proof.no_candidates_in_window!==true)
    return{ok:false,error:'LEGACY_ABSENCE_PREMATURE_OR_AMBIGUOUS'};
  const prevScan=prev.kind==='instagram_logged_legacy_absence_first_scan'
      ?Date.parse(String(prev.first_scan_at||'')):NaN;
  const evidence={kind:Number.isFinite(prevScan)&&Date.now()-prevScan>=3600000
       ?'instagram_logged_legacy_absence_two_scans'
       :'instagram_logged_legacy_absence_first_scan',
     first_scan_at:Number.isFinite(prevScan)?prev.first_scan_at:new Date().toISOString(),
     second_scan_at:Number.isFinite(prevScan)?new Date().toISOString():null,
     original_submission_at:new Date(started).toISOString(),profile_snapshot_id:String(scans[0].id),
     no_replay:true};
  const terminal=evidence.kind==='instagram_logged_legacy_absence_two_scans';
  const rows=await query(`UPDATE cortes_publications SET
    status=CASE WHEN $3::boolean THEN 'failed' ELSE status END,
    confirmation_evidence=$4::jsonb,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id IS NULL
    RETURNING id,status`,[id,target,terminal,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0],first_scan_only:!terminal}:
      {ok:false,error:'LEGACY_CAS_STALE'};
 }
 if(verb==='reconcile'){
  const id=String(b.id||''),kind=String(b.decision||'');
  if(!/^cortes-fanout-instagram-[a-f0-9]{32}$/.test(id)
     || !['visible','absent'].includes(kind))return{ok:false,error:'DIRECT_PUBLIC_DECISION_INVALID'};
  const tag='#antharescorte'+sha(id).slice(0,12);
  const proof=b.proof;
  if(!proof||proof.username!=='universoanthares'
     ||proof.origin!=='instagram_public_profile'
     ||proof.profile_url!=='https://www.instagram.com/universoanthares/reels/'
     ||proof.complete!==true||proof.graph_complete!==true
     ||!Number.isSafeInteger(proof.scanned_count)||proof.scanned_count<1
     ||!Number.isSafeInteger(proof.graph_scanned_count)||proof.graph_scanned_count<1
     ||proof.tag!==tag)return{ok:false,error:'DIRECT_PUBLIC_PROOF_INCOMPLETE'};
  const newer=Date.parse(String(proof.newest_at||'')),older=Date.parse(String(proof.oldest_at||''));
  const graphOlder=Date.parse(String(proof.graph_oldest_at||''));
  const at=Date.parse(String(proof.observed_at||''));
  if(![newer,older,graphOlder,at].every(Number.isFinite)
     ||newer<older||Math.abs(Date.now()-at)>15*60*1000)
     return{ok:false,error:'DIRECT_PUBLIC_WINDOW_INVALID'};
  const meta=await query(`SELECT id,publication_started_at,confirmation_evidence
     FROM cortes_publications WHERE id=$1 AND target_key=$2 AND status='uncertain'
       AND publication_started_at IS NOT NULL LIMIT 1`,[id,target]);
  const item=meta[0];if(!item)return{ok:false,error:'DIRECT_PUBLIC_ITEM_NOT_UNCERTAIN'};
  const started=Date.parse(String(item.publication_started_at));
  if(!Number.isFinite(started)||older>started-20*60000
     ||graphOlder>started-20*60000||newer<started+20*60000)
     return{ok:false,error:'DIRECT_PUBLIC_WINDOW_NOT_COVERED'};
  // A visible Reel can be independently confirmed immediately. An absence
  // requires two complete scans after a full 36-hour publication grace.
  if(kind==='absent'&&(Date.now()-started<36*3600*1000
      ||started<Date.parse('2026-11-12T13:00:00Z')))
    return{ok:false,error:'DIRECT_PUBLIC_ABSENCE_TOO_EARLY_OR_LEGACY'};
  if(kind==='visible'){
    const remote=String(b.media_id||''),link=String(b.permalink||'');
    let url;try{url=new URL(link)}catch{return{ok:false,error:'DIRECT_PUBLIC_LINK_INVALID'};}
    if(!/^\d{6,30}$/.test(remote)||url.protocol!=='https:'
       ||!['instagram.com','www.instagram.com'].includes(url.hostname)
       ||!/^\/(reel|p)\/[A-Za-z0-9_-]+\/?$/.test(url.pathname)
       ||url.search||url.hash||proof.matching_caption_tag!==true
       ||proof.matched_permalink!==link||proof.graph_media_id!==remote
       ||proof.graph_permalink!==link)
      return{ok:false,error:'DIRECT_PUBLIC_MATCH_INVALID'};
    const evidence={kind:'instagram_public_profile_and_graph_verified',
       public_permalink:link,remote_id:remote,tag,scan_at:new Date().toISOString(),
       scanned_count:proof.scanned_count,window_oldest:proof.oldest_at};
    const rows=await query(`UPDATE cortes_publications SET status='confirmed',
       remote_id=$3,confirmation_evidence=$4::jsonb,updated_at=now()
       WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id IS NULL
       RETURNING id,status,remote_id`,[id,target,remote,JSON.stringify(evidence)]);
    return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'DIRECT_PUBLIC_CAS_STALE'};
  }
  if(proof.matching_caption_tag!==false||proof.graph_matching_tag!==false)
    return{ok:false,error:'DIRECT_PUBLIC_ABSENCE_UNPROVEN'};
  const previous=item.confirmation_evidence||{};
  const prev=previous.kind==='instagram_public_absence_first_pass'
      ?Date.parse(String(previous.first_scan_at||'')):NaN;
  if(Number.isFinite(prev)&&Date.now()-prev>=60*60000){
    const evidence={kind:'instagram_public_profile_absence_two_complete_scans',
      decision:'failed',tag,first_scan_at:previous.first_scan_at,
      second_scan_at:new Date().toISOString(),
      scanned_count:proof.scanned_count,graph_scanned_count:proof.graph_scanned_count,
      no_replay:true};
    const rows=await query(`UPDATE cortes_publications SET status='failed',
       confirmation_evidence=$3::jsonb,updated_at=now()
       WHERE id=$1 AND target_key=$2 AND status='uncertain'
         AND remote_id IS NULL AND publication_started_at IS NOT NULL
         AND confirmation_evidence->>'kind'='instagram_public_absence_first_pass'
       RETURNING id,status`,[id,target,JSON.stringify(evidence)]);
    return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'DIRECT_PUBLIC_CAS_STALE'};
  }
  const evidence={kind:'instagram_public_absence_first_pass',tag,
    first_scan_at:new Date().toISOString(),scanned_count:proof.scanned_count,
    graph_scanned_count:proof.graph_scanned_count,previous_kind:previous.kind||null};
  const rows=await query(`UPDATE cortes_publications SET
    confirmation_evidence=$3::jsonb,updated_at=now()
    WHERE id=$1 AND target_key=$2 AND status='uncertain'
      AND remote_id IS NULL AND publication_started_at IS NOT NULL
    RETURNING id,status`,[id,target,JSON.stringify(evidence)]);
  return rows.length?{ok:true,first_scan_complete:true,job:rows[0]}:
    {ok:false,error:'DIRECT_PUBLIC_CAS_STALE'};
 }
 if(verb==='lease'){
  if(b.target_key!==target||b.owner!=='instagram-direct:github-cloud-v1')
    return {ok:false,error:'DIRECT_OWNER_INVALID'};
  const pacing=await instagramDeadlinePacing(target,100,Number(b.quota_remaining));
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
  // Provider quota and CORTES hard daily limit are separate; both apply.
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const used=await query(`SELECT count(*)::int AS n FROM cortes_publications
    WHERE target_key=$1 AND (
      status='confirmed' AND updated_at>=${day}
      OR publication_started_at>=${day} AND status IN ('started','uncertain','confirmed')
    )`,[target]);
  if(Number(used[0]?.n||0)>=100)return {ok:true,job:null,daily_limit_reached:true,limit:100};
  const row=await query(`WITH candidate AS (
    SELECT q.id FROM cortes_publications q WHERE q.target_key=$1 AND q.status='queued'
    ORDER BY (SELECT MIN(origin.created_at) FROM cortes_publications origin WHERE origin.target_key=q.target_key AND origin.source_id=q.source_id) DESC,
      q.created_at,q.id FOR UPDATE OF q SKIP LOCKED LIMIT 1
   ) UPDATE cortes_publications p SET status='leased',lease_owner=$2,
    lease_generation=p.lease_generation+1,lease_until=now()+interval '20 minutes',updated_at=now()
    FROM candidate WHERE p.id=candidate.id AND p.status='queued'
    RETURNING p.id,p.target_key,p.payload,p.duration_class,p.lease_generation`,
    [target,b.owner]);
  return {ok:true,job:row[0]||null,pacing};
 }
 const id=String(b.id||''),owner=String(b.owner||''),gen=Number(b.lease_generation);
 if(!id||owner!=='instagram-direct:github-cloud-v1'||!Number.isSafeInteger(gen)||gen<1)
  return {ok:false,error:'DIRECT_FENCE_INVALID'};
 if(verb==='start'){
  // Recheck immediately before the irreversible provider submission. A lease
  // acquired while due never authorizes a late/early second publication.
  const pacing=await instagramDeadlinePacing(target,100,Number(b.quota_remaining));
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
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

export function validatePinterestTerminalErrorProof(b, nowMs=Date.now()){
 // A stale Buffer 'error' is terminal only after exact identity and a full
 // day after provider due time. The original post is NEVER resubmitted.
 const id=String(b?.id||''),remote=String(b?.remote_id||'');
 if(!/^cortes-fanout-pinterest-[a-f0-9]{32}$/.test(id)
    || !/^[A-Za-z0-9_:-]{1,160}$/.test(remote)
    || b?.target_key!=='pinterest:lucasyahn'
    || b?.buffer_channel_id!=='6ad8a46d778b240e2f79a40f'
    || b?.provider_status!=='error'
    || b?.scheduling_type!=='automatic'
    || b?.external_link!==''
    || b?.provider_link_present!==false)return null;
 const due=String(b?.provider_due_at_utc||'');
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/.test(due))return null;
 const stamp=Date.parse(due);
 if(!Number.isFinite(stamp)||stamp>=nowMs-24*60*60*1000
     ||stamp<nowMs-366*24*60*60*1000)return null;
 return {id,remote,provider_due_at_utc:new Date(stamp).toISOString()};
}

async function bufferAction(verb,b,platform){
 const dest=target(platform),owner='buffer-'+platform+':';
 const allowed=new Set(['lease','start','fail','media-missing','editorial-invalid','rejected','scheduled','pending','reconcile','terminal-error','stats','retention','cooldown','cooldown-status','policy']);
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
  const pacing=await cortesDeadlinePacing(dest,LIMITS[platform]);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
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
       AND (COALESCE(confirmation_evidence->>'kind','') <> 'buffer_typed_rejection'
         OR COALESCE((confirmation_evidence->>'retry_after_at')::timestamptz,now())<=now())
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
if(!['reconcile','terminal-error'].includes(verb)&&(!who.startsWith(owner)||!Number.isInteger(fence)||fence<1))
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
 if(verb==='terminal-error'){
  // A remote Buffer error quarantines an already accepted post; no resubmit.
  // This route is accessible only to the pinned Pinterest main-branch worker.
  if(platform!=='pinterest')return{ok:false,error:'PINTEREST_ERROR_ONLY'};
  const proof=validatePinterestTerminalErrorProof(b);
  if(!proof)return{ok:false,error:'PINTEREST_ERROR_PROOF_INVALID'};
  const rows=await query(`UPDATE cortes_publications
    SET status='failed',lease_owner=NULL,lease_until=NULL,updated_at=now(),
      confirmation_evidence=jsonb_build_object(
        'kind','buffer_remote_error_verified',
        'buffer_post_id',$3::text,'provider_status','error',
        'channel_id',$4::text,'provider_due_at_utc',$5::text,
        'public_link_present',false,'confirmed_on_network',false,
        'do_not_retry_remote_id',true,
        'verified_at',to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
    WHERE id=$1 AND target_key=$2 AND remote_id=$3
      AND status='uncertain'
      AND confirmation_evidence->>'kind'='buffer_scheduled'
      AND confirmation_evidence->>'buffer_post_id'=$3
      AND updated_at < now()-interval '24 hours'
    RETURNING id,status,remote_id`,[
      proof.id,dest,proof.remote,
      String(b.buffer_channel_id),proof.provider_due_at_utc]);
  return rows.length?{ok:true,job:rows[0],requeue:false}:
    {ok:false,error:'PINTEREST_ERROR_CAS_REJECTED'};
 }
 if(verb==='rejected'){
  // A typed Buffer MutationError proves the createPost request was refused.
  // Preserve the same CAS lease/fencing used by Pinterest. An Instagram
  // MEDIA rejection is terminal for that asset; never resubmit that MP4.
  const reason=String(b.reason||'');
  if(!['pinterest','instagram'].includes(platform)||
     !['BOARD','MEDIA','METADATA','QUOTA','PERMISSION','UNCLASSIFIED'].includes(reason))
    return{ok:false,error:'BUFFER_REJECTED_PROOF_INVALID'};
  const terminalMedia=platform==='instagram'&&reason==='MEDIA';
  const rows=await query(`UPDATE cortes_publications
    SET status=CASE WHEN $6::boolean THEN 'failed' ELSE 'queued' END,
      publication_started_at=NULL,
      lease_owner=NULL,lease_until=NULL,updated_at=now(),
      confirmation_evidence=jsonb_build_object(
        'kind','buffer_typed_rejection','classification',$5::text,
        'terminal_media_rejection',$6::boolean,
        'retry_after_at',to_char((now()+interval '120 minutes') AT TIME ZONE 'UTC',
                  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'confirmed_on_network',false)
    WHERE id=$1 AND target_key=$2 AND lease_owner=$3 AND lease_generation=$4
      AND status='started' AND remote_id IS NULL AND lease_until>now()
    RETURNING id,status`,[id,dest,who,fence,reason,terminalMedia]);
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
  const pacing=await cortesDeadlinePacing(target,100);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
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
   ORDER BY (SELECT MIN(origin.created_at) FROM cortes_publications origin WHERE origin.target_key=p.target_key AND origin.source_id=p.source_id) DESC,
      p.created_at,p.updated_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1
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
const COMPANY_TARGET='linkedin:primary',COMPANY_OWNER='linkedin-company:github-cloud-v1',COMPANY_LIMIT=50;
async function companyAction(verb,b){
 const id=String(b.id||''),owner=String(b.owner||'');
 if(verb==='lease'){
  if(b.target_key!==COMPANY_TARGET||owner!==COMPANY_OWNER)return{ok:false,error:'COMPANY_TARGET_OWNER_INVALID'};
  const pacing=await cortesDeadlinePacing(COMPANY_TARGET,COMPANY_LIMIT);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
  await recoverExpiredLinkedin(COMPANY_TARGET);
  await query(`UPDATE cortes_publications SET status='failed',lease_owner=NULL,lease_until=NULL,updated_at=now()
    WHERE target_key=$1 AND status='uncertain'
      AND confirmation_evidence->>'kind'='source_media_http_404'
      AND COALESCE(NULLIF(confirmation_evidence->>'quarantine_at','')::timestamptz,updated_at)
          <= now()-interval '24 hours'
      AND confirmation_evidence @> '{"qa_recovery_exhausted":true}'::jsonb`,[COMPANY_TARGET]);
  // A read-only permission can be unavailable to self-serve member apps.
  // Keep accepted-but-unverified items UNCERTAIN and never retry their IDs;
  // other distinct queued shorts must continue under the shared daily budget.
  const day="(date_trunc('day',now() AT TIME ZONE 'America/Campo_Grande') AT TIME ZONE 'America/Campo_Grande')";
  const used=await query(`SELECT count(*)::int n FROM cortes_publications WHERE target_key=$1 AND status IN ('confirmed','leased','started','uncertain') AND updated_at >= ${day}`,[COMPANY_TARGET]);
  if(Number(used[0]?.n||0)>=COMPANY_LIMIT)return{ok:true,job:null,daily_limit_reached:true,limit:COMPANY_LIMIT};
  const rows=await query(`WITH picked AS (SELECT q.id FROM cortes_publications q WHERE q.target_key=$1 AND q.status='queued'
      ORDER BY (SELECT MIN(origin.created_at) FROM cortes_publications origin WHERE origin.target_key=q.target_key AND origin.source_id=q.source_id) DESC,
        q.created_at,q.id FOR UPDATE OF q SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+interval '30 minutes',updated_at=now() FROM picked WHERE p.id=picked.id AND p.status='queued' RETURNING p.*`,[COMPANY_TARGET,COMPANY_OWNER]);
  return{ok:true,job:rows[0]||null,limit:COMPANY_LIMIT};
 }
 if(verb==='pending'){
  const rows=await query("SELECT id,remote_id,confirmation_evidence FROM cortes_publications WHERE target_key=$1 AND status='uncertain' AND confirmation_evidence->>'kind'='linkedin_api_201_unverified' AND remote_id IS NOT NULL ORDER BY updated_at,id LIMIT 5",[COMPANY_TARGET]);
  return{ok:true,jobs:rows};
 }
 if(verb==='reconcile-public'){
  const remote=String(b.remote_id||'');
  if(!id||!/^urn:li:(ugcPost|share):[0-9]{8,25}$/.test(remote)||b.public_status!==200||b.control_status!==404||b.proof_kind!=='linkedin_public_embed_head')return{ok:false,error:'COMPANY_PUBLIC_PROOF_INVALID'};
  const evidence={kind:'linkedin_public_embed_http200',verified_id:remote,oauth_author_at_creation:true,public_embed_status:200,control_embed_status:404,permalink:'https://www.linkedin.com/embed/feed/update/'+remote};
  const rows=await query("UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$4::jsonb,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='uncertain' AND remote_id=$3 AND confirmation_evidence->>'kind'='linkedin_api_201_unverified' RETURNING id,status,remote_id",[id,COMPANY_TARGET,remote,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'COMPANY_PUBLIC_RECONCILE_STALE'};
 }
 if(!['start','fail','media-missing','accepted','confirmed'].includes(verb))return{ok:false,error:'COMPANY_ACTION_DENIED'};
 const generation=Number(b.lease_generation);
 if(!id||owner!==COMPANY_OWNER||!Number.isInteger(generation)||generation<1)return{ok:false,error:'COMPANY_INVALID_FENCE'};
 if(verb==='start'){
  const r=await query("UPDATE cortes_publications SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 AND lease_until>now() RETURNING id,status",[id,COMPANY_TARGET,owner,generation]);
  return r.length?{ok:true,job:r[0]}:{ok:false,error:'COMPANY_STALE_FENCE'};
 }
 if(verb==='fail'){
  const r=await query("UPDATE cortes_publications SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status IN ('leased','started') AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,COMPANY_TARGET,owner,generation]);
  return r.length?{ok:true,job:r[0]}:{ok:false,error:'COMPANY_STALE_FENCE'};
 }
 if(verb==='media-missing'){
  const evidence={kind:'source_media_http_404',account:'organization',confirmed_on_network:false,quarantine_at:new Date().toISOString(),discard_policy:'qa_24h_then_qa_exhaustion_required'};
  const rows=await query("UPDATE cortes_publications SET status='uncertain',confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='leased' AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status",[id,COMPANY_TARGET,owner,generation,JSON.stringify(evidence)]);
  return rows.length?{ok:true,job:rows[0]}:{ok:false,error:'COMPANY_STALE_FENCE'};
 }
 const remote=String(b.remote_id||'');
 if(!/^urn:li:(share|ugcPost):[0-9]{8,25}$/.test(remote))return{ok:false,error:'COMPANY_REMOTE_INVALID'};
 if(verb==='confirmed'&&(b.confirmation_evidence?.kind!=='linkedin_author_readback_verified'||b.confirmation_evidence?.verified_id!==remote||b.confirmation_evidence?.author_verified!==true))return{ok:false,error:'COMPANY_READBACK_REQUIRED'};
 const evidence=verb==='confirmed'?b.confirmation_evidence:{kind:'linkedin_api_201_unverified',verified_id:remote,account:'organization'};
 const status=verb==='confirmed'?'confirmed':'uncertain';
 const r=await query("UPDATE cortes_publications SET status=$5,remote_id=$6,confirmation_evidence=$7::jsonb,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$2 AND status='started' AND lease_owner=$3 AND lease_generation=$4 RETURNING id,status,remote_id",[id,COMPANY_TARGET,owner,generation,status,remote,JSON.stringify(evidence)]);
 return r.length?{ok:true,job:r[0]}:{ok:false,error:'COMPANY_STALE_FENCE'};
}
async function personalAction(verb,b){
 const id=String(b.id||''),owner=String(b.owner||'');
 if(verb==='lease'){
  if(b.target_key!==P_TARGET||owner!==P_OWNER)return{ok:false,error:'PERSONAL_TARGET_OWNER_INVALID'};
  const pacing=await cortesDeadlinePacing(P_TARGET,P_LIMIT);
  if(pacing.status!=='DUE')return{ok:true,job:null,pacing};
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
  const rows=await query(`WITH picked AS (SELECT q.id FROM cortes_publications q WHERE q.target_key=$1 AND q.status='queued'
      ORDER BY (SELECT MIN(origin.created_at) FROM cortes_publications origin WHERE origin.target_key=q.target_key AND origin.source_id=q.source_id) DESC,
        q.created_at,q.id FOR UPDATE OF q SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+interval '30 minutes',updated_at=now() FROM picked WHERE p.id=picked.id AND p.status='queued' RETURNING p.*`,[P_TARGET,P_OWNER]);
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
    (action.startsWith('kwai-')?(await kwaiPhysicalIdentity(request,action))||(await kwaiMobileIdentity(request,action))||kwaiPersistentCloudIdentity(request,action)||await identity(request):await identity(request));
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
  if(action.startsWith('company-')){
    if(actor.role!=='linkedin-company')return answer({ok:false,error:'COMPANY_WORKFLOW_ONLY'},403);
    const out=await companyAction(action.slice('company-'.length),body);
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
  if(action==='instagram-profile-save'){
   const out=await instagramAuthenticatedProfileSave(actor,body);
   return answer(out,out.ok?200:403);
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
