import app, { BrowserState } from "./northflank-owner-entry.js";

export { BrowserState };

const OWNER_COOKIE = "anthares_reserva_owner";
const OWNER_SESSION_SECONDS = 2592000;
const te = new TextEncoder();

const b64url = bytes => {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
};
function sameSecret(a,b){a=String(a||"");b=String(b||"");if(!a||a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
async function ownerCodeMatches(value,configured){
  // Accept the two interoperable SHA-256 encodings used by dashboards and
  // PowerShell: base64url (canonical) or hexadecimal. Never accept a raw code.
  const raw=String(configured||"").trim();
  const digest=new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode(String(value))));
  if(/^[a-f0-9]{64}$/i.test(raw)){
    const hex=Array.from(digest,b=>b.toString(16).padStart(2,"0")).join("");
    return sameSecret(hex,raw.toLowerCase());
  }
  const standard=raw.replaceAll("+","-").replaceAll("/","_").replace(/=+$/,"");
  return /^[A-Za-z0-9_-]{43}$/.test(standard)&&sameSecret(b64url(digest),standard);
}
const ownerLoginPage=message=>`<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Reserva | Proprietário</title></head><body style="font:16px system-ui;max-width:640px;margin:40px auto;padding:0 18px"><h1>Anthares Reserva</h1>${message?`<p role="alert">${message}</p>`:""}<form method="post" action="/owner/login"><label>Código do proprietário <input name="code" type="password" autocomplete="one-time-code" required maxlength="256"></label> <button type="submit">Entrar</button></form><p>Digite o código original utilizado para gerar o hash na Cloudflare. O hash não é um código de login.</p></body></html>`;

async function hmac(env,value){if(!env.ANTHARES_RESERVA_TOKEN)throw new Error("reserve token unavailable");const key=await crypto.subtle.importKey("raw",te.encode(env.ANTHARES_RESERVA_TOKEN),{name:"HMAC",hash:"SHA-256"},false,["sign"]);return b64url(new Uint8Array(await crypto.subtle.sign("HMAC",key,te.encode(value))));}
async function issueOwnerSession(env){const payload=b64url(te.encode(JSON.stringify({exp:Math.floor(Date.now()/1000)+OWNER_SESSION_SECONDS,nonce:crypto.randomUUID()})));return `${payload}.${await hmac(env,payload)}`;}
const ownerCookie=token=>`${OWNER_COOKIE}=${token}; Path=/; Max-Age=${OWNER_SESSION_SECONDS}; HttpOnly; Secure; SameSite=Strict`;

export default {
  async fetch(request,env,ctx){
    const url=new URL(request.url);
    if(url.pathname==="/owner/login"&&request.method==="POST"){
      if(!env.OWNER_APPROVAL_HASH)return new Response("Owner secret unavailable",{status:503,headers:{"cache-control":"no-store"}});
      const form=await request.formData();
      const code=String(form.get("code")||"");
      if(code.length>256||!(await ownerCodeMatches(code,env.OWNER_APPROVAL_HASH)))return new Response(ownerLoginPage("Código inválido. Confira o código original e tente novamente."),{status:403,headers:{"content-type":"text/html; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff","content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"}});
      const token=await issueOwnerSession(env);
      return new Response(null,{status:303,headers:{location:"/owner","set-cookie":ownerCookie(token),"cache-control":"no-store"}});
    }
    return app.fetch(request,env,ctx);
  }
};
