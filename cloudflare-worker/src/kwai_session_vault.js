// Private, durable storage for an already encrypted Kwai Android app archive.
// The archive must be encrypted client-side; never accept plaintext cookies,
// raw UI XML, screenshots, passwords or Android app data.
const KEY="kwai:mobile:session:lucasrosalem:v1";
const ACCOUNT="lucasrosalem";
const MAX_BASE64=6_000_000;
const HEADER="U2FsdGVkX1"; // base64(OpenSSL 'Salted__' archive)
function json(data,status=200){
  return new Response(JSON.stringify(data),{status,headers:{
    "content-type":"application/json;charset=utf-8",
    "cache-control":"no-store",
    "x-content-type-options":"nosniff"
  }});
}
function isCiphertext(s){
  return typeof s==="string"&&s.length>=64&&s.length<=MAX_BASE64&&
    s.startsWith(HEADER)&&/^[A-Za-z0-9+/]+={0,2}$/.test(s);
}
async function digest(s){
  const bytes=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));
  return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,"0")).join("");
}
export async function handleKwaiSessionVault(request,env,verifyGithubOidc){
  const authHeader=request.headers.get("Authorization")||"";
  const token=authHeader.replace(/^Bearer\s+/i,"");
  const auth=await verifyGithubOidc(token,env,["kwai-queue-publisher.yml"]);
  const claims=auth.claims||{};
  const workflow=String(claims.job_workflow_ref||claims.workflow_ref||"");
  if(!auth.ok||claims.repository!=="UniversoAnthares/anthares-kwai-runner"||
      !workflow.includes("UniversoAnthares/anthares-kwai-runner/.github/workflows/kwai-queue-publisher.yml@refs/heads/main")){
    return json({ok:false,error:"unauthorized"},401);
  }
  if(!env.ANTHARES_STATE)return json({ok:false,error:"persistent_state_unavailable"},503);
  const method=request.method;
  if(method==="GET"){
    const row=await env.ANTHARES_STATE.get(KEY,"json");
    if(new URL(request.url).searchParams.get("probe")==="1"){
      return json({ok:true,persistent:true,available:!!row,schema:"anthares.kwai.vault.v1"});
    }
    if(!row)return json({ok:false,error:"session_absent"},404);
    if(row.schema!=="anthares.kwai.vault.v1"||row.account!==ACCOUNT||!isCiphertext(row.ciphertext)||
        row.sha256!==await digest(row.ciphertext))return json({ok:false,error:"vault_integrity_failed"},409);
    return json({ok:true,schema:row.schema,account:ACCOUNT,ciphertext:row.ciphertext,
                 sha256:row.sha256,updated_at:row.updated_at});
  }
  if(method==="POST"){
    const body=await request.text();
    if(body.length>MAX_BASE64+1000)return json({ok:false,error:"payload_too_large"},413);
    let data;try{data=JSON.parse(body)}catch{return json({ok:false,error:"invalid_json"},400)}
    if(!data||data.account!==ACCOUNT||!isCiphertext(data.ciphertext))
      return json({ok:false,error:"encrypted_archive_required"},422);
    const sha256=await digest(data.ciphertext);
    if(data.sha256!==sha256)return json({ok:false,error:"digest_mismatch"},422);
    const row={schema:"anthares.kwai.vault.v1",account:ACCOUNT,
               ciphertext:data.ciphertext,sha256,updated_at:new Date().toISOString()};
    await env.ANTHARES_STATE.put(KEY,JSON.stringify(row));
    return json({ok:true,stored:true,sha256,updated_at:row.updated_at});
  }
  return json({ok:false,error:"method_not_allowed"},405);
}
