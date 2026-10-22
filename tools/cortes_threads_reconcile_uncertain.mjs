// Read-only reconciliation of uncertain Threads submissions. Never clicks Post.
import fs from 'node:fs';
import path from 'node:path';
import {claimTab,releaseTab} from './cortes_tab_lifecycle.mjs';
const base='D:\\AntharsWork\\cortes-social-browser-20261020',port=9225;
const ledgerFile=path.join(base,'threads-ledger.json'),lockFile=path.join(base,'threads-worker.lock');
const outFile=path.join(base,'threads-reconciliation-last.json');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const original=JSON.parse(fs.readFileSync(ledgerFile,'utf8'));
const candidates=Object.entries(original.items||{}).filter(([k,v])=>v.status==='submitting_uncertain');
const report={checked_at:new Date().toISOString(),total:candidates.length,matches:[],unresolved:[]};
if(!candidates.length){console.log(JSON.stringify(report));process.exit(0)}
let lockHandle=null,tab=null,ws=null;
try{
 lockHandle=fs.openSync(lockFile,'wx');fs.writeSync(lockHandle,'reconcile '+process.pid);
 const tabInfo=await (await fetch('http://127.0.0.1:'+port+'/json/new?'+encodeURIComponent('https://www.threads.com/@universoanthares'),{method:'PUT',signal:AbortSignal.timeout(10000)})).json();
 tab=tabInfo.id;claimTab(port,tab);
 ws=new WebSocket(tabInfo.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
 let seq=0;const requests=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data);const p=requests.get(m.id);if(!p)return;requests.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(m.error.message)):p.resolve(m.result)};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{requests.delete(id);reject(Error('CDP_TIMEOUT_'+method))},18000);requests.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}))});
 const evalIn=async exp=>{const r=await send('Runtime.evaluate',{expression:exp,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error('RUNTIME_EVALUATE_FAILED');return r.result?.value};
 await sleep(4500);
 // Only accept a unique same-account post with the original clip time and source title.
 // A page-level or mojibake-dependent substring is not a reliable identity proof.
 const probes=candidates.map(([key,value])=>{
  const times=/:([0-9]+):([0-9]+)$/.exec(String(value.clip_id||''));
  const startSeconds=times?Number(times[1]):-1;
  const marker=startSeconds>=0?'Trecho '+String(Math.floor(startSeconds/60)).padStart(2,'0')+':'+String(startSeconds%60).padStart(2,'0'):null;
  const sourceHint=String(value.title||'').split(' - ')[0].trim();
  return{key,marker,sourceHint};
 });
 for(let p=0;p<55;p++){
  const expression=`(()=>{
   const probes=${JSON.stringify(probes)};
   const norm=s=>String(s||'').normalize('NFD').split('').filter(ch=>ch.charCodeAt(0)<768||ch.charCodeAt(0)>879).join('').toLowerCase();
   const anchors=[...document.querySelectorAll('a[href*="/post/"]')];
   return probes.map(probe=>{
    if(!probe.marker||!probe.sourceHint)return null;
    const found=new Set();
    for(const a of anchors){
     if(!/^https:\\/\\/www\\.threads\\.com\\/@universoanthares\\/post\\/[A-Za-z0-9_-]+\\/?$/.test(a.href))continue;
     let card=a;
     for(let depth=0;depth<7&&card;depth++,card=card.parentElement){
      const content=card.innerText||'';
      if(content.length>1500)break;
      if(norm(content).includes(norm(probe.marker))&&norm(content).includes(norm(probe.sourceHint))){found.add(a.href);break}
     }
    }
    return found.size===1?{key:probe.key,url:[...found][0]}:null;
   }).filter(Boolean);
  })()`;
  const check=await evalIn(expression);
  for(const match of check)if(!report.matches.some(x=>x.key===match.key))report.matches.push(match);
  if(report.matches.length===candidates.length)break;
  await evalIn('(()=>{window.scrollTo(0,document.body.scrollHeight);const el=document.scrollingElement;if(el)el.scrollTop=el.scrollHeight;return true})()');
  await sleep(750);
 }
 const allMatch=new Map(report.matches.map(v=>[v.key,v.url]));
 const current=JSON.parse(fs.readFileSync(ledgerFile,'utf8'));
 for(const [key,value] of candidates){
  if(current.items[key]?.status!=='submitting_uncertain')continue;
  const publicUrl=allMatch.get(key);
  if(publicUrl){
   current.items[key]={...current.items[key],status:'published',url:publicUrl,published_at:value.submitAt||report.checked_at,reconciled_at:report.checked_at,confirmation_method:'unique_source_and_clip_marker_profile_match'};
  }else report.unresolved.push(key);
 }
 if(report.matches.length){
  const tmp=ledgerFile+'.tmp-reconcile-'+process.pid;
  fs.writeFileSync(tmp,JSON.stringify(current,null,2),'utf8');fs.renameSync(tmp,ledgerFile);
 }
 fs.writeFileSync(outFile,JSON.stringify(report,null,2),'utf8');
 console.log(JSON.stringify({ok:true,...report}));
}catch(e){report.error=String(e?.message||e);try{fs.writeFileSync(outFile,JSON.stringify(report,null,2),'utf8')}catch{};console.log(JSON.stringify({ok:false,...report}));process.exitCode=2}
finally{try{ws?.close()}catch{};if(tab)await releaseTab(port,tab);if(lockHandle){try{fs.closeSync(lockHandle);fs.unlinkSync(lockFile)}catch{}}}