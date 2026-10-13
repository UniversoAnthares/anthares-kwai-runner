const X_KEY = "x:web:session:lucasyahn:opaque:v1";
const BROWSER_KEY = "anthares:browser:legacy:opaque:v1";
const BROWSER_RUNTIME_KEY = "anthares:browser:runtime:opaque:v2";
const BROWSER_CONTROL_KEY = "anthares:browser:control:opaque:v1";
const BROWSER_CONTROL_JWK_KEY = "anthares:browser:signing:control-jwk:v1";
const BROWSER_RUNTIME_JWK_KEY = "anthares:browser:signing:runtime-jwk:v1";
const MAX_BODY = 500000;
const PUBLIC_JWK = {"kty":"EC","crv":"P-256","x":"oljQWjUajvbTS5Lyc0ElhK2nN_h6kJo-bhJ6F5mnf_4","y":"lBVZd8W28jEMd2A0oDs_PrGAkaDUbuzqb9WoerAVrmQ","ext":true};
let browserControlJwk=null,browserRuntimeJwk=null;

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
function adminAuthorized(request,env){
  const token=String(env.BROWSER_KEY_ADMIN_TOKEN||"");
  return !!token&&request.headers.get("Authorization")==="Bearer "+token;
}
async function storedBrowserKeys(env){
  if(!validBrowserJwk(browserControlJwk)){
    const stored=await env.ANTHARES_STATE.get(BROWSER_CONTROL_JWK_KEY,"json");
    if(validBrowserJwk(stored))browserControlJwk=stored;
  }
  if(!validBrowserJwk(browserRuntimeJwk)){
    const stored=await env.ANTHARES_STATE.get(BROWSER_RUNTIME_JWK_KEY,"json");
    if(validBrowserJwk(stored))browserRuntimeJwk=stored;
  }
  return [browserRuntimeJwk,browserControlJwk].filter(validBrowserJwk);
}
async function browserKeyStatus(env){
  await storedBrowserKeys(env);
  return {runtime:validBrowserJwk(browserRuntimeJwk),control:validBrowserJwk(browserControlJwk)};
}
async function registerBrowserKey(request,env){
  if(!adminAuthorized(request,env))return json({ok:false,error:"unauthorized"},401);
  let data;try{data=await request.json()}catch{return json({ok:false,error:"invalid_json"},400)}
  const authority=String(data?.authority||"");
  const jwk=data?.jwk;
  if(!["runtime","control"].includes(authority)||!validBrowserJwk(jwk))return json({ok:false,error:"invalid_browser_key_registration"},422);
  const key=authority==="runtime"?BROWSER_RUNTIME_JWK_KEY:BROWSER_CONTROL_JWK_KEY;
  await env.ANTHARES_STATE.put(key,JSON.stringify(jwk));
  if(authority==="runtime")browserRuntimeJwk=jwk;else browserControlJwk=jwk;
  return json({ok:true,registered:true,authority,render_dependency:false});
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
    for(const jwk of await storedBrowserKeys(env))if(await verifyBrowserSignature(jwk,message,sig))return true;
    return false;
  }catch{return false;}
}
function validEnvelope(x){return !!x&&x.schema==="anthares.encrypted-browser-state.v1"&&typeof x.ciphertext==="string"&&x.ciphertext.length>=64&&x.ciphertext.length<=MAX_BODY-1000&&/^[A-Za-z0-9+/_=-]+$/.test(x.ciphertext)&&typeof x.sha256==="string"&&/^[0-9a-f]{64}$/.test(x.sha256);}
function browserStateKey(pathname){
  if(pathname==="/browser-state/runtime")return BROWSER_RUNTIME_KEY;
  if(pathname==="/browser-state/control")return BROWSER_CONTROL_KEY;
  if(pathname==="/browser-state")return BROWSER_KEY;
  return null;
}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname==="/health"){
      const keys=env.ANTHARES_STATE?await browserKeyStatus(env):{runtime:false,control:false};
      return json({ok:true,service:"anthares-x-vault",version:"x-vault-v9-render-independent-keys",persistent_state:!!env.ANTHARES_STATE,browser_state_slot:true,browser_state_slots:["legacy","runtime","control"],browser_identity:"registered-public-keys",render_independent:true,browser_keys:keys});
    }
    if(url.pathname==="/browser-key/status"){
      if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
      return json({ok:true,...await browserKeyStatus(env),render_dependency:false});
    }
    if(url.pathname==="/browser-key/register"){
      if(request.method!=="POST")return json({ok:false,error:"method_not_allowed"},405);
      if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
      return registerBrowserKey(request,env);
    }
    if(url.pathname==="/browser-key/refresh")return json({ok:false,error:"endpoint_retired",render_dependency:false},410);
    const browserKey=browserStateKey(url.pathname);
    const isBrowser=!!browserKey;
    const key=url.pathname==="/state"?X_KEY:browserKey;
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
