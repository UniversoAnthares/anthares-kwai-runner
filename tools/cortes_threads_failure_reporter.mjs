// Runs in a separate "if: failure()" job step: failure reporting does not depend
// on the publisher itself being alive. No cookies, OAuth or video content logged.
const token=String(process.env.GITHUB_TOKEN||'');
const repo='UniversoAnthares/anthares-kwai-runner';
const event=String(process.env.THREADS_EVENT||'unknown').slice(0,36);
const run=String(process.env.GITHUB_RUN_ID||'');
const sha=String(process.env.GITHUB_SHA||'').slice(0,40);
const url='https://github.com/'+repo+'/actions/runs/'+run;
const headers={Authorization:'Bearer '+token,Accept:'application/vnd.github+json',
 'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'};
const safe=msg=>console.log(String(msg).slice(0,200));
async function request(path,body){
 const resp=await fetch('https://api.github.com/repos/'+repo+path,
  {method:'POST',headers,body:JSON.stringify(body),signal:AbortSignal.timeout(14000)});
 if(!resp.ok)throw Error('GITHUB_QA_HTTP_'+resp.status);
 return resp.status;
}
async function main(){
 if(!/^[0-9]{6,15}$/.test(run)||token.length<20)throw Error('QA_AUTH_OR_RUN_MISSING');
 const body='[QA P0][Threads][CORTES] Execução cloud falhou: '+url+
  '. Evento: '+event+'. Commit: '+sha+
  '. Diagnosticar imediatamente causa, leases e quotas no Neon. '+
  'Manter progresso por outro executor se necessário; jamais repetir publicação incerta. '+
  'Aplicar correção permanente, teste regressivo, redundância e validação de postagem real.';
 let ok=0;
 try{await request('/issues/283/comments',{body});ok++;safe('THREADS_QA_P0_CENTRAL_NOTIFIED=true')}
 catch(e){safe('THREADS_QA_P0_CENTRAL_FAILED='+e.message)}
 try{
  await request('/actions/workflows/cortes-threads-qa-auto-diagnostics.yml/dispatches',{
   ref:'main',inputs:{incident:'cloud-run-failed',source_run:run}
  });
  ok++;safe('THREADS_QA_DIAGNOSTICS_DISPATCHED=true');
 }catch(e){safe('THREADS_QA_DIAGNOSTICS_DISPATCH_FAILED='+e.message)}
 if(ok===0)throw Error('QA_ALL_NOTIFICATION_ROUTES_FAILED');
}
main().catch(e=>{console.error('THREADS_QA_REQUIRES_INDEPENDENT_WATCHDOG='+e.message);process.exitCode=2});
