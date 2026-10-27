import { neon } from "@neondatabase/serverless";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { randomUUID } from "node:crypto";

const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const allowedProjects={"87307248":"cortes","87361774":"clipper","87361776":"wordpress"};
const allowedRepo="UniversoAnthares/anthares-kwai-runner";
const allowedWorkflow=allowedRepo+"/.github/workflows/gitlab-quota-watcher.yml@refs/heads/main";

function done(res,status,body){
 res.setHeader("Cache-Control","no-store");return res.status(status).json(body);
}
async function api(token,url){
 const r=await fetch(url,{headers:{"PRIVATE-TOKEN":token,"Accept":"application/json"},
   signal:AbortSignal.timeout(8000)});
 if(!r.ok)throw new Error("UPSTREAM_READ_FAILED");
 return r.json();
}
export default async function handler(req,res){
 if(req.method!=="POST")return done(res,405,{ok:false,code:"METHOD_NOT_ALLOWED"});
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return done(res,503,{ok:false,code:"CONTROLLER_DISABLED"});
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return done(res,401,{ok:false,code:"OIDC_REQUIRED"});
 let claims;
 try {({payload:claims}=await jwtVerify(bearer[1],jwks,{
   issuer:"https://token.actions.githubusercontent.com",
   audience:"anthares-ci-quota-controller",algorithms:["RS256"]}));}
 catch{return done(res,401,{ok:false,code:"OIDC_INVALID"});}
 if(claims.repository!==allowedRepo || claims.workflow_ref!==allowedWorkflow)
    return done(res,403,{ok:false,code:"UNAUTHORIZED_WORKFLOW"});
 let body;
 try{body=typeof req.body==="string"?JSON.parse(req.body):req.body;}
 catch{return done(res,400,{ok:false,code:"INVALID_JSON"});}
 if(!body||typeof body!=="object")return done(res,400,{ok:false,code:"INVALID_BODY"});
 const project=String(body.project_id||"");
 const pipeline=String(body.pipeline_id||"");
 const sha=String(body.sha||"");
 const component=String(body.component||"");
 if(allowedProjects[project]!==component || !/^\d{1,20}$/.test(pipeline)
    || !/^[a-f0-9]{40}$/.test(sha))
   return done(res,400,{ok:false,code:"EVENT_IDENTITY_INVALID"});
 const token=req.headers["x-gitlab-token"];
 if(typeof token!=="string"||token.length<12)
   return done(res,401,{ok:false,code:"GITLAB_TOKEN_REQUIRED"});
 const base="https://gitlab.com/api/v4/projects/"+project+"/pipelines/"+pipeline;
 let remote,jobs;
 try{
   remote=await api(token,base);
   jobs=await api(token,base+"/jobs?per_page=100");
 }catch{return done(res,503,{ok:false,code:"GITLAB_STATUS_UNAVAILABLE"});}
 if(remote.id!==Number(pipeline)||remote.sha!==sha||remote.ref!=="main"
    ||!["failed","canceled"].includes(remote.status))
   return done(res,409,{ok:false,code:"SOURCE_NOT_CONFIRMED_TERMINAL"});
 if(!Array.isArray(jobs)||jobs.length>=100 ||
    !jobs.some(j=>j.failure_reason==="ci_quota_exceeded"&&j.status==="failed"&&!j.started_at)
    || jobs.some(j=>["running","pending","created","preparing","waiting_for_resource"].includes(j.status)))
   return done(res,409,{ok:false,code:"QUOTA_OR_JOB_OWNERSHIP_UNCONFIRMED"});

 const attempt="gitlab:"+project+":"+pipeline;
 const owner=randomUUID();
 let inserted;
 try{
  const sql=neon(process.env.DATABASE_URL);
  inserted=await sql`INSERT INTO public.anthares_ci_quota_attempts
    (attempt_id,owner_token,state,data,lease_until)
    VALUES (${attempt},${owner}::uuid,'FALLBACK_RESERVED',
      ${JSON.stringify({provider:"gitlab_ci",component,project,pipeline,sha,
         state:"FALLBACK_RESERVED",remote_terminal:true,successor_dispatched:false})}::jsonb,
      now()+interval '90 seconds')
    ON CONFLICT (attempt_id) DO NOTHING RETURNING attempt_id`;
 }catch{return done(res,503,{ok:false,code:"SHARED_LEDGER_UNAVAILABLE"});}
 if(inserted.length===0)
   return done(res,409,{ok:false,code:"ALREADY_RESERVED",attempt});
 return done(res,200,{ok:true,state:"FALLBACK_RESERVED",attempt,
     may_dispatch_one_successor:true});
}
