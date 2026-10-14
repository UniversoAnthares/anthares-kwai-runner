import app, { BrowserState } from "./tiktok-entry.js";

export { BrowserState };

const OWNER_COOKIE = "anthares_reserva_owner";
const te = new TextEncoder();
const td = new TextDecoder();

const html = (body, status = 200) => new Response(body, {
  status,
  headers: {
    "content-type":"text/html; charset=utf-8",
    "cache-control":"no-store",
    "x-content-type-options":"nosniff",
    "referrer-policy":"no-referrer",
    "content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
  },
});

const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
function sameSecret(a,b){a=String(a||"");b=String(b||"");if(!a||a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
function cookieValue(request,name){for(const part of (request.headers.get("cookie")||"").split(";")){const [k,...rest]=part.trim().split("=");if(k===name)return rest.join("=");}return "";}
const fromB64url=value=>{let s=String(value||"").replace(/-/g,"+").replace(/_/g,"/");while(s.length%4)s+="=";const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0));};
const b64url=bytes=>{let s="";for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");};
async function hmac(env,value){if(!env.ANTHARES_RESERVA_TOKEN)return "";const key=await crypto.subtle.importKey("raw",te.encode(env.ANTHARES_RESERVA_TOKEN),{name:"HMAC",hash:"SHA-256"},false,["sign"]);return b64url(new Uint8Array(await crypto.subtle.sign("HMAC",key,te.encode(value))));}
async function ownerAuthorized(request,env){const token=cookieValue(request,OWNER_COOKIE);const [payload,sig,extra]=String(token).split(".");if(!payload||!sig||extra!==undefined)return false;if(!sameSecret(sig,await hmac(env,payload)))return false;try{const p=JSON.parse(td.decode(fromB64url(payload)));return Number(p.exp)>Math.floor(Date.now()/1000);}catch{return false;}}

async function machineCall(request,env,ctx,path){
  const target=new URL(path,request.url).toString();
  return app.fetch(new Request(target,{method:"POST",headers:{Authorization:"Bearer "+env.ANTHARES_RESERVA_TOKEN}}),env,ctx);
}

function page(message="",live="",verify=null){
  const proof=verify?`<pre style="white-space:pre-wrap;background:#f4f4f4;padding:12px;border-radius:8px">${esc(JSON.stringify(verify,null,2))}</pre>`:"";
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Browser · TikTok</title></head><body style="font-family:system-ui;max-width:820px;margin:40px auto;padding:0 20px"><h1>Anthares Browser · TikTok</h1><p>Conta alvo: <b>@universo.anthares</b>.</p>${message?`<p><strong>${esc(message)}</strong></p>`:""}${live?`<p><a href="${esc(live)}" target="_blank" rel="noopener noreferrer">Abrir TikTok no Anthares Browser</a></p>`:""}${proof}<form method="post" action="/owner/tiktok/start"><button type="submit">Iniciar / recuperar sessão TikTok</button></form><form method="post" action="/owner/tiktok/live"><button type="submit">Gerar novo Live View</button></form><form method="post" action="/owner/tiktok/verify"><button type="submit">Verificar @universo.anthares e Studio</button></form><form method="post" action="/owner/tiktok/save"><button type="submit">Salvar autenticação e encerrar</button></form><p><a href="/owner">Voltar</a></p></body></html>`;
}

export default {
  async fetch(request,env,ctx){
    const url=new URL(request.url);
    if(url.pathname==="/owner/tiktok"&&request.method==="GET"){
      if(!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});
      return html(page());
    }
    if(["/owner/tiktok/start","/owner/tiktok/live","/owner/tiktok/verify","/owner/tiktok/save"].includes(url.pathname)&&request.method==="POST"){
      if(!(await ownerAuthorized(request,env)))return new Response(null,{status:303,headers:{location:"/owner","cache-control":"no-store"}});
      if(url.pathname.endsWith("/start")||url.pathname.endsWith("/live")){
        const r=await machineCall(request,env,ctx,"/tiktok/session/live");const d=await r.json();return html(page(d.ok?"Sessão TikTok pronta.":`Falha: ${d.error||"desconhecida"}`,d.live_view_url||""),d.ok?200:503);
      }
      if(url.pathname.endsWith("/save")){
        const r=await machineCall(request,env,ctx,"/tiktok/session/save");const d=await r.json();return html(page(d.ok?"Estado TikTok criptografado salvo e navegador encerrado.":`Falha: ${d.error||"desconhecida"}`),d.ok?200:503);
      }
      const r=await machineCall(request,env,ctx,"/tiktok/session/verify");const d=await r.json();
      const safe={ok:d.ok,persisted_state:d.persisted_state,identity_verified:d.identity_verified,studio_verified:d.studio_verified,session_state:d.session_state,restore_status:d.restore_status,state_refreshed:d.state_refreshed,error:d.error,detail:d.detail};
      return html(page(d.identity_verified&&d.studio_verified?"Sessão TikTok recuperada e verificada.":"Sessão ainda não verificada.","",safe),r.ok?200:503);
    }
    return app.fetch(request,env,ctx);
  },
};
