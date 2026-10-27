import {neon} from "@neondatabase/serverless";
import {createRemoteJWKSet,jwtVerify} from "jose";

const ROOT="UniversoAnthares/anthares-kwai-runner";
const WF=ROOT+"/.github/workflows/harness-quota-rescue.yml@refs/heads/main";
const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const PIPELINE_BLOB="bdbbd74b693d2f9fdd6c08b94cc03d8921ebce18";

function reply(res,status,code,data={}){
 res.setHeader("Cache-Control","no-store");
 return res.status(status).json({ok:status<300,code,...data});
}
export default async function handler(req,res){
 if(req.method!=="POST")return reply(res,405,"METHOD_NOT_ALLOWED");
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return reply(res,503,"CONTROLLER_DISABLED");
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return reply(res,401,"GITHUB_OIDC_REQUIRED");
 let claims;
 try {({payload:claims}=await jwtVerify(bearer[1],jwks,{
  issuer:"https://token.actions.githubusercontent.com",
  audience:"anthares-ci-quota-controller",algorithms:["RS256"]}));}
 catch{return reply(res,401,"GITHUB_OIDC_INVALID");}
 if(claims.repository!==ROOT||claims.workflow_ref!==WF||
    claims.ref!=="refs/heads/main"||claims.event_name!=="workflow_dispatch"||
    !/^[0-9]{1,20}$/.test(String(claims.run_id||"")))
  return reply(res,403,"WRONG_EXECUTOR");
 let b;try{b=typeof req.body==="string"?JSON.parse(req.body):req.body;}
 catch{return reply(res,400,"INVALID_JSON");}
 const phase=String(b?.phase||"");
 const execution=String(b?.harness_execution_id||"");
 const sha=String(b?.source_sha||"");
 if(!["start","finish"].includes(phase)||!/^[A-Za-z0-9_-]{16,64}$/.test(execution)
    ||!/^[a-f0-9]{40}$/.test(sha))
   return reply(res,400,"INVALID_SOURCE_IDENTITY");
 const attempt="harness:"+execution,run=String(claims.run_id);
 const sql=neon(process.env.DATABASE_URL);
 if(phase==="start"){
  const patch={state:"FALLBACK_EXECUTING",successor_run_id:run,
    successor_scope:"github_actions_public",executor_identity:"OIDC_AUTHENTICATED",
    source_pipeline_blob:PIPELINE_BLOB};
  try {
   const rows=await sql`UPDATE public.anthares_ci_quota_attempts
     SET state='FALLBACK_EXECUTING',data=data || ${JSON.stringify(patch)}::jsonb,
         lease_generation=lease_generation+1,updated_at=now()
     WHERE attempt_id=${attempt} AND state='FALLBACK_SUBMITTED'
       AND data->>'source_sha'=${sha}
       AND data->>'source_pipeline_blob'=${PIPELINE_BLOB}
       AND data->>'fallback_workflow'='harness-quota-rescue.yml'
       AND data->>'dispatch_accepted'='true'
       AND data->>'provider_terminal_reported'='true'
       AND data->>'side_effects_reconciled'='true'
     RETURNING attempt_id`;
   if(rows.length!==1)return reply(res,409,"NOT_RESERVED_OR_ALREADY_EXECUTING");
   return reply(res,200,"FALLBACK_EXECUTION_AUTHORIZED",{attempt});
  }catch{return reply(res,503,"LEDGER_UNAVAILABLE");}
 }
 const patch={state:"FALLBACK_CONFIRMED",successor_conclusion:"success",
              fallback_evidence:"PINNED_CI_TESTS_PASS",receipt_confirmed:true};
 try {
  const rows=await sql`UPDATE public.anthares_ci_quota_attempts
    SET state='FALLBACK_CONFIRMED',data=data || ${JSON.stringify(patch)}::jsonb,
        lease_generation=lease_generation+1,updated_at=now()
    WHERE attempt_id=${attempt} AND state='FALLBACK_EXECUTING'
      AND data->>'source_sha'=${sha}
      AND data->>'source_pipeline_blob'=${PIPELINE_BLOB}
      AND data->>'successor_run_id'=${run}
    RETURNING attempt_id`;
  if(rows.length!==1)return reply(res,409,"SUCCESS_RECEIPT_FENCING_REJECTED");
  return reply(res,200,"FALLBACK_CONFIRMED",{attempt,github_run_id:run});
 }catch{return reply(res,503,"SUCCESS_RECEIPT_UNAVAILABLE");}
}
