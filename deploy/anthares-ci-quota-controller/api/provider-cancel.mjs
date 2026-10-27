import {neon} from "@neondatabase/serverless";
import {createRemoteJWKSet,jwtVerify} from "jose";
import {randomUUID} from "node:crypto";

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
 let claims;
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return respond(res,401,"OIDC_REQUIRED");
 try{({payload:claims}=await jwtVerify(bearer[1],jwks,{
 issuer:"https://token.actions.githubusercontent.com",
 audience:"anthares-ci-quota-controller",algorithms:["RS256"]}));}
 catch{return respond(res,401,"OIDC_INVALID");}
 if(claims.repository!==ROOT||claims.workflow_ref!==WF||claims.ref!=="refs/heads/main"||
 !["schedule","workflow_dispatch"].includes(claims.event_name))
 return respond(res,403,"WORKFLOW_IDENTITY_INVALID");
 let body;try{body=typeof req.body==="string"?JSON.parse(req.body):req.body;}
 catch{return respond(res,400,"INVALID_JSON");}
 const provider=String(body?.provider||""),
 target=String(body?.target||""),code=String(body?.code||""),
 source_sha=String(body?.sha||""),phase=String(body?.phase||"");
 if(!["appveyor","bitrise"].includes(provider)||!plain.test(target)||
 !codes.has(code)||!/^[a-f0-9]{40}$/.test(source_sha))
 return respond(res,400,"INVALID_EVENT");
 const attempt=provider+":"+target;
 const sql=neon(process.env.DATABASE_URL);
 if(phase==="claim"){
   const token=randomUUID();
   try{
    const data={provider,target,source_sha,quota_code:code,
      state:"CANCEL_REQUESTED",owner_run:String(claims.run_id),
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
     AND data->>'owner_run'=${String(claims.run_id)}
     AND data->>'source_sha'=${source_sha}
   RETURNING attempt_id`;
   if(rows.length!==1)return respond(res,409,"FENCING_REJECTED");
   return respond(res,200,"RECORDED",{attempt,state:outcome});
 }catch{return respond(res,503,"REPORT_UNCERTAIN");}
}
