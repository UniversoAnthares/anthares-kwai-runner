import baseApp, { BrowserState } from "./tiktok-owner-entry.js";

export { BrowserState };

const OWNER_COOKIE = "anthares_reserva_owner";
const NF_BASE = "https://anthares-tiktok-worker.anthares1.workers.dev";
const te = new TextEncoder();
const td = new TextDecoder();

const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
function sameSecret(a,b){a=String(a||"");b=String(b||"");if(!a||a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
function machineAuthorized(request,env){const supplied=(request.headers.get("authorization")||"").replace(/^Bearer /i,"");return sameSecret(supplied,env.ANTHARES_RESERVA_TOKEN);}
function cookieValue(request,name){for(const part of (request.headers.get("cookie")||"").split(";")){const [k,...rest]=part.trim().split("=");if(k===name)return rest.join("=");}return "";}
const b64url=bytes=>{let s="";for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");};
const fromB64url=value=>{let s=String(value||"").replace(/-/g,"+").replace(/_/g,"/");while(s.length%4)s+="=";const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0));};
async function hmac(env,value){if(!env.ANTHARES_RESERVA_TOKEN)return "";const key=await crypto.subtle.importKey("raw",te.encode(env.ANTHARES_RESERVA_TOKEN),{name:"HMAC",hash:"SHA-256"},false,["sign"]);return b64url(new Uint8Array(await crypto.subtle.sign("HMAC",key,te.encode(value))));}
async function ownerAuthorized(request,env){const token=cookieValue(request,OWNER_COOKIE);const [payload,sig,extra]=String(token).split(".");if(!payload||!sig||extra!==undefined)return false;if(!sameSecret(sig,await hmac(env,payload)))return false;try{const p=JSON.parse(td.decode(fromB64url(payload)));return Number(p.exp)>Math.floor(Date.now()/1000);}catch{return false;}}

const html = (body,status=200)=>new Response(body,{status,headers:{"content-type":"text/html; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff","referrer-policy":"no-referrer","content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"}});
const json = (body,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}});

async function stateKey(env){if(!env.ANTHARES_RESERVA_TOKEN)throw new Error("reserve_token_unavailable");const raw=new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode("anthares-tiktok-browser-state-v1:"+env.ANTHARES_RESERVA_TOKEN)));return crypto.subtle.importKey("raw",raw,"AES-GCM",false,["encrypt","decrypt"]);}
async function encryptState(env,state){const iv=crypto.getRandomValues(new Uint8Array(12));const cipher=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv,additionalData:te.encode("anthares-tiktok-browser-state-v1")},await stateKey(env),te.encode(JSON.stringify(state))));const out=new Uint8Array(iv.length+cipher.length);out.set(iv);out.set(cipher,iv.length);return b64url(out);}
async function decryptState(env,value){const blob=fromB64url(value);if(blob.length<29)throw new Error("invalid_state_blob");const clear=await crypto.subtle.decrypt({name:"AES-GCM",iv:blob.slice(0,12),additionalData:te.encode("anthares-tiktok-browser-state-v1")},await stateKey(env),blob.slice(12));return JSON.parse(td.decode(clear));}
function stub(env){return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("tiktok-browser"));}
async function readPlainState(env){const r=await stub(env).fetch("https://state/state");const d=await r.json();if(!d.available)return null;try{return await decryptState(env,d.ciphertext);}catch{return null;}}
async function writePlainState(env,state){const ciphertext=await encryptState(env,state);const r=await stub(env).fetch("https://state/state",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({ciphertext})});return r.json();}

async function nf(env,path,{method="GET",body}={}){
  if(!env.NORTHFLANK_BROWSER_TOKEN) return {ok:false,error:"northflank_browser_token_missing",_status:503};
  const init={method,headers:{"authorization":"Bearer "+env.NORTHFLANK_BROWSER_TOKEN,"accept":"application/json","user-agent":"AntharesBrowserBridge/1.0"}};
  if(body!==undefined){init.headers["content-type"]="application/json";init.body=JSON.stringify(body);}
  try{
    const r=await (env.TIKTOK_WORKER ? env.TIKTOK_WORKER.fetch(NF_BASE+path,init) : fetch(NF_BASE+path,init));let d={};try{d=await r.json();}catch{d={ok:false,error:"invalid_upstream_json"};}d._status=r.status;return d;
  }catch(err){return {ok:false,error:"northflank_browser_unavailable",detail:String(err?.message||err).slice(0,160),_status:503};}
}
async function ensureStarted(env){
  const current=await nf(env,"/interactive-browser/status");
  if(current.ok&&current.active&&current.responsive!==false)return {ok:true,active:true,starting:false};
  if(current.ok&&current.starting)return {ok:true,active:false,starting:true};
  const state=await readPlainState(env);
  return nf(env,"/interactive-browser/start-async",{method:"POST",body:state?{state}:{}});
}
async function shot(env){const d=await nf(env,"/interactive-browser/screenshot");return d.ok?d:null;}
function normalizeState(input){if(!input||typeof input!=="object")throw new Error("invalid_state");const cookies=(Array.isArray(input.cookies)?input.cookies:[]).filter(c=>c&&c.name&&typeof c.value==="string"&&String(c.domain||"").toLowerCase().includes("tiktok.com")).slice(0,256);if(!cookies.length)throw new Error("no_tiktok_cookies");const origins=Array.isArray(input.origins)?input.origins.slice(0,16):[];return {schema:"anthares.tiktok-browser-state.v1",cookies,origins,saved_at:new Date().toISOString()};}

function browserPage(message="",screen=null,verify=null,drag=null){
  const img=screen?.image_b64?`<div class="remote-wrap"><p><strong>Arraste diretamente na imagem: pressione, mova e solte. Clique simples continua funcionando.</strong></p><img id="remote-shot" draggable="false" src="data:${esc(screen.mime||"image/jpeg")};base64,${screen.image_b64}" width="1365" height="768" alt="TikTok remoto"><div id="gesture-status" role="status" aria-live="polite">Pronto para clicar ou arrastar.</div></div>`:"<p>Nenhuma imagem disponível. Inicie a sessão.</p>";
  const gestureScript=screen?.image_b64?`<script>
  (()=>{
    const el=document.getElementById("remote-shot"),status=document.getElementById("gesture-status");
    let start=null,active=false,busy=false;
    function pos(e){const r=el.getBoundingClientRect();return {x:Math.max(0,Math.min(1365,Math.round((e.clientX-r.left)*1365/r.width))),y:Math.max(0,Math.min(768,Math.round((e.clientY-r.top)*768/r.height)))};}
    el.addEventListener("dragstart",e=>e.preventDefault());
    el.addEventListener("pointerdown",e=>{if(busy||e.button!==0)return;e.preventDefault();start=pos(e);active=true;el.setPointerCapture(e.pointerId);status.textContent="Movimente o ponteiro e solte no destino.";});
    el.addEventListener("pointercancel",()=>{start=null;active=false;status.textContent="Movimento cancelado.";});
    el.addEventListener("pointerup",async e=>{if(!active||!start||busy)return;e.preventDefault();active=false;const end=pos(e),origin=start;start=null;busy=true;status.textContent="Enviando movimento ao navegador remoto...";const moved=Math.hypot(end.x-origin.x,end.y-origin.y)>8;const path=moved?"/owner/tiktok/drag":"/owner/tiktok/click";const form=new FormData();if(moved){form.set("x1",String(origin.x));form.set("y1",String(origin.y));form.set("x2",String(end.x));form.set("y2",String(end.y));}else{form.set("x",String(end.x));form.set("y",String(end.y));}try{const response=await fetch(path,{method:"POST",body:form,credentials:"same-origin"});if(!response.ok)throw Error("HTTP "+response.status);const page=await response.text();document.open();document.write(page);document.close();}catch(err){status.textContent="Falha ao enviar: "+err.message+"; tente atualizar a imagem.";busy=false;}});
  })();
  </script>`:"";
  const proof=verify?`<pre>${esc(JSON.stringify(verify,null,2))}</pre>`:"";
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Browser · TikTok</title><style>body{font-family:system-ui;max-width:1500px;margin:24px auto;padding:0 18px}form{margin:8px 0}button,input{font:inherit;padding:6px}pre{white-space:pre-wrap;background:#f4f4f4;padding:12px}input[type=image]{padding:0;border:1px solid #bbb;max-width:none}#remote-shot{display:block;max-width:100%;height:auto;touch-action:none;user-select:none;cursor:crosshair;border:1px solid #aaa}.remote-wrap{max-width:1365px}#gesture-status{margin:8px 0;color:#333}</style></head><body><h1>Anthares Browser · TikTok</h1><p>Executor: <b>Northflank Chromium</b>. Cloudflare Browser Run: <b>não utilizado</b>.</p>${message?`<p><strong>${esc(message)}</strong></p>`:""}<p>${screen?.url?`URL: ${esc(screen.url)}`:""}</p>${img}<form method="post" action="/owner/tiktok/screen"><button>Atualizar imagem</button></form><form method="post" action="/owner/tiktok/type"><input name="text" type="text" autocomplete="off" placeholder="Texto / usuário / código" size="46" required> <button>Digitar</button></form><form method="post" action="/owner/tiktok/type"><input name="text" type="password" autocomplete="off" placeholder="Senha" size="46" required> <button>Digitar senha</button></form><form method="post" action="/owner/tiktok/key"><button name="key" value="Enter">Enter</button> <button name="key" value="Tab">Tab</button> <button name="key" value="Escape">Esc</button> <button name="key" value="Backspace">Backspace</button></form><form method="post" action="/owner/tiktok/navigate"><button name="url" value="https://www.tiktok.com/login">Login</button> <button name="url" value="https://www.tiktok.com/@universo.anthares">Perfil @universo.anthares</button> <button name="url" value="https://www.tiktok.com/tiktokstudio">TikTok Studio</button></form><form method="post" action="/owner/tiktok/verify"><button>Verificar conta e Studio</button></form><form method="post" action="/owner/tiktok/save"><button>Salvar autenticação e encerrar</button></form>${proof}${gestureScript}<p><a href="/owner">Voltar</a></p></body></html>`;
}

async function verifySession(env){
  const started=await ensureStarted(env);if(!started.ok||started.starting)return {ok:false,starting:!!started.starting,error:started.starting?"browser_starting":started.error||"start_failed"};
  await nf(env,"/interactive-browser/navigate",{method:"POST",body:{url:"https://www.tiktok.com/@universo.anthares"}});await new Promise(r=>setTimeout(r,1800));
  const p=await nf(env,"/interactive-browser/tiktok-evidence");const profile=p.evidence||{};const identity=!!(!profile.login_gate&&profile.account_marker&&String(profile.host||"").endsWith("tiktok.com"));
  let studio={};let studioOk=false;
  if(identity){await nf(env,"/interactive-browser/navigate",{method:"POST",body:{url:"https://www.tiktok.com/tiktokstudio"}});await new Promise(r=>setTimeout(r,1800));const s=await nf(env,"/interactive-browser/tiktok-evidence");studio=s.evidence||{};studioOk=!!(!studio.login_gate&&String(studio.host||"").endsWith("tiktok.com"));}
  const exported=await nf(env,"/interactive-browser/export",{method:"POST",body:{}});
  let stored=false;if(exported.ok&&exported.state){try{const state=normalizeState(exported.state);const wr=await writePlainState(env,state);stored=!!wr.stored;}catch{}}
  return {ok:true,persisted_state:stored||!!(await readPlainState(env)),identity_verified:identity,studio_verified:studioOk,session_state:studioOk?"authenticated":identity?"profile_only":profile.login_gate?"unauthenticated":"identity_unproven",backend:"northflank_chromium_cdp",evidence:profile,studio};
}

export default {
  async fetch(request,env,ctx){
    const url=new URL(request.url);
    const ownerPath=url.pathname.startsWith("/owner/tiktok");
    if(ownerPath&&!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});

    if(url.pathname==="/owner/tiktok"&&request.method==="GET"){
      const status=await nf(env,"/interactive-browser/status");const screen=status.active?await shot(env):null;return html(browserPage(status.active?"Sessão Northflank ativa.":"Sessão pronta para iniciar.",screen));
    }
    if(url.pathname==="/owner/tiktok/start"&&request.method==="POST"){
      const r=await ensureStarted(env);return html(browserPage(r.starting?"Chromium iniciando no Northflank. Atualize a imagem para acompanhar.":r.ok?"Chromium iniciado no Northflank.":`Falha: ${r.error||"desconhecida"}`,r.active?await shot(env):null),r.ok?200:503);
    }
    if((url.pathname==="/owner/tiktok/live"||url.pathname==="/owner/tiktok/screen")&&request.method==="POST"){
      const r=await ensureStarted(env);const screen=r.ok?await shot(env):null;return html(browserPage(screen?"Imagem atualizada.":`Falha: ${r.error||"screenshot"}`,screen),screen?200:503);
    }
    if(url.pathname==="/owner/tiktok/click"&&request.method==="POST"){
      const f=await request.formData();const x=Number(f.get("x")??f.get("shot.x"));const y=Number(f.get("y")??f.get("shot.y"));const r=await nf(env,"/interactive-browser/click",{method:"POST",body:{x,y}});await new Promise(q=>setTimeout(q,450));return html(browserPage(r.ok?`Clique enviado (${Math.round(x)}, ${Math.round(y)}).`:`Falha: ${r.error}`,await shot(env)),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/drag"&&request.method==="POST"){
      const f=await request.formData();
      const x1=Number(f.get("x1")),y1=Number(f.get("y1")),x2=Number(f.get("x2")),y2=Number(f.get("y2"));
      if(![x1,y1,x2,y2].every(Number.isFinite)||x1<0||x1>1365||x2<0||x2>1365||y1<0||y1>768||y2<0||y2>768)return html(browserPage("Coordenadas inválidas.",await shot(env)),400);
      const r=await nf(env,"/interactive-browser/drag",{method:"POST",body:{x1,y1,x2,y2}});
      await new Promise(q=>setTimeout(q,650));
      return html(browserPage(r.ok?"Arraste remoto transmitido.":`Falha no arraste: ${r.error||"desconhecida"}`,await shot(env)),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/drag-mode"&&request.method==="POST"){
      const screen=await shot(env);
      return html(browserPage("Selecione o ponto inicial com um clique na imagem.",screen,null,{phase:"start"}),screen?200:503);
    }
    if(url.pathname==="/owner/tiktok/drag-start"&&request.method==="POST"){
      const f=await request.formData();const x1=Number(f.get("shot.x"));const y1=Number(f.get("shot.y"));
      if(!Number.isFinite(x1)||!Number.isFinite(y1)||x1<0||x1>1365||y1<0||y1>768)return html(browserPage("Ponto inicial inválido."),400);
      const screen=await shot(env);
      return html(browserPage("Ponto inicial escolhido. Clique no ponto final do arrasto.",screen,null,{phase:"end",x1,y1}),screen?200:503);
    }
    if(url.pathname==="/owner/tiktok/drag-end"&&request.method==="POST"){
      const f=await request.formData();
      const x1=Number(f.get("x1")),y1=Number(f.get("y1")),x2=Number(f.get("shot.x")),y2=Number(f.get("shot.y"));
      const valid=[x1,y1,x2,y2].every(Number.isFinite)&&x1>=0&&x1<=1365&&x2>=0&&x2<=1365&&y1>=0&&y1<=768&&y2>=0&&y2<=768;
      if(!valid)return html(browserPage("Pontos do arrasto inválidos."),400);
      const r=await nf(env,"/interactive-browser/drag",{method:"POST",body:{x1,y1,x2,y2}});
      await new Promise(q=>setTimeout(q,600));
      const screen=await shot(env);
      return html(browserPage(r.ok?"Arrasto enviado. Atualize a imagem para conferir o resultado.":`Falha no arrasto: ${r.error||"desconhecida"}`,screen),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/type"&&request.method==="POST"){
      const f=await request.formData();const text=String(f.get("text")||"");const r=await nf(env,"/interactive-browser/type",{method:"POST",body:{text}});return html(browserPage(r.ok?"Texto enviado.":`Falha: ${r.error}`,await shot(env)),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/key"&&request.method==="POST"){
      const f=await request.formData();const key=String(f.get("key")||"");const r=await nf(env,"/interactive-browser/key",{method:"POST",body:{key}});await new Promise(q=>setTimeout(q,350));return html(browserPage(r.ok?`Tecla ${key} enviada.`:`Falha: ${r.error}`,await shot(env)),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/navigate"&&request.method==="POST"){
      const f=await request.formData();const target=String(f.get("url")||"");const r=await nf(env,"/interactive-browser/navigate",{method:"POST",body:{url:target}});await new Promise(q=>setTimeout(q,900));return html(browserPage(r.ok?"Página aberta.":`Falha: ${r.error}`,await shot(env)),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/verify"&&request.method==="POST"){
      const r=await verifySession(env);return html(browserPage(r.identity_verified&&r.studio_verified?"Sessão TikTok autenticada e verificada.":"Sessão ainda não verificada.",await shot(env),r),r.ok?200:503);
    }
    if(url.pathname==="/owner/tiktok/save"&&request.method==="POST"){
      const e=await nf(env,"/interactive-browser/export",{method:"POST",body:{}});let ok=false;let count=0;let err=e.error||"export_failed";
      if(e.ok&&e.state){try{const state=normalizeState(e.state);count=state.cookies.length;const wr=await writePlainState(env,state);ok=!!wr.stored;err=ok?"":(wr.error||"state_store_failed");}catch(x){err=String(x?.message||x);}}
      await nf(env,"/interactive-browser/close",{method:"POST",body:{}});
      return html(browserPage(ok?`Autenticação criptografada salva (${count} cookies) e Chromium encerrado.`:`Falha ao salvar: ${err}`,null),ok?200:503);
    }

    if(url.pathname==="/tiktok/northflank/status"&&request.method==="GET"){
      if(!machineAuthorized(request,env))return json({error:"unauthorized"},401);
      return json(await nf(env,"/interactive-browser/status"));
    }
    return baseApp.fetch(request,env,ctx);
  }
};
