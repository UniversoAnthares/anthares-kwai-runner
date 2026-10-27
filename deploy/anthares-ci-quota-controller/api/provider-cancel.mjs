import {neon} from "@neondatabase/serverless";
import {createRemoteJWKSet,jwtVerify} from "jose";
import {randomUUID} from "node:crypto";

const REPO="UniversoAnthares/anthares-kwai-runner";
const WORKFLOW=REPO+"/.github/workflows/ci-quota-external-cancel.yml@refs/heads/main";
const jwks=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const QUOTA=new Set(["ci_quota_exceeded","quota_exceeded","quota_exhausted",
 "insufficient_quota","resource_exhausted","billing_hard_limit_reached",
 "credits_exhausted","usage_limit_reached","monthly_quota_exceeded",
 "daily_quota_exceeded","rate_limit_exceeded"]);
const ident=/^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$/;
const digest=/^[a-f0-9]{40}$/;
function answer(res,status,code,more={}){res.setHeader("Cache-Control","no-store");return res.status(status).json({ok:status<300,code,...more});}
async function remote(url,token,provider,method="GET",body){
 const headers={Accept:"application/json",Authorization:(provider==="appveyor"?"Bearer ":"")+token};
 if(body!==undefined)headers["Content-Type"]="application/json";
 const response=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body),
   signal:AbortSignal.timeout(9000)});
 if(!response.ok&&!(provider==="appveyor"&&response.status===204))
   throw new Error("PROVIDER_"+response.status);
 const data=method==="GET"?await response.json():{};
 return {status:response.status,data};
}
function findCode(remoteData){
 const list=[remoteData?.failure_reason,remoteData?.failure_code,remoteData?.error_code,
   remoteData?.code,remoteData?.message?.code,
   ...((Array.isArray(remoteData?.messages)?remoteData.messages:[]).map(m=>m?.code))];
 return list.filter(x=>typeof x==="string").map(x=>x.trim().toLowerCase()).find(x=>QUOTA.has(x));
}
async function lookup(provider,b,token){
 if(provider==="appveyor"){
   const account=String(b.account||""),project=String(b.project||""),version=String(b.version||"");
   if(!ident.test(account)||!ident.test(project)||!ident.test(version))
     throw new Error("INVALID_TARGET");
   const root="https://ci.appveyor.com/api";
   const base=root+"/projects/"+encodeURIComponent(account)+"/"+encodeURIComponent(project)+"/build/"+encodeURIComponent(version);
   const x=(await remote(base,token,provider)).data;
   if(x.project?.accountName!==account||x.project?.slug!==project
      ||x.project?.repositoryName!==REPO||x.build?.version!==version
      ||x.build?.branch!=="main"||x.build?.commitId!==b.sha)
      throw new Error("OWNERSHIP_MISMATCH");
   return {endpoint:root+"/builds/"+encodeURIComponent(account)+"/"+encodeURIComponent(project)+"/"+encodeURIComponent(version),
     lookup:base,prior:x.build,terminal:["failed","cancelled","canceled"].includes(String(x.build.status).toLowerCase()),
     active:["queued","running","starting"].includes(String(x.build.status).toLowerCase()),
     status:x.build.status};
 }
 const app=String(b.app||""),slug=String(b.build_slug||"");
 if(!ident.test(app)||!ident.test(slug))throw new Error("INVALID_TARGET");
 const base="https://api.bitrise.io/v0.1/apps/"+encodeURIComponent(app);
 const [a,run]=await Promise.all([remote(base,token,provider),remote(base+"/builds/"+encodeURIComponent(slug),token,provider)]);
 const repoUrl=String(a.data?.data?.repo_url||a.data?.repo_url||"");
 const validRepo=repoUrl==="https://github.com/"+REPO||repoUrl==="https://github.com/"+REPO+".git"||
   repoUrl==="git@github.com:"+REPO+".git";
 const data=run.data?.data;
 if(!validRepo||data?.slug!==slug||data?.commit_hash!==b.sha||data?.branch!=="main")
   throw new Error("OWNERSHIP_MISMATCH");
 const status=Number(data.status);
 if(![0,1,2,3,4].includes(status))throw new Error("UNKNOWN_BUILD_STATUS");
 return {endpoint:base+"/builds/"+encodeURIComponent(slug)+"/abort",
   lookup:base+"/builds/"+encodeURIComponent(slug),prior:data,
   terminal:status===2||status===3||status===4,
   active:status===0,status};
}
export default async function handler(req,res){
 if(req.method!=="POST")return answer(res,405,"METHOD_NOT_ALLOWED");
 if(process.env.CI_QUOTA_MODE!=="ENABLED")return answer(res,503,"DISABLED");
 const bearer=/^Bearer ([\w.-]+)$/.exec(req.headers.authorization||"");
 if(!bearer)return answer(res,401,"OIDC_REQUIRED");
 let jwt;
 try{({payload:jwt}=await jwtVerify(bearer[1],jwks,{
   issuer:"https://token.actions.githubusercontent.com",audience:"anthares-ci-quota-controller",
   algorithms:["RS256"]}));}catch{return answer(res,401,"OIDC_INVALID");}
 if(jwt.repository!==REPO||jwt.workflow_ref!==WORKFLOW||!["workflow_dispatch","schedule"].includes(jwt.event_name)
    ||jwt.ref!=="refs/heads/main")
   return answer(res,403,"WORKFLOW_NOT_ALLOWED");
 let b;try{b=typeof req.body==="string"?JSON.parse(req.body):req.body;}catch{return answer(res,400,"JSON_INVALID");}
 if(!b||typeof b!=="object"||!["appveyor","bitrise"].includes(b.provider)
    ||!digest.test(String(b.sha||""))||!QUOTA.has(String(b.code||"")))
    return answer(res,400,"INVALID_QUOTA_EVENT");
 const token=req.headers["x-external-provider-token"];
 if(typeof token!=="string"||token.length<12)
    return answer(res,401,"PROVIDER_CREDENTIAL_MISSING");
 let item;
 try{item=await lookup(b.provider,b,token);}catch{return answer(res,409,"PROVIDER_IDENTITY_UNVERIFIED");}
 const proof=findCode(item.prior);
 if(proof!==b.code)return answer(res,409,"REMOTE_STRUCTURED_QUOTA_PROOF_MISSING");
 if(!item.active&&!item.terminal)return answer(res,409,"SOURCE_UNSAFE_OR_ALREADY_SUCCESS");
 const external=b.provider==="appveyor"?String(b.account)+":"+String(b.project)+":"+String(b.version):
     String(b.app)+":"+String(b.build_slug);
 const key=b.provider+":"+external;
 const owner=randomUUID(),db=neon(process.env.DATABASE_URL);
 let claimed;
 try{claimed=await db`INSERT INTO public.anthares_ci_quota_attempts
  (attempt_id,owner_token,state,data,lease_until)
  VALUES (${key},${owner}::uuid,'CANCEL_REQUESTED',
    ${JSON.stringify({provider:b.provider,external,sha:b.sha,quota_code:b.code,
       state:"CANCEL_REQUESTED",watcher_run_id:String(jwt.run_id),
       side_effects_reconciled:false})}::jsonb,
    now()+interval '90 seconds')
  ON CONFLICT DO NOTHING RETURNING attempt_id`;}
 catch{return answer(res,503,"LEDGER_UNAVAILABLE");}
 if(claimed.length!==1)return answer(res,409,"ATTEMPT_ALREADY_CLAIMED");
 let status="CANCEL_UNCONFIRMED",confirmed="UNKNOWN";
 try{
   if(item.active){
     if(b.provider==="appveyor")await remote(item.endpoint,token,b.provider,"DELETE");
     else await remote(item.endpoint,token,b.provider,"POST",
       {abort_reason:"Confirmed provider quota exhaustion",abort_with_success:false});
   }
   const after=(await remote(item.lookup,token,b.provider)).data;
   const fresh=b.provider==="appveyor"?after.build:after.data;
   if(b.provider==="appveyor"){
      const outcome=String(fresh?.status||"").toLowerCase();
      if(fresh?.version===b.version&&fresh?.commitId===b.sha&&
        ["cancelled","canceled","failed"].includes(outcome)){
         confirmed=outcome;status="CANCELLED_NO_INDEPENDENT_RESERVE";
      }
   }else{
      if(fresh?.slug===b.build_slug&&fresh?.commit_hash===b.sha&&
         [2,3,4].includes(Number(fresh.status))){
         confirmed=String(fresh.status);status="CANCELLED_NO_INDEPENDENT_RESERVE";
      }
   }
 }catch{ /* uncertain provider remote state stays quarantined */ }
 try{
   await db`UPDATE public.anthares_ci_quota_attempts
    SET state=${status},data=data ||
        ${JSON.stringify({state:status,remote_conclusion:confirmed,
          fallback_dispatched:false,side_effects_reconciled:false})}::jsonb,
        lease_generation=lease_generation+1,updated_at=now()
    WHERE attempt_id=${key} AND owner_token=${owner}::uuid AND lease_generation=1`;
 }catch{return answer(res,503,"CANCELLATION_RECEIPT_UNCERTAIN");}
 return answer(res,202,"RECORDED",{attempt:key,state:status,
   remote_conclusion:confirmed,fallback_dispatched:false});
}
