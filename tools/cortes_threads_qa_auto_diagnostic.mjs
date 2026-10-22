// P0 diagnostic in a fresh hosted runner, independent from the failed publisher.
// Diagnoses health & stale takeover; only performs safe reversible repairs.
const API='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/';
const REPO='UniversoAnthares/anthares-kwai-runner';
const gh=String(process.env.GITHUB_TOKEN||'');
const headers={Authorization:'Bearer '+gh,Accept:'application/vnd.github+json',
 'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'};
const incident=String(process.env.THREADS_QA_INCIDENT||'scheduled').slice(0,70);
const source=String(process.env.THREADS_QA_SOURCE_RUN||'');
async function api(path,opts={}){
 const r=await fetch('https://api.github.com/repos/'+REPO+path,
  {headers,...opts,signal:AbortSignal.timeout(18000)});
 if(!r.ok)throw Error('GITHUB_API_HTTP_'+r.status);
 return r.status===204?{}:r.json();
}
async function report(body){
 const sanitized=String(body).slice(0,1500);
 return api('/issues/283/comments',{method:'POST',body:JSON.stringify({body:sanitized})});
}
async function health(){
 const r=await fetch(API+'?action=gate',{signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error('NEON_GATE_HTTP_'+r.status);
 const z=await r.json();if(!z.ok||typeof z.cloud_primary_enabled!=='boolean')throw Error('NEON_GATE_UNVERIFIED');
 return z;
}
async function main(){
 let gate,problems=[],repair=[];
 try{
  gate=await health();
  const pending=Array.isArray(gate.queued_ids)?gate.queued_ids.length:0;
  const age=gate.cloud_heartbeat_at ? Math.max(0,(Date.now()-Date.parse(gate.cloud_heartbeat_at))/60000):Infinity;
  const last=gate.cloud_last_success_at?Math.max(0,(Date.now()-Date.parse(gate.cloud_last_success_at))/60000):null;
  console.log('THREADS_QA_HEALTH='+JSON.stringify({owner:gate.owner,cloud_primary_enabled:gate.cloud_primary_enabled,
   pending,cloud_inflight:gate.cloud_inflight,heartbeat_age_m:Number.isFinite(age)?Math.round(age):null,
   success_age_m:last===null?null:Math.round(last),status_counts:gate.counts}));
  if(pending>0&&!gate.cloud_primary_enabled)problems.push('PRIMARY_DISABLED_WITH_BACKLOG');
  if(pending>0&&gate.cloud_primary_enabled&&age>16)problems.push('CLOUD_HEARTBEAT_STALE');
  if(pending>0&&gate.cloud_primary_enabled&&last!==null&&last>25)problems.push('PROGRESS_STALLED');
  if((gate.counts||{}).uncertain>0)problems.push('INDIVIDUAL_UNCERTAIN_RECONCILIATION');
 }catch(e){problems.push('NEON_GATE_UNAVAILABLE');console.error('THREADS_QA_GATE='+e.message)}
 try{
  const wf=await api('/actions/workflows/cortes-threads-cloud-handoff.yml');
  if(wf.state!=='active'){
   const resp=await api('/actions/workflows/cortes-threads-cloud-handoff.yml/enable',{method:'PUT'});
   repair.push('WORKFLOW_ENABLE_ATTEMPTED');
  }
 }catch(e){problems.push('CLOUD_WORKFLOW_STATUS_UNAVAILABLE');console.error('THREADS_QA_WORKFLOW='+e.message)}
 if(problems.length){
  const body='[QA P0][Threads] Diagnóstico automático '+new Date().toISOString()+
   '. Origem='+incident+'; execução='+(/^\d{6,15}$/.test(source)?source:'unavailable')+
   '. Falhas='+problems.join(',')+'. Reparos seguros='+repair.join(',')+
   '. Fallback deve ser coordenado no Neon, sem concorrência nem reenvio de incertos. '+
   'Próxima ação: analisar execução e aplicar correção de código/testes e verificação real.';
  try{await report(body);console.log('THREADS_QA_CENTRAL_P0_CONFIRMED=true')}
  catch(e){console.error('THREADS_QA_CENTRAL_POST_FAILED='+e.message);process.exitCode=2}
 }
 if(process.env.GITHUB_STEP_SUMMARY){
  const {appendFile}=await import('node:fs/promises');
  await appendFile(process.env.GITHUB_STEP_SUMMARY,
   '## Threads QA P0 diagnóstico\n\n'+JSON.stringify({incident,problems,repair},null,2)+'\n');
 }
 console.log('THREADS_QA_AUTO_DIAG='+JSON.stringify({incident,problems,repair}));
}
main().catch(e=>{console.error('THREADS_QA_DIAGNOSTIC_FAILED='+e.message);process.exitCode=2});
