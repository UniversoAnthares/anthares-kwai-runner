import fs from 'node:fs';
import path from 'node:path';
import {claimTab,releaseTab} from './cortes_tab_lifecycle.mjs';
import {shouldAttemptPreSubmit} from './threads_queue_policy.mjs';
const root='D:\\AntharsWork\\cortes-social-browser-20261020';
const manifestPath=path.join(root,'manifest-threads.json');
const ledgerPath=path.join(root,'threads-ledger.json');
const eventFile=path.join(root,'threads-events.log');
const lock=path.join(root,'threads-worker.lock');
const mode=process.argv[2]||'test';
const minGapMs=6*60*1000;
const maxPerDay=100;
const port=9225;
const log=(msg)=>{const line=new Date().toISOString()+' '+JSON.stringify(msg);fs.appendFileSync(eventFile,line+'\n');console.log(line)};
const readJson=(f,fallback)=>{try{return JSON.parse(fs.readFileSync(f,'utf8').replace(/^\uFEFF/,''))}catch{return fallback}};
const saveJson=(f,v)=>{const temp=f+'.tmp';fs.writeFileSync(temp,JSON.stringify(v,null,2),'utf8');fs.renameSync(temp,f)};
async function delay(ms){return new Promise(r=>setTimeout(r,ms))}
let lockHandle;
try{lockHandle=fs.openSync(lock,'wx');fs.writeSync(lockHandle,String(process.pid)+' '+new Date().toISOString())}catch{
  let stale=false;
  try{const [oldpid,started]=fs.readFileSync(lock,'utf8').trim().split(' ');if(Date.now()-Date.parse(started)>25*60*1000){
    try{process.kill(Number(oldpid),0)}catch{stale=true}
  }}catch{}
  if(stale){try{fs.unlinkSync(lock);lockHandle=fs.openSync(lock,'wx');fs.writeSync(lockHandle,String(process.pid)+' '+new Date().toISOString())}catch{}}
  if(!lockHandle){console.log('WORKER_ALREADY_RUNNING');process.exit(0)}
}
process.on('exit',()=>{try{fs.closeSync(lockHandle);fs.unlinkSync(lock)}catch{}});
let ledger=readJson(ledgerPath,{items:{},lastPublished:null});
if(!ledger.items)ledger.items={};
const seed='9CIk-I_3VhM|g1:9CIk-I_3VhM:2426:2485';
if(!ledger.items[seed]){
 ledger.items[seed]={status:'published',url:'https://www.threads.com/@universoanthares/post/DewUdWroPT2',published_at:'2026-10-21T11:40:00Z',caption:'A Poética de Aristóteles - Parte 2 | Trecho 40:26 ● Universo Anthares'};
 saveJson(ledgerPath,ledger);
}
const sourceTitles={
 "fOmihuHUT1M":"A Metamorfose [Kafka] - AN\u00c1LISE",
 "9CIk-I_3VhM":"A Po\u00e9tica de Arist\u00f3teles - Parte 2",
 "-CSeY1OpvwA":"A Morte de Ivan Ilitch [Tolst\u00f3i] - AN\u00c1LISE"
};
function normalizeEntry(entry){
 const basis=sourceTitles[entry.source]||String(entry.title||'').split(' | Trecho ')[0].normalize('NFC').trim();
 if(!basis||basis.length>150||basis.includes("\uFFFD"))throw Error("UNKNOWN_SOURCE_METADATA_BLOCKED_"+entry.source);
 const match=String(entry.clip_id||"").match(/:(\d+):\d+$/);
 if(!match)throw Error("INVALID_SEGMENT_ID");
 const start=Number(match[1]);
 const title=basis+" | Trecho "+String(Math.floor(start/60)).padStart(2,"0")+":"+String(start%60).padStart(2,"0")+" \u25cf Universo Anthares";
 const tags=entry.source==="fOmihuHUT1M"?"#Literatura #Livros #Leitura #Kafka #AMetamorfose #UniversoAnthares":
   entry.source==="9CIk-I_3VhM"?"#Literatura #Livros #Aristoteles #Poetica #Filosofia #UniversoAnthares":
   entry.source==="-CSeY1OpvwA"?"#Literatura #Livros #Tolstoi #IvanIlitch #LiteraturaRussa #UniversoAnthares":"#Literatura #Livros #Leitura #UniversoAnthares";
 return {...entry,title,caption:title+"\n\nwww.anthares.us\n\n"+tags};
}
const list=(readJson(manifestPath,{items:[]}).items||[]).flatMap(x=>{try{return [normalizeEntry(x)]}catch(e){log({action:"ERROR",id:x.id||x.clip_id,message:"SOURCE_METADATA_BLOCKED_"+e.message});return []}});
if(list.length===0)throw Error('MANIFEST_EMPTY');
const today=new Date().toLocaleDateString('en-CA',{timeZone:'America/Campo_Grande'});
const publishedToday=Object.values(ledger.items).filter(x=>x.status==='published'&&new Date(x.published_at).toLocaleDateString('en-CA',{timeZone:'America/Campo_Grande'})===today).length;
const last=ledger.lastPublished?new Date(ledger.lastPublished).getTime():0;
if(mode==='auto'){
 if(publishedToday>=maxPerDay){log({action:"DAILY_CAP_REACHED_PENDING_PRESERVED",count:publishedToday});process.exit(0)}
 if(last&&Date.now()-last<minGapMs){log({action:'COOLDOWN',remainingSeconds:Math.ceil((minGapMs-Date.now()+last)/1000)});process.exit(0)}
}
let item;
if(mode==='test')item=list.find(x=>x.clip_id==='g1:fOmihuHUT1M:9434:9515');
else item=list.find(x=>{
  if(x.date<'2026-10-20')return false;
  const state=ledger.items[x.id];
  return shouldAttemptPreSubmit(state);
});
if(!item){log({action:'QUEUE_EMPTY',processed:Object.keys(ledger.items).length});process.exit(0)}
if(
 !item.title || !item.caption ||
 /[\uFFFD\u2500-\u257f]/u.test(item.title+item.caption) ||
 /(?:AN\?LISE|AN\u00D4|\?\s+Universo Anthares)/u.test(item.title) ||
 !item.title.includes('\u25CF Universo Anthares') ||
 !item.caption.includes('www.anthares.us')
){
 log({action:'FATAL_INVALID_UNICODE_TITLE_OR_CAPTION',clip:item.clip_id});
 process.exit(5);
}if(ledger.items[item.id] && ledger.items[item.id].status!=='failed_pre_submit'){log({action:'ALREADY_CLAIMED',id:item.id,status:ledger.items[item.id].status});process.exit(0)}
if(!item.url.startsWith('https://anthares.us/')||!Number.isInteger(item.size)||item.size<100000||item.size>60e6)
 throw Error('INVALID_MEDIA');
const mediaDir=path.join(root,'media');fs.mkdirSync(mediaDir,{recursive:true});
const file=path.join(mediaDir,path.basename(new URL(item.url).pathname));
if(!fs.existsSync(file)||fs.statSync(file).size!==item.size){
 log({action:'DOWNLOAD',id:item.id,bytes:item.size});
 const r=await fetch(item.url,{signal:AbortSignal.timeout(110000)});
 if(!r.ok)throw Error('MEDIA_FETCH_HTTP_'+r.status);
 const buf=Buffer.from(await r.arrayBuffer());
 if(buf.length!==item.size)throw Error('MEDIA_SIZE_MISMATCH');
 fs.writeFileSync(file,buf);
}
if(fs.statSync(file).size!==item.size)throw Error('MEDIA_SIZE_MISMATCH');
const tabsUrl='http://127.0.0.1:'+port+'/json';
async function createTab(url){
 const r=await fetch('http://127.0.0.1:'+port+'/json/new?'+encodeURIComponent(url),{method:'PUT',signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error('BROWSER_NEW_TAB_'+r.status);
 const t=await r.json();if(!t.webSocketDebuggerUrl)throw Error('NEW_TAB_WEBSOCKET_MISSING');
 try{claimTab(port,t.id);return await new CDP(t).init()}
  catch(e){await releaseTab(port,t.id);throw e}
}
class CDP{
 constructor(target){this.t=target;this.seq=0;this.requests=new Map();this.ws=null}
 async init(){this.ws=new WebSocket(this.t.webSocketDebuggerUrl);
  await new Promise((ok,no)=>{this.ws.onopen=ok;this.ws.onerror=no});
  this.ws.onmessage=e=>{const m=JSON.parse(e.data);if(!m.id||!this.requests.has(m.id))return;
   const v=this.requests.get(m.id);this.requests.delete(m.id);clearTimeout(v.timer);
   m.error?v.no(Error('CDP_'+m.error.message)):v.ok(m.result);};
  return this}
 send(method,params={},timeout=23000){return new Promise((ok,no)=>{
   const id=++this.seq;const timer=setTimeout(()=>{this.requests.delete(id);no(Error('TIMEOUT_'+method))},timeout);
   this.requests.set(id,{ok,no,timer});this.ws.send(JSON.stringify({id,method,params}));})}
 async evaluate(exp){const r=await this.send('Runtime.evaluate',{expression:exp,awaitPromise:true,returnByValue:true,userGesture:true});
  if(r.exceptionDetails)throw Error('DOM_EVAL_FAILED');return r.result?.value}
 async close(){try{this.ws?.close()}catch{}await releaseTab(port,this.t.id)}
}
let composer=null,profile=null;
try{
 ledger.items[item.id]={status:'preparing',attempts:1+(Number(ledger.items[item.id]?.attempts)||0),claimedAt:new Date().toISOString(),title:item.title,source:item.source,clip_id:item.clip_id};
 saveJson(ledgerPath,ledger);
 composer=await createTab('https://www.threads.com/');
 let authenticated=false;
 for(let n=0;n<20;n++){
   await delay(1000);
   const r=await composer.evaluate('(()=>({logged:!!document.querySelector("[aria-label^=\\"Campo de texto vazio\\"]"),profile:!!document.querySelector("img[alt*=\\"universoanthares\\"]"),login:document.body.innerText.slice(0,220)}))()');
   if(r.logged&&r.profile){authenticated=true;break}
   if(n===19)log({action:'AUTH_CHECK',state:r});
 }
 if(!authenticated)throw Error('THREADS_NOT_AUTHENTICATED_OR_WRONG_PROFILE');
 const open=await composer.evaluate('(()=>{const e=document.querySelector("[aria-label^=\\"Campo de texto vazio\\"]");if(!e)return false;e.click();return true})()');
 if(!open)throw Error('COMPOSER_NOT_OPEN');
 let fileInput=false;
 for(let n=0;n<10;n++){await delay(800);const r=await composer.evaluate('!!document.querySelector("input[type=file]")');if(r){fileInput=true;break}}
 if(!fileInput)throw Error('FILE_INPUT_MISSING');
 const dom=await composer.send('DOM.getDocument',{depth:-1,pierce:true});
 const input=await composer.send('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'input[type=file]'});
 if(!input.nodeId)throw Error('FILE_NODE_NOT_FOUND');
 await composer.send('DOM.setFileInputFiles',{nodeId:input.nodeId,files:[file]});
 let ready=false;
 for(let n=0;n<90;n++){
   await delay(600);
   const r=await composer.evaluate('(()=>({video:!!document.querySelector("[role=dialog] video[src^=\\"blob:\\"]"),editor:!!document.querySelector("[role=dialog] [contenteditable=true]"),errors:document.body.innerText.slice(-300)}))()');
   if(r.video&&r.editor){ready=true;break}
   if(n===89)log({action:'MEDIA_NOT_READY',state:r})
 }
 if(!ready)throw Error('VIDEO_PREVIEW_NOT_READY');
 const editor=await composer.evaluate('(()=>{const e=document.querySelector("[role=dialog] [contenteditable=true]");if(!e)return false;e.focus();return true})()');
 if(!editor)throw Error('COMPOSER_EDITOR_MISSING');
 await composer.send('Input.insertText',{text:item.caption});
 const text=await composer.evaluate('document.querySelector("[role=dialog] [contenteditable=true]")?.innerText');
 if(!text||!text.includes(item.title)||!text.includes('www.anthares.us'))throw Error('CAPTION_NOT_APPLIED');
 await delay(1700);
 const canSubmit=await composer.evaluate('(()=>{const x=[...document.querySelectorAll("[role=dialog] [role=button]")].filter(e=>e.textContent?.trim()==="Postar");return x.length>0&&x.at(-1).getAttribute("aria-disabled")!=="true"})()');
 if(!canSubmit)throw Error('SUBMIT_DISABLED');
 ledger.items[item.id].status='submitting_uncertain';ledger.items[item.id].submitAt=new Date().toISOString();saveJson(ledgerPath,ledger);
 const submitted=await composer.evaluate('(()=>{const a=[...document.querySelectorAll("[role=dialog] [role=button]")].filter(e=>e.textContent?.trim()==="Postar");if(a.length!==1)return {ok:false,count:a.length};a[0].click();return {ok:true}})()');
 if(!submitted.ok)throw Error('SUBMIT_BUTTON_UNEXPECTED');
 log({action:'CLICKED_PUBLISH',id:item.id,title:item.title});
 await delay(4000);
 profile=await createTab('https://www.threads.com/@universoanthares');
 let post=null;
 for(let attempt=0;attempt<22;attempt++){
  await delay(attempt===0?8000:5000);
  const found=await profile.evaluate('(()=>{const wanted='+JSON.stringify(item.title)+';const txt=document.body.innerText;if(!txt.includes(wanted))return {found:false,head:txt.slice(0,150)};const links=[...document.querySelectorAll("a[href*=\\"/post/\\"]")];for(const link of links){let e=link;for(let i=0;i<11&&e;i++,e=e.parentElement){if(e.innerText?.includes(wanted))return {found:true,url:link.href};}}return {found:true,url:null}})()');
  if(found.found&&found.url){post=found.url;break}
  if(found.found&&!found.url)log({action:'MATCH_WITHOUT_POST_URL',id:item.id});
  if(attempt%4===3)await profile.send('Page.reload',{ignoreCache:true});
 }
 if(!post){
  log({action:'UNCONFIRMED_AFTER_CLICK',id:item.id});
  process.exitCode=3;
 }else{
  ledger=readJson(ledgerPath,{items:{}});
  ledger.items[item.id]={...ledger.items[item.id],status:'published',url:post,published_at:new Date().toISOString()};
  ledger.lastPublished=new Date().toISOString();
  saveJson(ledgerPath,ledger);
  log({action:'PUBLICATION_CONFIRMED',id:item.id,url:post});
  try{fs.unlinkSync(file)}catch{}
 }
}catch(err){
 const message=String(err.message||err);
 ledger=readJson(ledgerPath,{items:{}});
 if(ledger.items[item.id])ledger.items[item.id]={...ledger.items[item.id],status:ledger.items[item.id].status==='submitting_uncertain'?'submitting_uncertain':'failed_pre_submit',failed_at:new Date().toISOString(),error:message};
 saveJson(ledgerPath,ledger);
 log({action:'ERROR',id:item.id,message});
 process.exitCode=2;
}finally{
 if(composer)await composer.close();
 if(profile)await profile.close();
 try{fs.closeSync(lockHandle);fs.unlinkSync(lock)}catch{}
}