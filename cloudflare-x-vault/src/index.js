const KEY = "x:web:session:lucasyahn:opaque:v1";
const MAX_BODY = 500000;
const PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvMGOSYs+YvDkqjPCCc3Q
VvUCRyMXjZiHReuZ2dFtnzBv/4RXiZIk4zFy95ovyeKr02OpWs46QlLUcgRF8nNN
Lk2ek6S2aAmwm4FHxbsJuwzgwPvVkGI2irbyOsXgBFL+GwgfgBxgeJjYX/tCqP7v
5iHte0En2u5Kshx/WkJicYtAUiC9j7E8Km6mS/gDT91VXvsUDOnbb1wVIw16EyCe
/RsdJKXpyGjVRJUY42MaFYbYEhhG68Yz8mWBDdMJBzEzM2Bf0yif0V9mdxzrNcxp
jgEnrbQ3Xl3JxMJ76OLyT6IW7xyIfWuC7yFLORxrb4yohEU//hQfaO76nfRP6tD4
OQIDAQAB
-----END PUBLIC KEY-----`;

function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json;charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}})}
function b64bytes(s){const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0));}
async function sha256hex(s){const d=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,"0")).join("");}
async function importKey(){const b64=PUBLIC_KEY.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\s+/g,"");return crypto.subtle.importKey("spki",b64bytes(b64),{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);}
async function authorized(request,body){
  const ts=Number(request.headers.get("X-Anthares-Timestamp")||0);
  const sig=String(request.headers.get("X-Anthares-Signature")||"");
  if(!ts||Math.abs(Date.now()-ts)>300000||!sig)return false;
  try{const hex=await sha256hex(body);return await crypto.subtle.verify("RSASSA-PKCS1-v1_5",await importKey(),b64bytes(sig),new TextEncoder().encode(String(ts)+"."+hex));}catch{return false;}
}
function validEnvelope(x){return !!x&&x.schema==="anthares.encrypted-browser-state.v1"&&typeof x.ciphertext==="string"&&x.ciphertext.length>=64&&x.ciphertext.length<=MAX_BODY-1000&&/^[A-Za-z0-9+/=]+$/.test(x.ciphertext)&&typeof x.sha256==="string"&&/^[0-9a-f]{64}$/.test(x.sha256);}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname==="/health")return json({ok:true,service:"anthares-x-vault",version:"x-vault-v1",persistent_state:!!env.ANTHARES_STATE});
    if(url.pathname!=="/state")return json({ok:false,error:"not_found"},404);
    if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
    const body=request.method==="POST"?await request.text():"";
    if(body.length>MAX_BODY)return json({ok:false,error:"payload_too_large"},413);
    if(!(await authorized(request,body)))return json({ok:false,error:"unauthorized"},401);
    if(request.method==="GET"){
      const row=await env.ANTHARES_STATE.get(KEY,"json");
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
      await env.ANTHARES_STATE.put(KEY,JSON.stringify(row));
      return json({ok:true,stored:true,sha256:sha,updated_at:row.updated_at});
    }
    return json({ok:false,error:"method_not_allowed"},405);
  }
};
