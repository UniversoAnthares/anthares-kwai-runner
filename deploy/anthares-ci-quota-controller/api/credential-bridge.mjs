import {neon} from "@neondatabase/serverless";
import {createRemoteJWKSet,jwtVerify} from "jose";
import {createPublicKey,verify} from "node:crypto";

const ROOT="UniversoAnthares/anthares-kwai-runner";
const REF=ROOT+"/.github/workflows/ci-quota-external-cancel.yml@refs/heads/main";
const JWKS=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const PUBLIC_ENV="ANTHARES_REMOTE_QUOTA_PUBJWK";
function respond(res,status,code,data={}){
  res.setHeader("Cache-Control","no-store");
  return res.status(status).json({ok:status<300,code,...data});
}
function pubkey(){
  const k=JSON.parse(process.env[PUBLIC_ENV]||"null");
  if(!k||k.kty!=="RSA"||k.alg!=="RS256"||!k.n||!k.e)
    throw new Error("NO_PUBLIC_KEY");
  const safe={kty:"RSA",n:k.n,e:k.e};
  return safe;
}
function canon(body,epoch){
  return [epoch,...["phase","provider","target","sha","code","owner_token","outcome"]
    .map(k=>String(body?.[k]||""))].join("\n");
}
async function githubAuthorized(req){
  const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
  if(!bearer)return false;
  try{
    const {payload}=await jwtVerify(bearer[1],JWKS,{
      issuer:"https://token.actions.githubusercontent.com",
      audience:"anthares-ci-quota-controller",algorithms:["RS256"]});
    if(payload.repository!==ROOT||payload.workflow_ref!==REF||
       payload.ref!=="refs/heads/main"||
       !["push","workflow_dispatch"].includes(payload.event_name))
      return false;
    return String(payload.run_id);
  }catch{return false;}
}
function remoteAuthorized(req,body){
  const host=String(req.headers["x-anthares-device"]||"");
  const epoch=String(req.headers["x-anthares-timestamp"]||"");
  const signature=String(req.headers["x-anthares-signature"]||"");
  if(host!=="DESKTOP-FTDK0HP"||!/^[0-9]{10}$/.test(epoch)||
    Math.abs(Date.now()/1000-Number(epoch))>120||
    !/^[a-zA-Z0-9+/]{500,520}={0,2}$/.test(signature))return false;
  try{
    return verify("RSA-SHA256",Buffer.from(canon(body,epoch)),
      createPublicKey({key:pubkey(),format:"jwk"}),Buffer.from(signature,"base64"));
  }catch{return false;}
}
export default async function handler(req,res){
  if(process.env.CI_QUOTA_MODE!=="ENABLED")return respond(res,503,"DISABLED");
  if(req.method==="GET"){
    try{return respond(res,200,"RSA_PUBLIC_KEY",{jwk:pubkey()});}
    catch{return respond(res,503,"PUBLIC_KEY_UNAVAILABLE");}
  }
  if(req.method!=="POST")return respond(res,405,"METHOD_NOT_ALLOWED");
  let body;try{body=typeof req.body==="string"?JSON.parse(req.body):req.body;}
  catch{return respond(res,400,"INVALID_JSON");}
  if(!body||typeof body!=="object"||body.provider!=="appveyor")
    return respond(res,400,"INVALID_PROVIDER");
  const db=neon(process.env.DATABASE_URL);
  if(body.phase==="stage"){
    const run=await githubAuthorized(req);
    if(!run)return respond(res,403,"WORKFLOW_NOT_AUTHORIZED");
    const sealed=String(body.sealed||"");
    if(!/^[A-Za-z0-9+/]+={0,2}$/.test(sealed)||
       Buffer.from(sealed,"base64").length!==384)
       return respond(res,400,"INVALID_SEALED_CREDENTIAL");
    try{
      await db`INSERT INTO public.anthares_ci_quota_sealed_credentials
       (provider,sealed_ciphertext,source_run,expires_at)
       VALUES ('appveyor',${sealed},${run},now()+interval '90 minutes')
       ON CONFLICT(provider) DO UPDATE SET
       sealed_ciphertext=EXCLUDED.sealed_ciphertext,
       source_run=EXCLUDED.source_run,
       expires_at=EXCLUDED.expires_at`;
      return respond(res,202,"SEALED_READY",{provider:"appveyor",expires_in_seconds:5400});
    }catch{return respond(res,503,"SEALED_LEDGER_UNAVAILABLE");}
  }
  if(body.phase==="consume"){
    if(!remoteAuthorized(req,body))return respond(res,403,"REMOTE_IDENTITY_INVALID");
    try{
      const rows=await db`DELETE FROM public.anthares_ci_quota_sealed_credentials
       WHERE provider='appveyor' AND expires_at>now()
       RETURNING sealed_ciphertext`;
      if(rows.length!==1)return respond(res,404,"NO_SEALED_CREDENTIAL");
      return respond(res,200,"SEALED_CONSUMED",{sealed:rows[0].sealed_ciphertext});
    }catch{return respond(res,503,"SEALED_CONSUME_UNAVAILABLE");}
  }
  return respond(res,400,"INVALID_PHASE");
}
