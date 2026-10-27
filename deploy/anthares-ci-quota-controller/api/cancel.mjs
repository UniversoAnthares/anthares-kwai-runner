import { neon } from "@neondatabase/serverless";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { randomUUID } from "node:crypto";

const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const QUOTA=new Set(["ci_quota_exceeded","quota_exceeded","quota_exhausted",
  "insufficient_quota","resource_exhausted","billing_hard_limit_reached",
  "credits_exhausted","usage_limit_reached","monthly_quota_exceeded",
  "daily_quota_exceeded","rate_limit_exceeded"]);
const REPOS=new Set(["UniversoAnthares/anthares-kwai-runner","UniversoAnthares/anthares-clipper"]);
const maxBody=8192;

function reject(res,status,code){res.setHeader("Cache-Control","no-store");return res.status(status).json({ok:false,code});}

async function github(token,repo,id,method,extra=""){
  const url="https://api.github.com/repos/"+repo+"/actions/runs/"+id+extra;
  const r=await fetch(url,{method,headers:{"Authorization":"Bearer "+token,
    "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},
    signal:AbortSignal.timeout(7000)});
  let data={};
  if(method==="GET"&&r.ok){data=await r.json();}
  return {status:r.status,data};
}

export default async function handler(req,res){
  res.setHeader("Cache-Control","no-store");
  if(req.method!=="POST")return reject(res,405,"METHOD_NOT_ALLOWED");
  if(process.env.CI_QUOTA_MODE!=="ENABLED")return reject(res,503,"CONTROLLER_DISABLED");
  if(!process.env.DATABASE_URL)return reject(res,503,"DATABASE_UNCONFIGURED");
  if(Number(req.headers["content-length"]||0)>maxBody)return reject(res,413,"BODY_TOO_LARGE");
  const auth=/^Bearer ([A-Za-z0-9._-]+)$/.exec(req.headers.authorization||"");
  if(!auth)return reject(res,401,"OIDC_REQUIRED");
  let claims;
  try{
    ({payload:claims}=await jwtVerify(auth[1],jwks,{
      issuer:"https://token.actions.githubusercontent.com",
      audience:"anthares-ci-quota-controller",
      algorithms:["RS256"]
    }));
  }catch{return reject(res,401,"OIDC_INVALID");}
  const body=typeof req.body==="string"?JSON.parse(req.body):req.body;
  if(!body||typeof body!=="object")return reject(res,400,"INVALID_BODY");
  const repo=String(claims.repository||"");
  const run=String(claims.run_id||"");
  const providerCode=String(body.provider_code||"").trim().toLowerCase();
  if(!REPOS.has(repo)||body.repository!==repo||
     !/^\d{1,20}$/.test(run)||String(body.run_id)!==run ||
     !QUOTA.has(providerCode) || claims.repository_owner!=="UniversoAnthares")
    return reject(res,403,"OWNERSHIP_OR_QUOTA_INVALID");
  const githubToken=req.headers["x-github-actions-token"];
  if(typeof githubToken!=="string" || !/^[A-Za-z0-9_\-]{20,}$/.test(githubToken))
    return reject(res,401,"GITHUB_RUN_TOKEN_REQUIRED");

  let initial;
  try{initial=await github(githubToken,repo,run,"GET");}
  catch{return reject(res,503,"REMOTE_STATUS_UNAVAILABLE");}
  if(initial.status!==200)return reject(res,503,"REMOTE_STATUS_UNAVAILABLE");
  if(initial.data.id!==Number(run) || initial.data.repository?.full_name!==repo)
    return reject(res,403,"RUN_IDENTITY_UNVERIFIED");

  const attempt="github:"+repo+":"+run;
  const owner=randomUUID();
  const sql=neon(process.env.DATABASE_URL);
  let inserted;
  try {
    inserted=await sql`INSERT INTO public.anthares_ci_quota_attempts
     (attempt_id,owner_token,state,data,lease_until)
     VALUES (${attempt},${owner}::uuid,'CANCEL_REQUESTED',
       ${JSON.stringify({provider:"github_actions",repo,run,provider_code:providerCode,
                          state:"CANCEL_REQUESTED",side_effects_reconciled:false})}::jsonb,
       now()+interval '90 seconds')
     ON CONFLICT (attempt_id) DO NOTHING RETURNING attempt_id`;
  }catch{return reject(res,503,"LEDGER_UNAVAILABLE");}
  if(inserted.length===0)return res.status(202).json({ok:true,state:"ALREADY_OWNED",attempt});

  let next="CANCEL_UNCONFIRMED",observed="UNKNOWN";
  try {
    if(initial.data.status==="completed"){
      observed=String(initial.data.conclusion||"UNKNOWN").toUpperCase();
      next=observed==="SUCCESS"?"RECONCILE_REQUIRED":"CANCELLED_NO_INDEPENDENT_RESERVE";
    }else{
      const sent=await github(githubToken,repo,run,"POST","/cancel");
      if(![202,204,409].includes(sent.status)){
        next="CANCEL_UNCONFIRMED";
      }else{
        const current=await github(githubToken,repo,run,"GET");
        if(current.status===200&&current.data.status==="completed"){
          observed=String(current.data.conclusion||"UNKNOWN").toUpperCase();
          next=observed==="SUCCESS"?"RECONCILE_REQUIRED":"CANCELLED_NO_INDEPENDENT_RESERVE";
        }
      }
    }
  }catch{next="CANCEL_UNCONFIRMED";}
  try{
    await sql`UPDATE public.anthares_ci_quota_attempts
       SET state=${next},
         data=${JSON.stringify({provider:"github_actions",repo,run,provider_code:providerCode,
                                 state:next,provider_conclusion:observed,
                                 side_effects_reconciled:false})}::jsonb,
         updated_at=now(), lease_generation=lease_generation+1
       WHERE attempt_id=${attempt} AND owner_token=${owner}::uuid
         AND lease_generation=1`;
  }catch{return reject(res,503,"LEDGER_FINALIZATION_UNCERTAIN");}
  return res.status(202).json({ok:true,state:next,attempt,remote_conclusion:observed,
    fallback_dispatched:false});
}
