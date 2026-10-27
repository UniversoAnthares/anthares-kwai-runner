import { neon } from "@neondatabase/serverless";
import { createRemoteJWKSet, jwtVerify } from "jose";

const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const repo="UniversoAnthares/anthares-kwai-runner";
const workflow=repo+"/.github/workflows/gitlab-quota-watcher.yml@refs/heads/main";
const projects={"87307248":"cortes","87361774":"clipper","87361776":"wordpress"};

function out(res,status,body){res.setHeader("Cache-Control","no-store");return res.status(status).json(body)}
export default async function handler(req,res){
 if(req.method!=="POST")return out(res,405,{ok:false,code:"METHOD_NOT_ALLOWED"});
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return out(res,503,{ok:false,code:"DISABLED"});
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return out(res,401,{ok:false,code:"OIDC_REQUIRED"});
 let claims;
 try {({payload:claims}=await jwtVerify(bearer[1],jwks,{
  issuer:"https://token.actions.githubusercontent.com",
  audience:"anthares-ci-quota-controller",algorithms:["RS256"]}));}
 catch{return out(res,401,{ok:false,code:"OIDC_INVALID"});}
 if(claims.repository!==repo||claims.workflow_ref!==workflow)
   return out(res,403,{ok:false,code:"WORKFLOW_UNAUTHORIZED"});
 let body;try{body=typeof req.body==="string"?JSON.parse(req.body):req.body;}catch{return out(res,400,{ok:false,code:"INVALID_BODY"});}
 const project=String(body?.project_id||""),pipeline=String(body?.pipeline_id||"");
 const sha=String(body?.sha||""),component=String(body?.component||"");
 const runId=String(body?.github_run_id||"");
 if(projects[project]!==component||!/^\d{1,20}$/.test(pipeline)||
    !/^\d{1,20}$/.test(runId)||!/^[a-f0-9]{40}$/.test(sha))
   return out(res,400,{ok:false,code:"UNVERIFIED_EVENT"});

 const token=req.headers["x-github-actions-token"];
 if(typeof token!=="string"||token.length<20)
   return out(res,401,{ok:false,code:"GITHUB_TOKEN_REQUIRED"});
 let run;
 try{
  const r=await fetch("https://api.github.com/repos/"+repo+"/actions/runs/"+runId,{
    headers:{"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json"},
    signal:AbortSignal.timeout(7000)});
  if(!r.ok)return out(res,503,{ok:false,code:"RUN_STATUS_UNAVAILABLE"});
  run=await r.json();
 }catch{return out(res,503,{ok:false,code:"RUN_STATUS_UNAVAILABLE"});}
 const wantWorkflow=component==="cortes"?"gitlab-quota-fallback.yml":"private-ci-quota-rescue.yml";
 const marker="quota-rescue-"+component+"-glsha-"+sha;
 if(run.id!==Number(runId)||run.repository?.full_name!==repo||run.event!=="workflow_dispatch"||
    run.status!=="completed"||run.conclusion!=="success"||
    !String(run.path||"").endsWith("/"+wantWorkflow)||
    !String(run.display_title||"").includes(marker))
   return out(res,409,{ok:false,code:"SUCCESS_RECEIPT_NOT_CONFIRMED"});
 const attempt="gitlab:"+project+":"+pipeline;
 try{
  const sql=neon(process.env.DATABASE_URL);
  const patch={state:"FALLBACK_CONFIRMED",successor_dispatched:true,
    successor_run_id:runId,successor_conclusion:"success",receipt_confirmed:true};
  const rows=await sql`UPDATE public.anthares_ci_quota_attempts
   SET state='FALLBACK_CONFIRMED',data=data || ${JSON.stringify(patch)}::jsonb,
       lease_generation=lease_generation+1,updated_at=now()
   WHERE attempt_id=${attempt}
     AND state IN ('FALLBACK_SUBMITTED','FALLBACK_RESERVED')
     AND data->>'sha'=${sha} AND data->>'component'=${component}
   RETURNING attempt_id,lease_generation`;
  if(rows.length===1)return out(res,200,{ok:true,state:"FALLBACK_CONFIRMED",
    attempt,successor_run_id:runId});
  const existing=await sql`SELECT state,data->>'successor_run_id' AS recorded_run
     FROM public.anthares_ci_quota_attempts WHERE attempt_id=${attempt}`;
  if(existing.length===1&&existing[0].state==="FALLBACK_CONFIRMED"&&
      existing[0].recorded_run===runId)
      return out(res,200,{ok:true,state:"ALREADY_CONFIRMED",attempt});
  return out(res,409,{ok:false,code:"RESERVATION_NOT_RECONCILABLE"});
 }catch{return out(res,503,{ok:false,code:"LEDGER_RECONCILIATION_UNAVAILABLE"});}
}
