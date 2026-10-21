#!/usr/bin/env node
// Pinterest web-UI publisher. No Pinterest API calls, cookies, passwords or CAPTCHA bypass.
// Opens only owned tabs in the existing invisible CORTES Chrome CDP session.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const port=Number(process.env.CORTES_CHROME_CDP_PORT||9226);
if(port!==9226)throw Error('UNAUTHORIZED_BROWSER_PORT');
const board='Universo Anthares — Vídeos',account='lucasyahn';
const editor='https://br.pinterest.com/pin-creation-tool/';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const markers='D:\\AntharsWork\\cortes-social-browser-20261020\\chrome-owned-tabs';
let pages=[];
const safe=val=>String(val||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[—–]/g,'-').replace(/\s+/g,' ').trim().toLowerCase();
function emit(data){process.stdout.write(JSON.stringify(data)+'\n')}

async function pruneOwnedPinterestTabs(){
 if(!fs.existsSync(markers))return;
 let list=[];
 try{const r=await fetch('http://127.0.0.1:'+port+'/json/list',{signal:AbortSignal.timeout(4500)});
  if(r.ok)list=await r.json();}catch{return}
 for(const filename of fs.readdirSync(markers)){
  if(!/^9226-[a-f0-9]{32}\.json$/i.test(filename))continue;
  const marker=path.join(markers,filename);
  let entry;try{entry=JSON.parse(fs.readFileSync(marker,'utf8'))}catch{continue}
  if(Date.now()-Number(entry.created||0)<180000)continue;
  try{process.kill(Number(entry.pid),0);continue}catch(e){if(e.code==='EPERM')continue}
  const tab=list.find(x=>x.id===entry.id);
  if(tab){
   try{
    const url=new URL(tab.url);
    if(!['br.pinterest.com','www.pinterest.com','pinterest.com'].includes(url.hostname))continue;
    await fetch('http://127.0.0.1:'+port+'/json/close/'+entry.id,{signal:AbortSignal.timeout(4500)});
   }catch{continue}
  }
  try{fs.unlinkSync(marker)}catch{}
 }
}
class Page{
 constructor(target){this.t=target;this.ws=null;this.i=0;this.pending=new Map()}
 async open(){
  this.ws=new WebSocket(this.t.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{this.ws.onopen=resolve;this.ws.onerror=reject});
  this.ws.onmessage=e=>{const m=JSON.parse(e.data);if(!m.id||!this.pending.has(m.id))return;
   const p=this.pending.get(m.id);this.pending.delete(m.id);clearTimeout(p.timer);
   if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result)};
  return this;
 }
 rpc(method,params={},wait=20000){
  return new Promise((resolve,reject)=>{const id=++this.i,timer=setTimeout(()=>{
   this.pending.delete(id);reject(Error('CDP_TIMEOUT_'+method))},wait);
   this.pending.set(id,{resolve,reject,timer});
   this.ws.send(JSON.stringify({id,method,params}))});
 }
 async js(expr){const r=await this.rpc('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true,userGesture:true});if(r.exceptionDetails)throw Error('PIN_DOM_EVALUATION_FAILED');return r.result?.value}
 async text(selector,text){
  const focused=await this.js('(()=>{const e=document.querySelector('+JSON.stringify(selector)+');if(!e)return false;e.focus();return true})()');
  if(!focused)throw Error('PIN_EDITOR_FIELD_MISSING');
  await this.rpc('Input.insertText',{text});
  const got=await this.js('(()=>{const e=document.querySelector('+JSON.stringify(selector)+');return (e?.value??e?.innerText??"").trim()})()');
  if(got!==text.trim())throw Error('PIN_EDITOR_FIELD_MISMATCH');
 }
 async close(){
  try{this.ws?.close()}catch{}
  const id=this.t.id;
  try{await fetch('http://127.0.0.1:'+port+'/json/close/'+id,{signal:AbortSignal.timeout(5000)})}catch{}
  try{fs.unlinkSync(path.join(markers,port+'-'+id+'.json'))}catch{}
 }
}
async function page(url){
 if(!/^https:\/\/(?:br\.|www\.)?pinterest\.com\//.test(url))throw Error('PIN_URL_DENIED');
 const r=await fetch('http://127.0.0.1:'+port+'/json/new?'+encodeURIComponent(url),{method:'PUT',signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error('CHROME_NEW_TAB_'+r.status);
 const target=await r.json();if(!/^[a-f0-9]{32}$/i.test(target.id)||!target.webSocketDebuggerUrl)throw Error('INVALID_CHROME_TARGET');
 fs.mkdirSync(markers,{recursive:true});
 fs.writeFileSync(path.join(markers,port+'-'+target.id+'.json'),JSON.stringify({port,id:target.id,pid:process.pid,created:Date.now(),kind:'pinterest-browser'}),{flag:'wx'});
 const p=new Page(target);pages.push(p);return p.open();
}
async function until(fn,attempts=40,gap=900){
 for(let i=0;i<attempts;i++){const v=await fn();if(v)return v;await pause(gap)}
 return null;
}
async function session(p){
 await pause(6000);
 const r=await p.js('(()=>({href:location.href,login:!![...document.querySelectorAll("button")].find(x=>/^(entrar|log in|login)$/i.test((x.innerText||"").trim())),profile:[...document.querySelectorAll("a")].some(x=>{try{const u=new URL(x.href);return u.hostname.endsWith("pinterest.com")&&u.pathname==="/lucasyahn/"&&(x.querySelector("img")||/profile|perfil|account|conta/i.test([x.getAttribute("aria-label"),x.getAttribute("data-test-id")].join(" ")))}catch{return false}}),upload:!!document.querySelector("input[type=file]"),text:document.body?.innerText.slice(0,250)||""}))()');
 const url=new URL(r.href);
 if(!url.hostname.endsWith('.pinterest.com'))throw Error('PIN_WRONG_ORIGIN');
 if(r.login||!url.pathname.includes('pin-creation-tool'))throw Error('PINTEREST_BROWSER_LOGIN_REQUIRED');
 if(!r.profile)throw Error('PINTEREST_BROWSER_ACCOUNT_NOT_VERIFIED');
 return r;
}
async function inspect(p){
 return p.js('(()=>({url:location.href,fields:[...document.querySelectorAll("input,textarea,[contenteditable=true]")].map(x=>({tag:x.tagName,type:x.type,placeholder:x.getAttribute("placeholder"),name:x.getAttribute("name"),testid:x.getAttribute("data-test-id")})).slice(0,20),buttons:[...document.querySelectorAll("button,[role=button]")].map(x=>(x.innerText||x.getAttribute("aria-label")||"").trim()).filter(Boolean).slice(0,25)}))()');
}
function validate(data){
 if(!data||data.account_id!==account||data.platform!=='pinterest')throw Error('PIN_DESTINATION_INVALID');
 const media=new URL(String(data.media_url||''));
 if(media.protocol!=='https:'||!['anthares.us','www.anthares.us'].includes(media.hostname)||
   !media.pathname.toLowerCase().endsWith('.mp4')||media.username||media.password)throw Error('PIN_MEDIA_URL_INVALID');
 const title=String(data.title||'').normalize('NFC').trim();
 if(title.length<12||title.length>100||!title.endsWith('● Universo Anthares'))throw Error('PIN_TITLE_INVALID');
 const description=String(data.description||'').normalize('NFC').trim();
 if(description.length<15||description.length>500||!description.includes('www.anthares.us'))throw Error('PIN_DESCRIPTION_INVALID');
 return {title,description,media:media.href};
}
async function getVideo(data){
 const dir=path.join(os.tmpdir(),'anthares-pinterest-media');fs.mkdirSync(dir,{recursive:true});
 const file=path.join(dir,'pin-'+process.pid+'-'+Date.now()+'.mp4');
 const response=await fetch(data.media,{signal:AbortSignal.timeout(110000)});
 if(!response.ok)throw Error('PIN_MEDIA_FETCH_'+response.status);
 const kind=(response.headers.get('content-type')||'').toLowerCase();
 if(kind && !kind.includes('video')&&!kind.includes('octet-stream'))throw Error('PIN_MEDIA_NOT_VIDEO');
 const buf=Buffer.from(await response.arrayBuffer());
 if(buf.length<100000||buf.length>90000000)throw Error('PIN_MEDIA_SIZE_INVALID');
 fs.writeFileSync(file,buf,{flag:'wx'});return file;
}
async function setField(p,kind,val){
 // Pinterest uses DraftJS for video descriptions. It is NOT an input/textarea
 // and must be ready (contenteditable=true) before typing. Keep strict
 // identity and exact readback; never type into an ambiguous field.
 if(kind==='description'){
  const sel='[aria-label="Descreva seu Pin"][contenteditable="true"],[aria-label="Describe your Pin"][contenteditable="true"]';
  const ready=await until(()=>p.js('(()=>document.querySelectorAll('+JSON.stringify(sel)+').length===1)()'),90,1000);
  if(!ready)throw Error('PIN_DESCRIPTION_EDITOR_NOT_READY');
  const focus=await p.js('(()=>{const x=document.querySelector('+JSON.stringify(sel)+');if(!x)return false;x.focus();return document.activeElement===x})()');
  if(!focus)throw Error('PIN_DESCRIPTION_EDITOR_NOT_FOCUSED');
  await p.rpc('Input.insertText',{text:val});
  const verified=await until(()=>p.js('(()=>{const x=document.querySelector('+JSON.stringify(sel)+');return x?.innerText?.trim()})()').then(x=>x===val),14,450);
  if(!verified)throw Error('PIN_DESCRIPTION_NOT_VERIFIED');
  return;
 }
 const sel=await p.js('(()=>{const kind='+JSON.stringify(kind)+';const inputs=[...document.querySelectorAll("input:not([type=file]),textarea,[contenteditable=true]")];const matches=inputs.filter(x=>{const s=[x.getAttribute("placeholder"),x.getAttribute("aria-label"),x.getAttribute("data-test-id"),x.getAttribute("name"),x.getAttribute("id")].filter(Boolean).join(" ").toLowerCase();return kind==="title"?/t.tulo|title/.test(s):kind==="description"?/descri|description/.test(s):/link|destino|destination/.test(s)});return matches.length===1?inputs.indexOf(matches[0]):-1})()');
 if(sel<0)throw Error('PIN_'+kind.toUpperCase()+'_AMBIGUOUS');
 const focused=await p.js('(()=>{const x=[...document.querySelectorAll("input:not([type=file]),textarea,[contenteditable=true]")]['+sel+'];if(!x)return false;x.focus();if("value" in x){const setter=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(x),"value")?.set;setter?.call(x,"");x.dispatchEvent(new Event("input",{bubbles:true}))}else{document.getSelection()?.selectAllChildren(x);document.getSelection()?.deleteFromDocument()}return true})()');
 if(!focused)throw Error('PIN_FIELD_NOT_FOCUSABLE');
 await p.rpc('Input.insertText',{text:val});
 const got=await p.js('(()=>{const x=[...document.querySelectorAll("input:not([type=file]),textarea,[contenteditable=true]")]['+sel+'];return x?(x.value??x.innerText??"").trim():""})()');
 if(got!==val)throw Error('PIN_'+kind.toUpperCase()+'_NOT_VERIFIED');
}
async function selectBoard(p){
 const opened=await p.js('(()=>{const list=[...document.querySelectorAll("button,[role=button]")].filter(x=>/selecionar pasta|select board|escolher pasta|choose board|pasta/i.test((x.innerText||"")+" "+(x.getAttribute("aria-label")||"")));const x=list.find(e=>/selecionar|select|pasta|board/i.test(e.innerText||e.getAttribute("aria-label")||""));if(!x)return false;x.click();return true})()');
 if(!opened)throw Error('PIN_BOARD_DROPDOWN_MISSING');
 await pause(650);
 const selected=await p.js('(()=>{const norm=s=>String(s||"").normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/[—–]/g,"-").replace(/\\s+/g," ").trim().toLowerCase();const wanted=norm('+JSON.stringify(board)+');const x=[...document.querySelectorAll("button,[role=option],[role=menuitem],li")].filter(e=>norm(e.innerText)===wanted);if(x.length!==1)return {ok:false,matches:x.length};x[0].click();return {ok:true}})()');
 if(!selected.ok)throw Error('PIN_BOARD_NOT_UNIQUELY_FOUND_'+selected.matches);
 await pause(350);
 const verified=await p.js('(()=>{const text=document.body?.innerText||"";return text.includes('+JSON.stringify(board)+')})()');
 if(!verified)throw Error('PIN_BOARD_NOT_CONFIRMED_IN_EDITOR');
}
async function stage(p,file,data){
 const input=await until(()=>p.js('!!document.querySelector("input[type=file]")'),30,550);
 if(!input)throw Error('PIN_VIDEO_UPLOAD_INPUT_MISSING');
 const doc=await p.rpc('DOM.getDocument',{depth:-1,pierce:true});
 const node=await p.rpc('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'input[type=file]'});
 if(!node.nodeId)throw Error('PIN_VIDEO_INPUT_UNRESOLVED');
 await p.rpc('DOM.setFileInputFiles',{nodeId:node.nodeId,files:[file]});
 // Pinterest React replaces the upload input after accepting a file.
 // Never require f.files.length after DOM.setFileInputFiles: it becomes 0/null
 // even when the video preview is valid and a draft was saved.
 // Ignore videos inside the drafts sidebar to avoid false positives.
 const media=await until(()=>p.js('(()=>{const videos=[...document.querySelectorAll("video")].filter(v=>!v.closest(\'[data-test-id="storyboard-drafts-sidebar"]\'));const ready=[...document.querySelectorAll("button,[role=button]")].some(e=>/^(publicar|publish)$/i.test((e.innerText||"").trim()));return videos.length>0&&ready})()'),90,1000);
 if(!media)throw Error('PIN_VIDEO_PREVIEW_TIMEOUT');
 await setField(p,'title',data.title);
 await setField(p,'description',data.description);
 await setField(p,'link','https://www.anthares.us');
 await selectBoard(p);
 const enabled=await until(()=>p.js('(()=>{const x=[...document.querySelectorAll("button,[role=button]")].filter(e=>/^(publicar|publish)$/i.test((e.innerText||"").trim()));return x.length===1&&!x[0].disabled&&x[0].getAttribute("aria-disabled")!=="true"})()'),120,900);
 if(!enabled)throw Error('PIN_PUBLISH_BUTTON_NOT_READY');
}
function getGo(){
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(Error('GO_TIMEOUT')),115000);
  process.stdin.setEncoding('utf8');
  process.stdin.once('data',chunk=>{clearTimeout(timer);if(String(chunk).trim()==='GO')resolve();else reject(Error('GO_NOT_AUTHORIZED'))});
 });
}
async function publish(p,data){
 const clicked=await p.js('(()=>{const x=[...document.querySelectorAll("button,[role=button]")].filter(e=>/^(publicar|publish)$/i.test((e.innerText||"").trim()));if(x.length!==1||x[0].disabled)return false;x[0].click();return true})()');
 if(!clicked)throw Error('PIN_SUBMIT_BUTTON_MISSING');
 emit({phase:'SUBMIT_CLICKED'});
 const url=await until(()=>p.js('(()=>{const paths=[location.href,...[...document.querySelectorAll("a")].map(x=>x.href)];return paths.find(x=>/^https:\\/\\/(?:br\\.|www\\.)?pinterest\\.com\\/pin\\/[0-9]+\\/?(?:\\?.*)?$/.test(x))||null})()'),120,1300);
 if(!url)throw Error('PIN_SUBMITTED_WITHOUT_PERMALINK');
 const pinId=new URL(url).pathname.match(/\/pin\/([0-9]+)/)?.[1];
 if(!pinId)throw Error('PIN_PERMALINK_INVALID');
 const v=await page('https://br.pinterest.com/pin/'+pinId+'/');
 await pause(5500);
 const verified=await v.js('(()=>({path:location.pathname,title:document.title,body:document.body?.innerText.slice(0,2000)||""}))()');
 if(verified.path!=='/pin/'+pinId+'/')throw Error('PIN_PUBLIC_READBACK_FAILED');
 if(/p.gina n.o encontrada|not found/i.test(verified.body))throw Error('PIN_PUBLIC_NOT_FOUND');
 return {status:'CONFIRMED',remote_id:pinId,permalink:'https://br.pinterest.com/pin/'+pinId+'/'};
}
const mode=process.argv[2]||'--preflight';
let mediaFile=null;
try{
 await pruneOwnedPinterestTabs();
 const p=await page(editor);
 const auth=await session(p);
 if(mode==='--preflight'){emit({status:'READY',account_id:account,editor_url:auth.href,details:await inspect(p)})}
 else if(mode==='--publish'){
  const job=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
  const data=validate(job);
  mediaFile=await getVideo(data);
  await stage(p,mediaFile,data);
  emit({phase:'PREPARED',account_id:account,board});
  await getGo();
  emit(await publish(p,data));
 }else throw Error('INVALID_MODE');
}catch(e){emit({status:'BLOCKED_OR_UNCERTAIN',reason:String(e.message||e).slice(0,180)});process.exitCode=2}
finally{
 for(const p of pages.reverse()){try{await p.close()}catch{}}
 if(mediaFile){try{fs.unlinkSync(mediaFile)}catch{}}
}
