import {neon} from "@neondatabase/serverless";
import {createRemoteJWKSet,jwtVerify} from "jose";
import {randomUUID,createPublicKey,verify} from "node:crypto";

const ROOT="UniversoAnthares/anthares-kwai-runner";
const WF=ROOT+"/.github/workflows/ci-quota-external-cancel.yml@refs/heads/main";
const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const codes=new Set(["ci_quota_exceeded","quota_exceeded","quota_exhausted",
"insufficient_quota","resource_exhausted","billing_hard_limit_reached",
"credits_exhausted","usage_limit_reached","monthly_quota_exceeded","daily_quota_exceeded"]);
const plain=/^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$/;
function respond(res,status,code,data={}){res.setHeader("Cache-Control","no-store");
return res.status(status).json({ok:status<300,code,...data});}
export default async function handler(req,res){
 if(req.method!=="POST")return respond(res,405,"METHOD_NOT_ALLOWED");
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return respond(res,503,"DISABLED");
 let body;try{body=typeof req.body==="string"?JSON.parse(req.body):req.body;}
 catch{return respond(res,400,"INVALID_JSON");}
 if(!body||typeof body!=="object")return respond(res,400,"INVALID_BODY");
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 let owner;
 if(bearer){
   let claims;
   try{({payload:claims}=await jwtVerify(bearer[1],jwks,{
     issuer:"https://token.actions.githubusercontent.com",
     audience:"anthares-ci-quota-controller",algorithms:["RS256"]}));}
   catch{return respond(res,401,"OIDC_INVALID");}
   if(claims.repository!==ROOT||claims.workflow_ref!==WF||
      claims.ref!=="refs/heads/main"||
      !["schedule","workflow_dispatch","push"].includes(claims.event_name))
      return respond(res,403,"WORKFLOW_IDENTITY_INVALID");
   owner=String(claims.run_id);
 }else{
   const id=String(req.headers["x-anthares-device"]||"");
   const t=String(req.headers["x-anthares-timestamp"]||"");
   const signature=String(req.headers["x-anthares-signature"]||"");
   if(id!=="DESKTOP-FTDK0HP"||!/^[0-9]{10}$/.test(t)||
      Math.abs(Date.now()/1000-Number(t))>120||!/^[A-Za-z0-9+/]{300,600}={0,2}$/.test(signature))
      return respond(res,401,"REMOTE_AUTH_REQUIRED");
   const publicJwk=process.env.ANTHARES_REMOTE_QUOTA_PUBJWK;
   if(!publicJwk)return respond(res,503,"REMOTE_AUTH_DISABLED");
   const fields=["phase","provider","target","sha","code","owner_token","outcome"];
   const message=[t,...fields.map(k=>String(body[k]||""))].join("\n");
   let valid=false;
   try{
     const jwk=JSON.parse(publicJwk);
     if(jwk.kty!=="RSA"||jwk.alg!=="RS256"||!jwk.n||!jwk.e)
       return respond(res,503,"REMOTE_KEY_INVALID");
     valid=verify("RSA-SHA256",Buffer.from(message,"utf8"),
       createPublicKey({key:jwk,format:"jwk"}),Buffer.from(signature,"base64"));
   }catch{return respond(res,401,"REMOTE_AUTH_INVALID");}
   if(!valid)return respond(res,401,"REMOTE_AUTH_INVALID");
   owner="remote:"+id;
 }
 if(body.phase==="health"&&owner==="remote:DESKTOP-FTDK0HP"){
   try{
     const probe=await neon(process.env.DATABASE_URL)`SELECT current_user AS who, to_regclass('public.anthares_ci_quota_attempts')::text AS ledger`;
     if(probe[0]?.who!=="anthares_ci_quota_limited"||!probe[0]?.ledger)
       return respond(res,503,"LEDGER_PRINCIPAL_MISMATCH");
     return respond(res,200,"REMOTE_AUTH_READY",{ledger:"READY"});
   }catch{return respond(res,503,"LEDGER_UNAVAILABLE");}
 }
 const provider=String(body?.provider||""),
 target=String(body?.target||""),code=String(body?.code||""),
 source_sha=String(body?.sha||""),phase=String(body?.phase||"");
 if(!["appveyor","bitrise","harness"].includes(provider)||!plain.test(target)||
 !codes.has(code)||!/^[a-f0-9]{40}$/.test(source_sha))
 return respond(res,400,"INVALID_EVENT");
 // Harness claims are *only* ledger reservations: this endpoint never
 // performs provider cancellation or enqueues a successor. Authorization and
 // quota/source-commit validation remain the signed watcher's responsibility.
 if(provider==="harness"&&!/^[A-Za-z0-9_-]{16,64}$/.test(target))
   return respond(res,400,"INVALID_HARNESS_EXECUTION");
 const attempt=provider+":"+target;
 const sql=neon(process.env.DATABASE_URL);
 if(phase==="claim"){
   const token=randomUUID();
   try{
    const data={provider,target,source_sha,quota_code:code,
      state:"CANCEL_REQUESTED",owner_run:owner,
      fallback_dispatched:false,side_effects_reconciled:false};
    const rows=await sql`INSERT INTO public.anthares_ci_quota_attempts
      (attempt_id,owner_token,state,data,lease_until)
      VALUES (${attempt},${token}::uuid,'CANCEL_REQUESTED',
        ${JSON.stringify(data)}::jsonb,now()+interval '180 seconds')
      ON CONFLICT DO NOTHING RETURNING attempt_id`;
    if(rows.length!==1)return respond(res,409,"ALREADY_CLAIMED");
    return respond(res,200,"CLAIMED",{attempt,owner_token:token});
   }catch{return respond(res,503,"LEDGER_UNAVAILABLE");}
 }
 if(phase!=="report")return respond(res,400,"INVALID_PHASE");
 const owner_token=String(body.owner_token||"");
 const outcome=String(body.outcome||"");
 if(!/^[a-f0-9-]{36}$/.test(owner_token)||
 !["CANCELLED_NO_INDEPENDENT_RESERVE","CANCEL_UNCONFIRMED"].includes(outcome))
 return respond(res,400,"INVALID_REPORT");
 try{
   const extra={state:outcome,provider_terminal_reported:outcome==="CANCELLED_NO_INDEPENDENT_RESERVE",
       verified_by:"authenticated_watcher",fallback_dispatched:false};
   const rows=await sql`UPDATE public.anthares_ci_quota_attempts
   SET state=${outcome},data=data || ${JSON.stringify(extra)}::jsonb,
       updated_at=now(),lease_generation=lease_generation+1
   WHERE attempt_id=${attempt} AND owner_token=${owner_token}::uuid
     AND lease_generation=1 AND state='CANCEL_REQUESTED'
     AND data->>'owner_run'=${owner}
     AND data->>'source_sha'=${source_sha}
   RETURNING attempt_id`;
   if(rows.length!==1)return respond(res,409,"FENCING_REJECTED");
   return respond(res,200,"RECORDED",{attempt,state:outcome});
 }catch{return respond(res,503,"REPORT_UNCERTAIN");}
}
