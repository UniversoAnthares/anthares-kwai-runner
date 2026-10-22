import crypto from 'node:crypto';
import fs from 'node:fs';
import {fetchCloudManifest} from './cortes_threads_cloud_feed.mjs';
import {captionForClip} from './cortes_threads_cloud_captions.mjs';
const GRAPH='https://graph.threads.net/v1.0';
const CONTROL='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/';
const TARGET='threads:universoanthares';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const requireOk=(yes,msg)=>{if(!yes)throw Error(msg)};
async function graph(path,token,form){
 const opts={method:form?'POST':'GET',headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(25000)};
 if(form){opts.headers['Content-Type']='application/x-www-form-urlencoded';opts.body=new URLSearchParams(form)}
 const res=await fetch(GRAPH+path,opts),body=await res.json().catch(()=>({}));
 requireOk(res.ok,'GRAPH_HTTP_'+res.status+'_CODE_'+(body.error?.code||'none'));
 return body;
}
async function oidc(){
 const base=process.env.ACTIONS_ID_TOKEN_REQUEST_URL,token=process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
 requireOk(base&&token,'GITHUB_OIDC_MISSING');
 const uri=new URL(base);uri.searchParams.set('audience',CONTROL);
 const r=await fetch(uri,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(10000)});
 requireOk(r.ok,'OIDC_FETCH_HTTP_'+r.status);
 const value=(await r.json()).value;requireOk(value,'OIDC_EMPTY');return value;
}
async function verifyCloudOidc(jwt){
 const res=await fetch(CONTROL+'?action=preflight',{
  method:'POST',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},
  body:'{}',signal:AbortSignal.timeout(15000)});
 const result=await res.json().catch(()=>({}));
 requireOk(res.ok&&result.ok&&result.mutations_allowed===false,'CLOUD_OIDC_PREFLIGHT_REJECTED_'+(result.error||res.status));
 return result;
}
async function callControl(jwt,action,details={}){
 const r=await fetch(CONTROL+'?action=control',{
  method:'POST',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},
  body:JSON.stringify({action,...details}),signal:AbortSignal.timeout(23000)});
 const data=await r.json().catch(()=>({}));
 requireOk(r.ok&&data.ok,'CONTROL_'+action+'_'+(data.error||r.status));
 return data;
}
async function gate(){
 const r=await fetch(CONTROL+'?action=gate',{signal:AbortSignal.timeout(15000)});
 requireOk(r.ok,'GATE_HTTP_'+r.status);
 const d=await r.json();requireOk(d.ok&&Array.isArray(d.queued_ids),'INVALID_NEON_GATE');return d;
}
async function mediaDigest(uri){
 requireOk(/^https:\/\/anthares\.us\/wp-content\/uploads\/anthares-clips\/\d{4}\/\d{2}\/short_/.test(uri),'UNTRUSTED_MEDIA_ORIGIN');
 const r=await fetch(uri,{signal:AbortSignal.timeout(90000)});
 requireOk(r.ok&&r.body,'MEDIA_HTTP_'+r.status);
 let size=0;const hash=crypto.createHash('sha256');
 for await(const chunk of r.body){size+=chunk.byteLength;requireOk(size<=70000000,'MEDIA_TOO_BIG');hash.update(chunk)}
 requireOk(size>10000,'MEDIA_TOO_SMALL');
 return{sha256:hash.digest('hex'),bytes:size};
}
async function notifyQA(id,reason){
 const token=String(process.env.GITHUB_TOKEN||'').trim();
 if(!token){console.log('THREADS_QA_NOTIFY_TOKEN_MISSING');return}
 const body='[QA P1][THREADS][AUTO] Mídia isolada por até 24 horas: '+id+
  '. Causa: '+reason+'. Investigar origem, corrigir e reabilitar antes do prazo. '+
  'Outras mídias continuam publicando normalmente; nenhum reenvio incerto permitido.';
 try{
  const r=await fetch('https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments',{
   method:'POST',headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},
   body:JSON.stringify({body}),signal:AbortSignal.timeout(9000)});
  console.log('THREADS_QA_NOTIFY_HTTP='+r.status);
 }catch(e){console.log('THREADS_QA_NOTIFY_FAILED='+e.constructor.name)}
}
async function choose(jwt,publish){
 const snapshot=await gate();
 const queue=Array.isArray(snapshot.queued_rows)?snapshot.queued_rows:[];
 if(!queue.length)return null;
 const days=[...new Set(queue.map(row=>String(row.source_day||'')))]
  .filter(day=>/^20\d\d-\d\d-\d\d$/.test(day)).sort();
 const byId=new Map();
 for(const day of days){
  const manifest=await fetchCloudManifest({day});
  for(const item of manifest.items)byId.set('threads:'+item.id,{...item,day});
 }
 let rejected=0;
 for(const row of queue.slice(0,60)){
  const candidate=byId.get(row.id);
  if(!candidate){
   if(publish){
    const v=await callControl(jwt,'quarantine',{id:row.id,reason:'MEDIA_INVALID'});
    if(v.first_notice)await notifyQA(row.id,'MEDIA_INVALID');
   }
   rejected++;continue;
  }
  const {day,...clip}=candidate;
  let digest,tagged;
  try{
   digest=await mediaDigest(clip.url);
   tagged=captionForClip(clip.editorial,clip);
  }catch(error){
   const msg=String(error?.message||'');
   const reason=/EDITORIAL_/.test(msg)?'EDITORIAL_MISSING':/MEDIA_HTTP_404/.test(msg)?'MEDIA_HTTP_404':/MEDIA_HTTP_410/.test(msg)?'MEDIA_HTTP_410':/MEDIA_HTTP_403/.test(msg)?'MEDIA_HTTP_403':/MEDIA_HTTP_5\d\d/.test(msg)?'MEDIA_HTTP_5XX':/CAPTION_/.test(msg)?'CAPTION_FETCH_ERROR':/MEDIA_/.test(msg)?'MEDIA_INVALID':'MEDIA_FETCH_ERROR';
   console.log('THREADS_CLIP_ISOLATED='+JSON.stringify({id:row.id,reason}));
   if(publish){
    try{const v=await callControl(jwt,'quarantine',{id:row.id,reason});if(v.first_notice)await notifyQA(row.id,reason)}
    catch(err){console.log('THREADS_QUARANTINE_WRITE_FAILED='+String(err.message).slice(0,90));throw err}
   }
   rejected++;
   continue;
  }
  return{clip:tagged,media:digest,queued:queue.length,selectedDay:day,skipped:rejected};
 }
 if(rejected)console.log('THREADS_ALL_CANDIDATES_QUARANTINED='+rejected);
 return null;
}

async function publishVideo(item,token,id){
 // Reserve first, then start the quota transaction before issuing any irreversible Graph call.
 const create=await graph('/'+id+'/threads',token,{media_type:'VIDEO',video_url:item.url,text:item.caption});
 requireOk(create.id,'THREADS_CONTAINER_MISSING');
 let done=false;
 for(let n=0;n<50;n++){
  const info=await graph('/'+create.id+'?fields=id,status,error_message',token);
  if(info.status==='FINISHED'){done=true;break}
  requireOk(!['ERROR','EXPIRED'].includes(info.status),'CONTAINER_'+info.status);
  await sleep(6000);
 }
 requireOk(done,'VIDEO_PROCESSING_TIMEOUT');
 const posted=await graph('/'+id+'/threads_publish',token,{creation_id:create.id});
 requireOk(posted.id,'PUBLISH_NO_REMOTE_ID');
 const confirm=await graph('/'+posted.id+'?fields=id,permalink',token);
 requireOk(confirm.id===posted.id&&/^https:\/\/(www\.)?threads\.com\/@universoanthares\/post\/[A-Za-z0-9_-]+\/?$/.test(confirm.permalink||''),'WRONG_PUBLICATION_ID_OR_URL');
 return{post_id:posted.id,url:confirm.permalink};
}
function verifyAuthReference(){
 const c=JSON.parse(fs.readFileSync(new URL('../config/threads-cloud-auth-reference.json',import.meta.url),'utf8'));
 requireOk(c.schema==='anthares.threads.auth-reference.v1'&&c.account==='universoanthares'&&
  c.credential_kind==='oauth_access_token'&&c.token_storage==='bitwarden_secrets_manager'&&
  c.cloud_environment_variable==='THREADS_ACCESS_TOKEN'&&c.copy_browser_cookies===false&&
  c.copy_access_token_to_folder===false&&c.requires_live_identity_check===true&&
  c.requires_neon_fencing===true,'UNSAFE_THREADS_CREDENTIAL_REFERENCE');
 return c;
}
export async function run(){
 verifyAuthReference();
 const token=String(process.env.THREADS_ACCESS_TOKEN||'').trim();
 requireOk(token.length>20,'BITWARDEN_THREADS_TOKEN_NOT_LOADED');
 const me=await graph('/me?fields=id,username',token);
 requireOk(me.id&&me.username?.toLowerCase()==='universoanthares','WRONG_THREADS_ACCOUNT');
 const jwt=await oidc();await verifyCloudOidc(jwt);
 const publish=process.env.THREADS_ALLOW_PUBLISH==='1';
 const before=await gate();
 if(publish && !before.cloud_primary_enabled && process.env.GITHUB_EVENT_NAME==='schedule'){
  console.log('THREADS_CLOUD_PRIMARY_DISABLED_SKIP');return;
 }
 if(publish && before.cloud_last_success_at &&
    Date.now()-Date.parse(before.cloud_last_success_at)<6*60*1000){
  console.log('THREADS_CLOUD_COOLDOWN_SIX_MINUTES');return;
 }
 if(publish&&before.cloud_primary_enabled)await callControl(jwt,'heartbeat');
 const selected=await choose(jwt,publish);
 if(!selected){console.log('THREADS_QUEUE_EMPTY_OR_ISOLATED');return}
 const id='threads:'+selected.clip.id,media=selected.media;
 const publicInfo={account:me.username,clip:id,bytes:media.bytes,media_verified:true,queue_candidates:selected.queued,source_day:selected.selectedDay};
 if(!publish){
  console.log(JSON.stringify({ok:true,mode:'dry_run',...publicInfo,published:false}));
  return;
 }
 requireOk(['workflow_dispatch','schedule'].includes(process.env.GITHUB_EVENT_NAME),'LIVE_EVENT_NOT_AUTHORIZED');
 const claim=await callControl(jwt,'claim');const epoch=Number(claim.lease.epoch);
 const ident={id,epoch};
 let leased=null,started=false,verified=null;
 try{
  const reservation=await callControl(jwt,'reserve',{...ident,sha256:media.sha256,media_url:selected.clip.url});
  leased=reservation.job;
  await callControl(jwt,'start',{...ident,generation:Number(leased.lease_generation)});
  started=true;
  verified=await publishVideo(selected.clip,token,me.id);
  // Public proof precedes any possibly failing metadata confirmation.
  console.log('THREADS_GRAPH_POSTED='+JSON.stringify({clip:id,post_id:verified.post_id,permalink:verified.url,run_id:process.env.GITHUB_RUN_ID||''}));
  let confirmed=false,lastError=null;
  for(let attempt=1;attempt<=4;attempt++){
   try{
    await callControl(jwt,'confirm',{...ident,generation:Number(leased.lease_generation),url:verified.url});
    confirmed=true;break;
   }catch(error){lastError=error;if(attempt<4)await sleep(1200*attempt)}
  }
  if(!confirmed)throw Error('GRAPH_PUBLISHED_NEON_CONFIRM_PENDING_'+String(lastError?.message||'unknown').slice(0,80));
  console.log(JSON.stringify({ok:true,mode:'cloud_verified',...publicInfo,remote_url:verified.url,post_id:verified.post_id}));
 }catch(e){
  if(leased){
   // Fail closed even when failure happens before the publish API call.
   await callControl(jwt,'uncertain',{...ident,generation:Number(leased.lease_generation),url:verified?.url||null,post_id:verified?.post_id||null}).catch(()=>{});
  }
  throw e;
 }finally{
  // After an unknown submission, the local gate still blocks replays until reconciliation.
  await callControl(jwt,'release',{epoch}).catch(()=>{});
 }
}
if(import.meta.url===new URL('file://'+process.argv[1]).href){
 run().catch(e=>{console.error('THREADS_CLOUD_HANDOFF_FAILED='+String(e.message).slice(0,200));process.exitCode=1});
}
