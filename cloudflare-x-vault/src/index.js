const X_KEY = "x:web:session:lucasyahn:opaque:v1";
const BROWSER_KEY = "anthares:browser:runtime:opaque:v1";
const BROWSER_JWK_KEY = "anthares:browser:signing:jwk:v1";
const MAX_BODY = 500000;
const PUBLIC_JWK = {"kty":"EC","crv":"P-256","x":"oljQWjUajvbTS5Lyc0ElhK2nN_h6kJo-bhJ6F5mnf_4","y":"lBVZd8W28jEMd2A0oDs_PrGAkaDUbuzqb9WoerAVrmQ","ext":true};
const BROWSER_PUBLIC_KEY_URL = "https://anthares-remote-control.onrender.com/v1/runtime/browser/signing-public-key";
let browserJwk=null;

function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json;charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}})}
function b64bytes(s){s=s.replace(/-/g,"+").replace(/_/g,"/");while(s.length%4)s+="=";const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0));}
async function sha256hex(s){const d=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,"0")).join("");}
async function importVerifyKey(jwk){return crypto.subtle.importKey("jwk",jwk,{name:"ECDSA",namedCurve:"P-256"},false,["verify"]);}
function validBrowserJwk(jwk){return !!jwk&&jwk.kty==="EC"&&jwk.crv==="P-256"&&typeof jwk.x==="string"&&typeof jwk.y==="string";}
async function authorized(request,body){
  const ts=Number(request.headers.get("X-Anthares-Timestamp")||0);
  const sig=String(request.headers.get("X-Anthares-Signature")||"");
  if(!ts||Math.abs(Date.now()-ts)>300000||!sig)return false;
  try{const hex=await sha256hex(body);return await crypto.subtle.verify({name:"ECDSA",hash:"SHA-256"},await importVerifyKey(PUBLIC_JWK),b64bytes(sig),new TextEncoder().encode(String(ts)+"."+hex));}catch{return false;}
}
async function fetchBrowserPublicJwk(env){
  const r=await fetch(BROWSER_PUBLIC_KEY_URL,{headers:{"accept":"application/json","cache-control":"no-cache"}});
  if(!r.ok)throw new Error("browser_public_key_unavailable");
  const data=await r.json(),jwk=data&&data.jwk;
  if(!data?.ok||!validBrowserJwk(jwk))throw new Error("browser_public_key_invalid");
  await env.ANTHARES_STATE.put(BROWSER_JWK_KEY,JSON.stringify(jwk));
  browserJwk=jwk;
  return jwk;
}
async function browserPublicJwk(env){
  if(validBrowserJwk(browserJwk))return browserJwk;
  const stored=await env.ANTHARES_STATE.get(BROWSER_JWK_KEY,"json");
  if(validBrowserJwk(stored)){browserJwk=stored;return stored;}
  return fetchBrowserPublicJwk(env);
}
async function verifyBrowserSignature(jwk,message,sig){
  return crypto.subtle.verify({name:"ECDSA",hash:"SHA-256"},await importVerifyKey(jwk),b64bytes(sig),new TextEncoder().encode(message));
}
async function browserAuthorized(request,body,env){
  const ts=Number(request.headers.get("X-Anthares-Browser-Timestamp")||0);
  const sig=String(request.headers.get("X-Anthares-Browser-Signature")||"");
  if(!ts||Math.abs(Date.now()-ts)>300000||!sig)return false;
  try{
    const hex=await sha256hex(body),message=String(ts)+"."+hex;
    const cached=await browserPublicJwk(env);
    if(await verifyBrowserSignature(cached,message,sig))return true;
    const refreshed=await fetchBrowserPublicJwk(env);
    return await verifyBrowserSignature(refreshed,message,sig);
  }catch{return false;}
}
function validEnvelope(x){return !!x&&x.schema==="anthares.encrypted-browser-state.v1"&&typeof x.ciphertext==="string"&&x.ciphertext.length>=64&&x.ciphertext.length<=MAX_BODY-1000&&/^[A-Za-z0-9+/_=-]+$/.test(x.ciphertext)&&typeof x.sha256==="string"&&/^[0-9a-f]{64}$/.test(x.sha256);}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname==="/health")return json({ok:true,service:"anthares-x-vault",version:"x-vault-v6-browser-key-auto-refresh",persistent_state:!!env.ANTHARES_STATE,browser_state_slot:true,browser_identity:"remote-public-key"});
    if(url.pathname==="/browser-key/refresh"){
      if(request.method!=="POST")return json({ok:false,error:"method_not_allowed"},405);
      if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
      try{await fetchBrowserPublicJwk(env);return json({ok:true,refreshed:true});}
      catch{return json({ok:false,error:"browser_public_key_refresh_failed"},503);}
    }
    const isBrowser=url.pathname==="/browser-state";
    const key=url.pathname==="/state"?X_KEY:isBrowser?BROWSER_KEY:null;
    if(!key)return json({ok:false,error:"not_found"},404);
    if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
    const body=request.method==="POST"?await request.text():"";
    if(body.length>MAX_BODY)return json({ok:false,error:"payload_too_large"},413);
    const authOk=isBrowser?await browserAuthorized(request,body,env):await authorized(request,body);
    if(!authOk)return json({ok:false,error:"unauthorized"},401);
    if(request.method==="GET"){
      const row=await env.ANTHARES_STATE.get(key,"json");
      if(!row)return json({ok:false,available:false},404);
      if(!validEnvelope(row)||row.sha256!==await sha256hex(row.ciphertext))return json({ok:false,error:"vault_integrity_failed"},409);
      return json({ok:true,available:true,schema:row.schema,ciphertext:row.ciphertext,sha256:row.sha256,updated_at:row.updated_at});
    }
    if(request.method==="POST"){
      let data;try{data=JSON.parse(body)}catch{return json({ok:false,error:"invalid_json"},400)}
      if(!validEnvelope(data))return json({ok:false,error:"encrypted_envelope_required"},422);
      const sha=await sha256hex(data.ciphertext);
      if(sha!==data.sha256)return json({ok:false,error:"digest_mismatch"},422);
      const row={schema:data.schema,ciphertext:data.ciphertext,sha256:sha,updated_at:new Date().toISOString()};
      await env.ANTHARES_STATE.put(key,JSON.stringify(row));
      return json({ok:true,stored:true,sha256:sha,updated_at:row.updated_at});
    }
    return json({ok:false,error:"method_not_allowed"},405);
  }
};