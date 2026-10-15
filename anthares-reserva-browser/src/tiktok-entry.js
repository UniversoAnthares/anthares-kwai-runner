import puppeteer from "@cloudflare/puppeteer";
import app, { BrowserState } from "./generic-entry.js";

export { BrowserState };

const VERSION = "2026-10-14-tiktok-browser-v1";
const PROFILE_URL = "https://www.tiktok.com/@universo.anthares";
const STUDIO_URL = "https://www.tiktok.com/tiktokstudio";
const te = new TextEncoder();
const td = new TextDecoder();

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"},
});

function sameSecret(a, b) {
  a=String(a||""); b=String(b||"");
  if(!a || a.length!==b.length) return false;
  let diff=0; for(let i=0;i<a.length;i++) diff|=a.charCodeAt(i)^b.charCodeAt(i);
  return diff===0;
}
function authorized(request, env) {
  const supplied=(request.headers.get("authorization")||"").replace(/^Bearer /i,"");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}
const b64url = bytes => {
  let s=""; for(const b of bytes)s+=String.fromCharCode(b);
  return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");
};
const fromB64url = value => {
  let s=String(value||"").replace(/-/g,"+").replace(/_/g,"/"); while(s.length%4)s+="=";
  const raw=atob(s); return Uint8Array.from(raw,c=>c.charCodeAt(0));
};
async function stateKey(env) {
  if(!env.ANTHARES_RESERVA_TOKEN) throw new Error("reserve_token_unavailable");
  const raw=new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode("anthares-tiktok-browser-state-v1:"+env.ANTHARES_RESERVA_TOKEN)));
  return crypto.subtle.importKey("raw",raw,"AES-GCM",false,["encrypt","decrypt"]);
}
async function encryptState(env,state) {
  const iv=crypto.getRandomValues(new Uint8Array(12));
  const cipher=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv,additionalData:te.encode("anthares-tiktok-browser-state-v1")},await stateKey(env),te.encode(JSON.stringify(state))));
  const out=new Uint8Array(iv.length+cipher.length); out.set(iv); out.set(cipher,iv.length); return b64url(out);
}
async function decryptState(env,value) {
  const blob=fromB64url(value); if(blob.length<29) throw new Error("invalid_state_blob");
  const clear=await crypto.subtle.decrypt({name:"AES-GCM",iv:blob.slice(0,12),additionalData:te.encode("anthares-tiktok-browser-state-v1")},await stateKey(env),blob.slice(12));
  return JSON.parse(td.decode(clear));
}

function stub(env){return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("tiktok-browser"));}
async function readState(env){const r=await stub(env).fetch("https://state/state");return r.json();}
async function writeState(env,state){const ciphertext=await encryptState(env,state);const r=await stub(env).fetch("https://state/state",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({ciphertext})});return r.json();}
async function readSessionId(env){const r=await stub(env).fetch("https://state/session");return String((await r.json()).session_id||"");}
async function writeSessionId(env,id){await stub(env).fetch("https://state/session",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({session_id:id||""})});}

function normalizeState(input){
  const source=(input&&typeof input==="object"&&input.state&&typeof input.state==="object")?input.state:input;
  if(!source||typeof source!=="object") throw new Error("invalid_state");
  const cookies=(Array.isArray(source.cookies)?source.cookies:[]).filter(c=>c&&c.name&&typeof c.value==="string"&&/(^|\.)tiktok\.com$/i.test(String(c.domain||"").replace(/^\./,""))).slice(0,256).map(c=>{
    const out={}; for(const k of ["name","value","domain","path","expires","httpOnly","secure","sameSite"]) if(c[k]!==undefined)out[k]=c[k]; return out;
  });
  if(!cookies.length) throw new Error("no_tiktok_cookies");
  const origins=Array.isArray(source.origins)?source.origins.filter(o=>o&&typeof o.origin==="string"&&/(^|\.)tiktok\.com$/i.test((()=>{try{return new URL(o.origin).hostname}catch{return ""}})())).slice(0,16):[];
  return {schema:"anthares.tiktok-browser-state.v1",cookies,origins,saved_at:new Date().toISOString()};
}
async function restoreState(env,page){
  const record=await readState(env); if(!record.available)return {status:"empty",available:false};
  let state; try{state=await decryptState(env,record.ciphertext);}catch{return {status:"decrypt_failed",available:true};}
  await page.goto("https://www.tiktok.com/",{waitUntil:"domcontentloaded",timeout:20000});
  if(Array.isArray(state.cookies)&&state.cookies.length)await page.setCookie(...state.cookies).catch(()=>{});
  const origin=(Array.isArray(state.origins)?state.origins:[]).find(o=>o&&Array.isArray(o.localStorage)&&String(o.origin||"").includes("tiktok.com"));
  if(origin){
    const values={}; for(const item of origin.localStorage.slice(0,256)){if(item&&item.name!=null&&item.value!=null)values[String(item.name)]=String(item.value);}
    await page.evaluate(v=>{try{localStorage.clear();for(const [k,val] of Object.entries(v))localStorage.setItem(k,val);}catch{}},values).catch(()=>{});
  }
  await page.reload({waitUntil:"domcontentloaded",timeout:20000}).catch(()=>{});
  return {status:"restored",available:true,cookie_count:state.cookies?.length||0};
}
async function captureState(env,page){
  const cookies=(await page.cookies().catch(()=>[])).filter(c=>/(^|\.)tiktok\.com$/i.test(String(c.domain||"").replace(/^\./,""))).slice(0,256);
  const localStorage=await page.evaluate(()=>{const out=[];try{for(let i=0;i<Math.min(localStorage.length,256);i++){const name=localStorage.key(i);if(name!==null)out.push({name,value:localStorage.getItem(name)});}}catch{}return out;}).catch(()=>[]);
  return writeState(env,{schema:"anthares.tiktok-browser-state.v1",cookies,origins:[{origin:"https://www.tiktok.com",localStorage}],saved_at:new Date().toISOString()});
}
async function connectOrLaunch(env){
  const existing=await readSessionId(env);
  if(existing){try{return {browser:await puppeteer.connect(env.BROWSER,existing),reused:true};}catch{await writeSessionId(env,"");}}
  const browser=await puppeteer.launch(env.BROWSER,{keep_alive:600000}); await writeSessionId(env,browser.sessionId()); return {browser,reused:false};
}
async function pageFor(browser){const pages=await browser.pages();return pages.find(p=>p.url().includes("tiktok.com"))||pages[0]||await browser.newPage();}
async function liveView(page){const cdp=await page.createCDPSession();try{const r=await cdp.send("Cloudflare.getLiveView",{mode:"full",expiresInMs:600000});return String(r.devtoolsFrontendUrl||"");}finally{await cdp.detach().catch(()=>{});}}
async function inspect(page){
  return page.evaluate(()=>{
    const body=(document.body?.innerText||"").slice(0,30000).toLowerCase();
    const links=[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')||"");
    const loginGate=!!document.querySelector('input[type="password"]')||/\blog in\b|\blogin\b|\bfazer login\b|\bentrar\b/.test(body);
    const handle=body.includes("universo.anthares")||links.some(h=>h.includes("/@universo.anthares"));
    const upload=!!document.querySelector('input[type="file"]')||/carregar|upload|publicar|postar/.test(body);
    return {host:location.hostname.toLowerCase(),path:location.pathname,login_gate:loginGate,account_marker:handle,upload_marker:upload};
  });
}
async function verify(env){
  let browser; let restore={status:"reused",available:true};
  try{
    const opened=await connectOrLaunch(env); browser=opened.browser; const page=await pageFor(browser);
    if(!opened.reused)restore=await restoreState(env,page);
    if(!restore.available)return {ok:true,persisted_state:false,identity_verified:false,studio_verified:false,session_state:"no_persisted_state",restore_status:restore.status};
    await page.goto(PROFILE_URL,{waitUntil:"domcontentloaded",timeout:25000}); await new Promise(r=>setTimeout(r,2500));
    const profile=await inspect(page);
    const identity=!profile.login_gate&&profile.account_marker&&profile.host.endsWith("tiktok.com");
    if(!identity)return {ok:true,persisted_state:true,identity_verified:false,studio_verified:false,session_state:profile.login_gate?"unauthenticated":"identity_unproven",restore_status:restore.status,evidence:profile};
    await page.goto(STUDIO_URL,{waitUntil:"domcontentloaded",timeout:25000}); await new Promise(r=>setTimeout(r,3000));
    const studio=await inspect(page); const studioOk=!studio.login_gate&&studio.host.endsWith("tiktok.com");
    const stored=await captureState(env,page);
    return {ok:true,persisted_state:true,identity_verified:true,studio_verified:studioOk,session_state:studioOk?"authenticated":"profile_only",restore_status:restore.status,state_refreshed:!!stored.stored,evidence:profile,studio:{host:studio.host,path:studio.path,login_gate:studio.login_gate,upload_marker:studio.upload_marker}};
  }catch(err){return {ok:false,error:"tiktok_session_verify_failed",detail:String(err?.message||err).slice(0,180)};}
  finally{if(browser)await browser.close().catch(()=>{});await writeSessionId(env,"").catch(()=>{});}
}
async function mintLive(env){let browser;try{const opened=await connectOrLaunch(env);browser=opened.browser;const page=await pageFor(browser);if(!opened.reused)await restoreState(env,page);if(!page.url().includes("tiktok.com"))await page.goto(STUDIO_URL,{waitUntil:"domcontentloaded",timeout:25000});const url=await liveView(page);await browser.disconnect();return {ok:true,live_view_url:url,reused:opened.reused};}catch(err){if(browser)await browser.close().catch(()=>{});await writeSessionId(env,"").catch(()=>{});return {ok:false,error:"live_view_failed",detail:String(err?.message||err).slice(0,160)};}}
async function saveClose(env){const id=await readSessionId(env);if(!id)return {ok:true,active:false};let browser;try{browser=await puppeteer.connect(env.BROWSER,id);const page=await pageFor(browser);const stored=await captureState(env,page);return {ok:!!stored.stored,saved_at:stored.saved_at||null};}finally{if(browser)await browser.close().catch(()=>{});await writeSessionId(env,"");}}

export default {
  async fetch(request,env,ctx){
    const url=new URL(request.url);
    if(url.pathname==="/health"&&request.method==="GET"){
      const r=await app.fetch(request,env,ctx); let base={}; if(r.ok)base=await r.json();
      return json({...base,ok:true,tiktok_session_recovery:true,tiktok_browser_version:VERSION,tiktok_profile:"universo.anthares",render_required:false});
    }
    if(url.pathname==="/tiktok/import"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401);
      try{const body=await request.json();const state=normalizeState(body);const stored=await writeState(env,state);return json({ok:!!stored.stored,stored:!!stored.stored,cookie_count:state.cookies.length,saved_at:stored.saved_at||null});}catch(err){return json({ok:false,error:"invalid_tiktok_state",detail:String(err?.message||err).slice(0,120)},400);}
    }
    if(url.pathname==="/tiktok/session/verify"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401);const result=await verify(env);return json(result,result.ok?200:503);
    }
    if(url.pathname==="/tiktok/session/live"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401);const result=await mintLive(env);return json(result,result.ok?200:503);
    }
    if(url.pathname==="/tiktok/session/save"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401);return json(await saveClose(env));
    }
    return app.fetch(request,env,ctx);
  },
};
