import crypto from 'node:crypto';
import {fetchCloudManifest} from './cortes_threads_cloud_feed.mjs';
import {addCloudCaptions} from './cortes_threads_cloud_captions.mjs';
const BASE='https://graph.threads.net/v1.0';
const QUEUE='https://anthares-remote-primary.vercel.app/api/cortes-queue';
const TARGET='threads:universoanthares';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function must(condition,reason){if(!condition)throw Error(reason);}
async function graph(path,token,{method='GET',form=null}={}){
 const url=new URL(BASE+path),opts={method,headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(30000)};
 if(form){opts.body=new URLSearchParams(form);opts.headers['Content-Type']='application/x-www-form-urlencoded';}
 const r=await fetch(url,opts);const d=await r.json().catch(()=>({}));
 if(!r.ok)throw Error('THREADS_GRAPH_HTTP_'+r.status+'_'+(d.error?.code||'unknown'));
 return d;
}
async function oidc(){
 const u=process.env.ACTIONS_ID_TOKEN_REQUEST_URL,token=process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
 must(u&&token,'GITHUB_OIDC_UNAVAILABLE');
 const url=new URL(u);url.searchParams.set('audience',QUEUE);
 const r=await fetch(url,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(10000)});
 must(r.ok,'GITHUB_OIDC_HTTP_'+r.status);const d=await r.json();must(d.value,'GITHUB_OIDC_MISSING');return d.value;
}
async function callQueue(action,body){
 const jwt=await oidc();const r=await fetch(QUEUE+'?action='+action,{method:'POST',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(25000)});
 const d=await r.json().catch(()=>({}));
 must(r.ok&&d.ok,'QUEUE_'+action+'_HTTP_'+r.status+'_'+(d.error||'error'));
 return d;
}
async function publishedTexts(token){
 let next=BASE+'/me/threads?fields=id,text,permalink&limit=100',pages=0;const rows=[];
 while(next&&pages++<8){
  must(next.startsWith(BASE+'/'),'UNTRUSTED_GRAPH_PAGINATION');
  const r=await fetch(next,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(20000)});
  must(r.ok,'THREADS_TIMELINE_HTTP_'+r.status);const d=await r.json();must(Array.isArray(d.data),'THREADS_TIMELINE_INVALID');
  rows.push(...d.data);next=d.paging?.next||'';
 }
 must(!next,'THREADS_HISTORY_TRUNCATED');
 return rows;
}
function identity(item){return 'threads:universoanthares:'+item.id;}
async function sha256Media(url){
 must(/^https:\/\/anthares\.us\/wp-content\/uploads\/anthares-clips\//.test(url),'MEDIA_ORIGIN_NOT_APPROVED');
 const response=await fetch(url,{signal:AbortSignal.timeout(90000)});must(response.ok,'MEDIA_HTTP_'+response.status);
 const hash=crypto.createHash('sha256');let size=0;
 for await(const chunk of response.body){size+=chunk.length;must(size<100_000_000,'MEDIA_TOO_LARGE');hash.update(chunk);}
 must(size>20000,'MEDIA_TOO_SMALL');return hash.digest('hex');
}
async function publish(item,token,uid){
 let containerId='';
 try{
  const created=await graph('/'+uid+'/threads',token,{method:'POST',form:{media_type:'VIDEO',video_url:item.url,text:item.caption}});
  containerId=created.id;must(containerId,'THREADS_CONTAINER_ID_MISSING');
  let ready=false;
  for(let i=0;i<30;i++){
   const d=await graph('/'+containerId+'?fields=id,status,error_message',token);
   if(d.status==='FINISHED'){ready=true;break;}
   must(!['ERROR','EXPIRED'].includes(d.status),'THREADS_PROCESSING_'+d.status);
   await sleep(5000);
  }
  must(ready,'THREADS_PROCESSING_TIMEOUT');
  const result=await graph('/'+uid+'/threads_publish',token,{method:'POST',form:{creation_id:containerId}});
  must(result.id,'THREADS_PUBLISH_RESULT_UNKNOWN');
  const verify=await graph('/'+result.id+'?fields=id,permalink,text',token);
  must(verify.id===result.id&&/^https:\/\/(www\.)?threads\.(com|net)\//.test(verify.permalink||''),'THREADS_PUBLIC_PROOF_MISSING');
  return {id:result.id,permalink:verify.permalink};
 }catch(e){throw Error('PUBLISH_UNCERTAIN_'+e.message);}
}
async function main(){
 const token=process.env.THREADS_ACCESS_TOKEN?.trim();must(token,'THREADS_TOKEN_MISSING');
 const me=await graph('/me?fields=id,username',token);
 must(me.username?.toLowerCase()==='universoanthares','THREADS_WRONG_ACCOUNT');
 const manifest=await addCloudCaptions(await fetchCloudManifest());
 const recent=await publishedTexts(token);
 const item=manifest.items.find(i=>!recent.some(r=>String(r.text||'').includes(i.title)));
 must(item,'NO_SAFE_UNPOSTED_MEDIA');
 const sha=await sha256Media(item.url);
 const key=identity(item);
 const body={id:key,dedupe_key:key,target_key:TARGET,platform:'threads',expected_account:'universoanthares',master_id:item.id,source_id:item.source,source_start:Number(item.clip_id.split(':').at(-2)),source_end:Number(item.clip_id.split(':').at(-1)),duration_class:'short',media_sha256:sha,video_url:item.url,caption:item.caption};
 if(process.env.THREADS_ALLOW_PUBLISH!=='1'){
  console.log(JSON.stringify({ok:true,mode:'dry-run',account:me.username,feed:manifest.total,selected_clip:item.id,media_sha256:sha,publish_executed:false}));return;
 }
 // One published item per workflow invocation; caller must first stop the independent
 // local publisher, reconcile its previous uncertain results and check the central queue.
 must(process.env.THREADS_LOCAL_PAUSED_AND_RECONCILED==='1','LOCAL_EXECUTOR_NOT_RECONCILED');
 const e=await callQueue('enqueue',body);
 must(['queued','failed'].includes(e.job?.status),'QUEUE_EXISTING_ITEM_'+e.job?.status);
 const owner='github-threads-'+process.env.GITHUB_RUN_ID;
 const lease=await callQueue('lease',{target_key:TARGET,owner,lease_seconds:1200});
 must(lease.job?.id===key,'QUEUE_PICK_DIFFERENT_JOB');
 await callQueue('start',{id:key,owner,lease_generation:lease.job.lease_generation});
 try{
  const result=await publish(item,token,me.id);
  await callQueue('confirm',{id:key,owner,lease_generation:lease.job.lease_generation,remote_id:result.id,confirmation_evidence:{permalink:result.permalink,media_sha256:sha,source:item.source,clip_id:item.clip_id}});
  console.log(JSON.stringify({ok:true,mode:'published',clip:item.id,permalink:result.permalink}));
 }catch(e){
  await callQueue('fail',{id:key,owner,lease_generation:lease.job.lease_generation}).catch(()=>{});
  throw e;
 }
}
main().catch(e=>{console.error('THREADS_CLOUD_PUBLISH_ERROR='+e.message);process.exitCode=1;});
