// One authorized night run in GitHub cloud; primary gate/Neon fences every clip.
// Runs only within the window established by the user. Never opens a browser.
import {run} from './cortes_threads_cloud_handoff.mjs';
const API='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/';
const END=Date.parse('2026-10-22T08:40:00Z'); // 04:40 America/Campo_Grande; finish before 05:00.
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function gate(){
 const r=await fetch(API+'?action=gate',{signal:AbortSignal.timeout(16000)});
 if(!r.ok)throw Error('NEON_GATE_HTTP_'+r.status);
 const v=await r.json();if(!v.ok||typeof v.cloud_primary_enabled!=='boolean')throw Error('NEON_GATE_INVALID');
 return v;
}
async function jwt(){
 const base=process.env.ACTIONS_ID_TOKEN_REQUEST_URL,token=process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
 if(!base||!token)throw Error('OIDC_NOT_PRESENT');
 const url=new URL(base);url.searchParams.set('audience',API);
 const r=await fetch(url,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(10000)});
 if(!r.ok)throw Error('OIDC_HTTP_'+r.status);
 return (await r.json()).value;
}
async function yieldToWindows(){
 try{
  const r=await fetch(API+'?action=control',{method:'POST',headers:{Authorization:'Bearer '+await jwt(),'Content-Type':'application/json'},
   body:JSON.stringify({action:'yield-primary'}),signal:AbortSignal.timeout(20000)});
  const result=await r.json();
  console.log('THREADS_CLOUD_FAILOVER='+JSON.stringify({status:r.status,yielded:result?.yielded===true,error:result?.error||null}));
 }catch(e){console.log('THREADS_CLOUD_FAILOVER_ERROR='+e.constructor.name)}
}
async function notifyQA(message){
 try{
  const token=process.env.GITHUB_TOKEN||'';
  if(!token)return;
  await fetch('https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments',{
   method:'POST',headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','Content-Type':'application/json'},
   body:JSON.stringify({body:message}),signal:AbortSignal.timeout(10000)});
 }catch{}
}
async function main(){
 if(process.env.GITHUB_EVENT_NAME!=='workflow_dispatch'||process.env.THREADS_ALLOW_PUBLISH!=='1'||process.env.THREADS_BATCH!=='1')
  throw Error('AUTHORIZED_DISPATCH_BATCH_REQUIRED');
 let n=0,failed=0,completed=0;
 while(Date.now()<END&&n<75){
  const before=await gate();
  if(!before.cloud_primary_enabled){console.log('BATCH_STOP_PRIMARY_RELEASED');break}
  if(!before.queued_ids?.length){console.log('BATCH_QUEUE_EMPTY_OR_ISOLATED');break}
  n++;
  console.log('THREADS_CLOUD_BATCH_ITERATION='+n+' PENDING='+before.queued_ids.length);
  try{
   await run();
   const after=await gate();
   if(after.confirmed?.length>before.confirmed?.length){
    completed++;failed=0;
    const c=after.confirmed[0];
    console.log('THREADS_CLOUD_BATCH_PROVEN='+JSON.stringify({id:c.id,url:c.url}));
   }else{
    // Normal cooldown, queue exhaustion or per-item quarantine: no global stall.
    failed=0;
    console.log('THREADS_CLOUD_BATCH_NO_NEW_POST;NEXT_MEDIA_ELIGIBLE='+after.queued_ids?.length);
   }
  }catch(err){
   failed++;
   console.log('THREADS_CLOUD_BATCH_ERROR='+JSON.stringify({iteration:n,failed_in_sequence:failed,error:String(err?.message||'').slice(0,160)}));
   if(failed>=3){
    await notifyQA('[QA P0][Threads cloud batch] Três execuções consecutivas falharam; testando fallback Windows via Neon. Nenhum corte incerto deve ser republicado. Verificar GitHub Actions e erro de API imediatamente.');
    await yieldToWindows();
    break;
   }
  }
  if(Date.now()+6*60*1000>=END)break;
  await sleep(6*60*1000);
 }
 console.log('THREADS_CLOUD_BATCH_SUMMARY='+JSON.stringify({iterations:n,confirmed_in_batch:completed,remaining_from_last_snapshot:(await gate()).queued_ids.length,stop_at:new Date().toISOString()}));
}
main().catch(e=>{console.error('THREADS_CLOUD_BATCH_FATAL='+String(e.message).slice(0,160));process.exitCode=1});
