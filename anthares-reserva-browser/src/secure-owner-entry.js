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
async function sha256b64(value){return b64url(new Uint8Array(await crypto.subtle.digest("SHA-256",te.encode(String(value)))));}
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
      if(!sameSecret(await sha256b64(code),env.OWNER_APPROVAL_HASH))return new Response("Código inválido.",{status:403,headers:{"content-type":"text/plain; charset=utf-8","cache-control":"no-store"}});
      const token=await issueOwnerSession(env);
      return new Response(null,{status:303,headers:{location:"/owner","set-cookie":ownerCookie(token),"cache-control":"no-store"}});
    }
    return app.fetch(request,env,ctx);
  }
};
