// Authentication circuit for the already-owned AntharesMeta browser.
// Zero page creation, zero login attempts, zero cookies in logs.
import fs from 'node:fs';
const root='D:/AntharsWork/cortes-social-browser-20261020';
const receipt=root+'/threads-auth-circuit-status.json';
let state='AUTH_REQUIRED';
let reason='NO_SESSION_PROOF';
let browserPid=null;
try {
  const response=await fetch('http://127.0.0.1:9225/json/list',{signal:AbortSignal.timeout(3500)});
  if(!response.ok)throw Error('CDP_UNAVAILABLE');
  const tabs=await response.json();
  const page=tabs.find(t=>t.type==='page' && /^https:\/\/www\.threads\.com\//.test(t.url));
  if(!page)throw Error('THREADS_TARGET_MISSING');
  const ws=new WebSocket(page.webSocketDebuggerUrl);
  try {
    await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no});
    const expression=`(()=>({isThreads:location.hostname==='www.threads.com',composer:!!document.querySelector('[aria-label^="Campo de texto vazio"]'),owner:!!document.querySelector('img[alt*="universoanthares"]')}))()`;
    ws.send(JSON.stringify({id:911,method:'Runtime.evaluate',params:{expression,returnByValue:true}}));
    const result=await new Promise((ok,no)=>{const timer=setTimeout(()=>no(Error('CDP_EVAL_TIMEOUT')),4000);ws.onmessage=e=>{const data=JSON.parse(e.data);if(data.id===911){clearTimeout(timer);if(data.error)no(Error('CDP_EVAL_REJECTED'));else ok(data.result?.result?.value)}}});
    if(result?.isThreads && result.composer && result.owner){state='AUTH_READY';reason='LIVE_OWNER_IDENTITY_CONFIRMED'}else{reason='SESSION_MISSING_OR_WRONG_ACCOUNT'}
  } finally {ws.close()}
}catch(e){reason=String(e.message||e).slice(0,80)}
const output={schema:'anthares.threads.auth-circuit.v1',checked_at_utc:new Date().toISOString(),profile:'AntharesMeta',account:'universoanthares',state,reason};
const tmp=receipt+'.tmp-'+process.pid;
try {fs.writeFileSync(tmp,JSON.stringify(output)+'\n',{encoding:'utf8',flag:'w'});fs.renameSync(tmp,receipt)}
catch(e){console.error('AUTH_CIRCUIT_RECEIPT_FAILURE');process.exitCode=21}
if(!process.exitCode)process.exitCode=state==='AUTH_READY'?0:20;
console.log('THREADS_AUTH_CIRCUIT='+state+' REASON='+reason);

