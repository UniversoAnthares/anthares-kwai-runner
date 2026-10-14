import puppeteer from "@cloudflare/puppeteer";
import app, { BrowserState } from "./entry.js";

export { BrowserState };

const GENERIC_VERSION = "2026-10-14-generic-browser-v3";
const OWNER_COOKIE = "anthares_reserva_owner";
const REDIRECT_URI = "http://127.0.0.1:59231/callback";
const ALLOWED_HOSTS = new Set(["app.circleci.com", "circleci.com", "github.com"]);
const te = new TextEncoder();
const td = new TextDecoder();

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"},
});
const html = (body, status = 200) => new Response(body, {
  status,
  headers: {"content-type":"text/html; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff","referrer-policy":"no-referrer","content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"},
});
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

function sameSecret(a, b) {
  a = String(a || ""); b = String(b || "");
  if (!a || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
function authorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}
function cookieValue(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return "";
}
const b64url = bytes => {
  let s = ""; for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");
};
const fromB64url = value => {
  let s=String(value||"").replace(/-/g,"+").replace(/_/g,"/"); while(s.length%4)s+="=";
  const raw=atob(s); return Uint8Array.from(raw,c=>c.charCodeAt(0));
};
async function hmac(env, value) {
  const key=await crypto.subtle.importKey("raw",te.encode(env.ANTHARES_RESERVA_TOKEN),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  return b64url(new Uint8Array(await crypto.subtle.sign("HMAC",key,te.encode(value))));
}
async function ownerAuthorized(request, env) {
  if (!env.ANTHARES_RESERVA_TOKEN) return false;
  const token=cookieValue(request,OWNER_COOKIE); const [payload,sig,extra]=String(token).split(".");
  if(!payload||!sig||extra!==undefined||!sameSecret(sig,await hmac(env,payload))) return false;
  try { const p=JSON.parse(td.decode(fromB64url(payload))); return Number(p.exp)>Math.floor(Date.now()/1000); } catch { return false; }
}
async function oauthKey(env) {
  const raw=new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode("anthares-circleci-oauth-v1:"+env.ANTHARES_RESERVA_TOKEN)));
  return crypto.subtle.importKey("raw",raw,"AES-GCM",false,["encrypt","decrypt"]);
}
async function sealOAuthState(env, payload) {
  const iv=crypto.getRandomValues(new Uint8Array(12));
  const cipher=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv,additionalData:te.encode("circleci-oauth-state-v1")},await oauthKey(env),te.encode(JSON.stringify(payload))));
  const out=new Uint8Array(iv.length+cipher.length); out.set(iv); out.set(cipher,iv.length); return b64url(out);
}
async function openOAuthState(env, value) {
  const blob=fromB64url(value); if(blob.length<29) throw new Error("invalid_oauth_state");
  const clear=await crypto.subtle.decrypt({name:"AES-GCM",iv:blob.slice(0,12),additionalData:te.encode("circleci-oauth-state-v1")},await oauthKey(env),blob.slice(12));
  const p=JSON.parse(td.decode(clear)); if(Number(p.exp)<=Math.floor(Date.now()/1000)) throw new Error("oauth_state_expired"); return p;
}

function genericStub(env) { return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("generic-browser")); }
async function readSessionId(env) { const r=await genericStub(env).fetch("https://state/session"); return String((await r.json()).session_id||""); }
async function writeSessionId(env,id) { await genericStub(env).fetch("https://state/session",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({session_id:id||""})}); }
async function connectOrLaunch(env) {
  const existing=await readSessionId(env);
  if(existing){try{return {browser:await puppeteer.connect(env.BROWSER,existing),reused:true};}catch{await writeSessionId(env,"");}}
  const browser=await puppeteer.launch(env.BROWSER,{keep_alive:600000}); await writeSessionId(env,browser.sessionId()); return {browser,reused:false};
}
async function liveView(page) {
  const cdp=await page.createCDPSession();
  try { const r=await cdp.send("Cloudflare.getLiveView",{mode:"full",expiresInMs:600000}); return String(r.devtoolsFrontendUrl||""); }
  finally { await cdp.detach().catch(()=>{}); }
}
async function navigate(env,target) {
  let parsed; try{parsed=new URL(target);}catch{return {ok:false,error:"invalid_url"};}
  if(parsed.protocol!=="https:"||!ALLOWED_HOSTS.has(parsed.hostname.toLowerCase())) return {ok:false,error:"host_not_allowed"};
  const opened=await connectOrLaunch(env); const browser=opened.browser;
  try { const pages=await browser.pages(); const page=pages[0]||await browser.newPage(); await page.goto(parsed.toString(),{waitUntil:"domcontentloaded",timeout:20000}); const title=await page.title().catch(()=>""); const live_view_url=await liveView(page); await browser.disconnect(); return {ok:true,reused:opened.reused,url:page.url(),title,live_view_url}; }
  catch(err){await browser.disconnect().catch(()=>{}); return {ok:false,error:"navigation_failed",detail:String(err?.message||err).slice(0,180)};}
}
async function closeGeneric(env) {
  const id=await readSessionId(env); if(!id)return {ok:true,active:false};
  try{const browser=await puppeteer.connect(env.BROWSER,id); await browser.close();}catch{}
  await writeSessionId(env,""); return {ok:true,active:false};
}

async function circleOauthStart(env) {
  const register=await fetch("https://app.circleci.com/oauth/register",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({client_name:"Anthares CircleCI Recovery",redirect_uris:[REDIRECT_URI],grant_types:["authorization_code"],response_types:["code"]})});
  if(register.status!==201) return {ok:false,error:"circleci_client_registration_failed",status:register.status,detail:(await register.text()).slice(0,300)};
  const reg=await register.json(); const clientId=String(reg.client_id||""); if(!clientId)return {ok:false,error:"circleci_client_id_missing"};
  const verifier=b64url(crypto.getRandomValues(new Uint8Array(48)));
  const challenge=b64url(new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode(verifier))));
  const state=await sealOAuthState(env,{client_id:clientId,verifier,redirect_uri:REDIRECT_URI,exp:Math.floor(Date.now()/1000)+900});
  const auth=new URL("https://app.circleci.com/oauth/authorize");
  auth.searchParams.set("response_type","code"); auth.searchParams.set("client_id",clientId); auth.searchParams.set("redirect_uri",REDIRECT_URI); auth.searchParams.set("code_challenge",challenge); auth.searchParams.set("code_challenge_method","S256"); auth.searchParams.set("state",state);
  const opened=await connectOrLaunch(env); const browser=opened.browser;
  try { const pages=await browser.pages(); const page=pages[0]||await browser.newPage(); await page.goto(auth.toString(),{waitUntil:"domcontentloaded",timeout:20000}); const live=await liveView(page); await browser.disconnect(); return {ok:true,live_view_url:live}; }
  catch(err){await browser.disconnect().catch(()=>{}); return {ok:false,error:"circleci_authorize_navigation_failed",detail:String(err?.message||err).slice(0,180)};}
}
async function circleOauthFinish(env) {
  const id=await readSessionId(env); if(!id)return {ok:false,error:"no_circleci_oauth_session"};
  let browser;
  try {
    browser=await puppeteer.connect(env.BROWSER,id); const pages=await browser.pages(); const page=pages[0]||await browser.newPage(); const current=page.url();
    let callback; try{callback=new URL(current);}catch{return {ok:false,error:"invalid_callback_url",current};}
    const code=callback.searchParams.get("code")||""; const state=callback.searchParams.get("state")||"";
    if(!code||!state)return {ok:false,error:"circleci_authorization_not_finished",current};
    const saved=await openOAuthState(env,state);
    const form=new URLSearchParams({grant_type:"authorization_code",code,client_id:saved.client_id,redirect_uri:saved.redirect_uri,code_verifier:saved.verifier});
    const tokenResp=await fetch("https://app.circleci.com/oauth/token",{method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},body:form.toString()});
    if(!tokenResp.ok)return {ok:false,error:"circleci_token_exchange_failed",status:tokenResp.status,detail:(await tokenResp.text()).slice(0,300)};
    const token=String((await tokenResp.json()).access_token||""); if(!token)return {ok:false,error:"circleci_access_token_missing"};
    const follow=await fetch("https://circleci.com/api/v1.1/project/github/UniversoAnthares/anthares-wordpress/follow",{method:"POST",headers:{"Circle-Token":token}});
    const followText=await follow.text(); if(!follow.ok)return {ok:false,error:"circleci_follow_failed",status:follow.status,detail:followText.slice(0,300)};
    const trigger=await fetch("https://circleci.com/api/v2/project/gh/UniversoAnthares/anthares-wordpress/pipeline",{method:"POST",headers:{"Circle-Token":token,"content-type":"application/json"},body:JSON.stringify({branch:"main"})});
    const triggerText=await trigger.text(); if(trigger.status!==201)return {ok:false,error:"circleci_trigger_failed",status:trigger.status,detail:triggerText.slice(0,300)};
    let pipelineId=""; try{pipelineId=String(JSON.parse(triggerText).id||"");}catch{}
    return {ok:true,followed:true,pipeline_triggered:true,pipeline_id:pipelineId};
  } finally { if(browser)await browser.close().catch(()=>{}); await writeSessionId(env,"").catch(()=>{}); }
}
function circlePage(message="",live="") {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares · CircleCI</title></head><body style="font-family:system-ui;max-width:760px;margin:40px auto;padding:0 20px"><h1>Ativação CircleCI</h1>${message?`<p><strong>${esc(message)}</strong></p>`:""}${live?`<p><a href="${esc(live)}" target="_blank" rel="noopener noreferrer">Abrir autorização CircleCI</a></p>`:""}<form method="post" action="/owner/circleci/start"><button type="submit">Iniciar autorização segura</button></form><form method="post" action="/owner/circleci/finish"><button type="submit">Concluir e ativar anthares-wordpress</button></form><p>O token é usado somente para seguir o projeto e disparar o primeiro pipeline; não é exibido nem persistido.</p><p><a href="/owner">Voltar</a></p></body></html>`;
}

export default {
  async fetch(request,env,ctx) {
    const url=new URL(request.url);
    if(url.pathname==="/health"&&request.method==="GET"){
      let base={}; try{const r=await app.fetch(request,env,ctx);if(r.ok)base=await r.json();}catch{}
      return json({...base,ok:true,service:"anthares-reserva-browser",generic_browser:true,generic_browser_version:GENERIC_VERSION,generic_browser_allowed_hosts:[...ALLOWED_HOSTS],circleci_oauth_activation:true,browser_binding:!!env.BROWSER,durable_state_binding:!!env.BROWSER_STATE,render_required:false});
    }
    if(url.pathname==="/browser/navigate"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401); let body;try{body=await request.json();}catch{return json({error:"invalid_json"},400);} const result=await navigate(env,String(body?.url||""));return json(result,result.ok?200:400);
    }
    if(url.pathname==="/browser/close"&&request.method==="POST"){
      if(!authorized(request,env))return json({error:"unauthorized"},401);return json(await closeGeneric(env));
    }
    if(url.pathname==="/owner/circleci"&&request.method==="GET"){
      if(!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});return html(circlePage());
    }
    if(url.pathname==="/owner/circleci/start"&&request.method==="POST"){
      if(!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});const r=await circleOauthStart(env);return html(circlePage(r.ok?"Autorização preparada. Abra o navegador remoto, entre no CircleCI se necessário, escolha Write e clique Allow.":`Falha: ${r.error}`,r.live_view_url||""),r.ok?200:500);
    }
    if(url.pathname==="/owner/circleci/finish"&&request.method==="POST"){
      if(!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});const r=await circleOauthFinish(env);return html(circlePage(r.ok?`CircleCI ativado. Pipeline: ${r.pipeline_id||"disparado"}`:`Ainda não concluído: ${r.error}`),r.ok?200:409);
    }
    return app.fetch(request,env,ctx);
  },
};
