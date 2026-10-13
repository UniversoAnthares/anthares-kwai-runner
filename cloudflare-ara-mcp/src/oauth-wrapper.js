import originalWorker from './index.js';
export { GatewayState } from './index.js';

const ORIGIN='https://anthares-ara-mcp.anthares1.workers.dev';
const CONTROL='https://anthares-ara-backup.anthares1.workers.dev';
const DEFAULT_DEVICE='DESKTOP-FTDK0HP';
const FALLBACK_DEVICE='DESKTOP-FTDK0HP-SYSTEM';
const SCOPES=new Set(['ara.read','ara.write']);
const te=new TextEncoder();

function b64urlBytes(bytes){let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function rand(n=32){const b=new Uint8Array(n);crypto.getRandomValues(b);return b64urlBytes(b);}
function eq(a,b){a=String(a);b=String(b);if(a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
async function sha256b64(v){return b64urlBytes(new Uint8Array(await crypto.subtle.digest('SHA-256',te.encode(String(v)))));}
function esc(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));}
function json(data,status=200,headers={}){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff',...headers}});}
function html(body,status=200){return new Response(body,{status,headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store','content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",'referrer-policy':'no-referrer','x-content-type-options':'nosniff'}});}
function st(env){return env.GATEWAY_STATE.get(env.GATEWAY_STATE.idFromName('global'));}
function validClient(v){return v==='https://chatgpt.com/oauth/client.json'||/^https:\/\/chatgpt\.com\/oauth\/[A-Za-z0-9_-]{8,}\/client\.json$/.test(v||'');}
function validRedirect(v){return v==='https://chatgpt.com/connector_platform_oauth_redirect'||/^https:\/\/chatgpt\.com\/connector\/oauth\/[A-Za-z0-9_-]+$/.test(v||'');}
function parseScopes(v){const xs=String(v||'ara.read ara.write').trim().split(/\s+/).filter(Boolean);if(!xs.length||xs.some(x=>!SCOPES.has(x)))return null;return[...new Set(xs)];}

async function control(env,path,{method='GET',body,timeoutMs=30000}={}){
  const raw=body===undefined?'':JSON.stringify(body);
  const sig=await st(env).signControl(method,path,raw);
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    return await fetch(CONTROL+path,{method,headers:{'content-type':'application/json','x-ara-timestamp':sig.timestamp,'x-ara-signature':sig.signature,'x-ara-signer':'anthares-remote-mcp'},body:body===undefined?undefined:raw,signal:controller.signal});
  }finally{clearTimeout(timer);}
}
async function controlJson(env,path,opts){const r=await control(env,path,opts);const raw=await r.text();let data={};try{data=raw?JSON.parse(raw):{};}catch{data={raw};}if(!r.ok)throw new Error(`control ${r.status}: ${data.error||data.raw||'request failed'}`);return data;}
async function status(env,device=DEFAULT_DEVICE){return controlJson(env,`/v1/mcp/status?device_id=${encodeURIComponent(device)}`);}
async function resolveDevice(env){try{if((await status(env,DEFAULT_DEVICE)).connected)return DEFAULT_DEVICE;}catch{}try{if((await status(env,FALLBACK_DEVICE)).connected)return FALLBACK_DEVICE;}catch{}return DEFAULT_DEVICE;}
async function execute(env,type,args={},timeout=20,device=DEFAULT_DEVICE){return controlJson(env,'/v1/mcp/execute',{method:'POST',timeoutMs:(Number(timeout)+12)*1000,body:{device_id:device,type,args,timeout_seconds:Math.max(1,Math.min(Number(timeout)||20,120)),idempotency_key:`cfoauth-${crypto.randomUUID()}`}});}

function outputContainsCode(out,code){
  const values=[];
  if(typeof out==='string'){
    values.push(out);
    try{const obj=JSON.parse(out);if(obj&&typeof obj==='object')values.push(obj.text,obj.stdout,obj.output);}catch{}
  }else if(out&&typeof out==='object')values.push(out.text,out.stdout,out.output);
  return values.some(v=>typeof v==='string'&&v.trim()===code);
}

async function sendApproval(env,code){
  try{
    const device=await resolveDevice(env);
    if(!(await status(env,device)).connected)return false;
    const set=await execute(env,'clipboard_set',{text:code},20,device);
    if(!set.ok||set.status!=='done')return false;
    const read=await execute(env,'clipboard_get',{},20,device);
    return !!(read.ok&&read.status==='done'&&outputContainsCode(read.output,code));
  }catch{return false;}
}

// ChatGPT may retry the authorization GET while the user is already looking at
// the first page. A fresh random code on every GET can therefore overwrite the
// clipboard with a code that belongs to a different pending transaction. Use a
// secret-derived short-lived code for the whole 10-minute window so concurrent
// retries cannot race each other. The code is still delivered only through the
// authenticated device channel and is consumed once on successful approval.
async function currentApproval(env){
  const bucket=Math.floor(Date.now()/600000);
  const mac=await st(env).hmac(`oauth-approval-v2:${bucket}`);
  return `ARA-${mac.slice(0,10)}`;
}

function approvalPage(tx,message='Cole o código que foi enviado à área de transferência deste computador.'){
  return html(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Remote</title></head><body><main><h1>Anthares Remote</h1><p>${esc(message)}</p><p>O código Anthares sempre começa com <strong>ARA-</strong>. Se o conteúdo colado não começar assim, não autorize.</p><form method="post" action="/oauth/authorize"><input type="hidden" name="tx" value="${esc(tx)}"><label>Código <input type="password" name="approval" pattern="ARA-[A-Za-z0-9_-]{10}" autocomplete="one-time-code" required autofocus></label><button type="submit">Autorizar</button></form></main></body></html>`);
}

async function authorizeGet(req,env,u){
  const cid=u.searchParams.get('client_id')||'';
  const red=u.searchParams.get('redirect_uri')||'';
  const challenge=u.searchParams.get('code_challenge')||'';
  const method=u.searchParams.get('code_challenge_method')||'';
  const resource=u.searchParams.get('resource')||ORIGIN;
  const scopes=parseScopes(u.searchParams.get('scope'));
  if(!validClient(cid)||!validRedirect(red)||u.searchParams.get('response_type')!=='code'||method!=='S256'||challenge.length<43||resource!==ORIGIN||!scopes)return json({error:'invalid_request'},400);
  const approval=await currentApproval(env);
  const now=Math.floor(Date.now()/1000);
  const tx=await st(env).signToken({typ:'oauth_pending',iss:ORIGIN,aud:ORIGIN,iat:now,exp:now+600,jti:rand(16),clientId:cid,redirectUri:red,challenge,scopes,scp:scopes,state:u.searchParams.get('state')||'',approvalHash:await sha256b64(approval)});
  if(!(await sendApproval(env,approval)))return json({error:'device_authorization_unavailable'},503);
  return approvalPage(tx);
}

async function authorizePost(req,env){
  const f=await req.formData();
  const tx=String(f.get('tx')||'');
  const approval=String(f.get('approval')||'').trim();
  const p=await st(env).verifyToken(tx,'oauth_pending');
  if(!p)return json({error:'authorization_expired'},400);
  const approvalHash=await sha256b64(approval);
  if(!approval.startsWith('ARA-')||!eq(approvalHash,p.approvalHash))return approvalPage(tx,'O conteúdo colado não é o código Anthares desta autorização. O clipboard pode ter sido substituído por outro conteúdo. Inicie novamente a conexão e cole apenas um código que comece com ARA-.'),403);
  if(!(await st(env).consume('oauth_approval',p.approvalHash,p.exp)))return json({error:'authorization_already_used'},409);
  const now=Math.floor(Date.now()/1000);
  const code=await st(env).signToken({typ:'oauth_code',iss:ORIGIN,aud:ORIGIN,iat:now,exp:now+300,jti:rand(16),clientId:p.clientId,redirectUri:p.redirectUri,challenge:p.challenge,scopes:p.scopes,scp:p.scopes});
  const target=new URL(p.redirectUri);
  target.searchParams.set('code',code);
  if(p.state)target.searchParams.set('state',p.state);
  target.searchParams.set('iss',ORIGIN);
  return Response.redirect(target.toString(),302);
}

export default {
  async fetch(req,env,ctx){
    const u=new URL(req.url);
    if(u.pathname==='/oauth/authorize'&&req.method==='GET')return authorizeGet(req,env,u);
    if(u.pathname==='/oauth/authorize'&&req.method==='POST')return authorizePost(req,env);
    return originalWorker.fetch(req,env,ctx);
  }
};
