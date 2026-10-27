import { neon } from "@neondatabase/serverless";
import { createRemoteJWKSet, jwtVerify } from "jose";

const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const repo="UniversoAnthares/anthares-kwai-runner";
const workflow=repo+"/.github/workflows/gitlab-quota-watcher.yml@refs/heads/main";
const projects={"87307248":"cortes","87361774":"clipper","87361776":"wordpress"};

function reply(res,status,data){res.setHeader("Cache-Control","no-store");return res.status(status).json(data)}
export default async function handler(req,res){
 if(req.method!=="POST")return reply(res,405,{ok:false,code:"METHOD_NOT_ALLOWED"});
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return reply(res,503,{ok:false,code:"DISABLED"});
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return reply(res,401,{ok:false,code:"OIDC_REQUIRED"});
 let claims;try{({payload:claims}=await jwtVerify(bearer[1],jwks,{
   issuer:"https://token.actions.githubusercontent.com",audience:"anthares-ci-quota-controller",
   algorithms:["RS256"]}));}catch{return reply(res,401,{ok:false,code:"OIDC_INVALID"});}
 if(claims.repository!==repo||claims.workflow_ref!==workflow)
  return reply(res,403,{ok:false,code:"WORKFLOW_NOT_AUTHORIZED"});
 let b;try{b=typeof req.body==="string"?JSON.parse(req.body):req.body;}catch{return reply(res,400,{ok:false,code:"INVALID_BODY"});}
 const project=String(b?.project_id||""),pipeline=String(b?.pipeline_id||"");
 const sha=String(b?.sha||""),component=String(b?.component||"");
 const watcherRun=String(b?.watcher_run_id||"");
 if(projects[project]!==component||!/^[0-9]{1,20}$/.test(pipeline)
    || !/^[a-f0-9]{40}$/.test(sha)
    || watcherRun!==String(claims.run_id))
  return reply(res,403,{ok:false,code:"RECEIPT_IDENTITY_UNVERIFIED"});
 const attempt="gitlab:"+project+":"+pipeline;
 try{
  const sql=neon(process.env.DATABASE_URL);
  const patch={state:"FALLBACK_SUBMITTED",successor_dispatched:true,
     dispatch_accepted:true,dispatch_http_status:204,
     dispatch_watcher_run_id:watcherRun,dispatch_workflow:
        component==="cortes"?"gitlab-quota-fallback.yml":"private-ci-quota-rescue.yml"};
  const rows=await sql`UPDATE public.anthares_ci_quota_attempts
     SET state='FALLBACK_SUBMITTED',data=data || ${JSON.stringify(patch)}::jsonb,
         lease_generation=lease_generation+1,updated_at=now()
     WHERE attempt_id=${attempt} AND state='FALLBACK_RESERVED'
       AND data->>'sha'=${sha} AND data->>'component'=${component}
       AND lease_until>now() RETURNING attempt_id,lease_generation`;
  if(rows.length!==1)return reply(res,409,{ok:false,code:"RESERVATION_MISSING_OR_ALREADY_USED"});
  return reply(res,200,{ok:true,state:"FALLBACK_SUBMITTED",attempt,
    dispatch_acceptance_recorded:true});
 }catch{return reply(res,503,{ok:false,code:"LEDGER_ACK_UNAVAILABLE"});}
}
