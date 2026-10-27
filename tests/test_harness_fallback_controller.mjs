// Harness read-only successor OIDC + Neon CAS contract (mock I/O only).
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const source=readFileSync(new URL(
  "../deploy/anthares-ci-quota-controller/api/harness-fallback-verify.mjs",
  import.meta.url),"utf8");
const transformed=source.replace(/^import .*;\s*$/gm,"")
  .replace("export default async function handler","async function handler");
let state="FALLBACK_SUBMITTED",runId="123",wrongIdentity=false;
const queries=[];
const neon=()=>async (strings,...args)=>{
 const sql=strings.join("?");
 queries.push(sql);
 assert.ok(sql.includes("UPDATE public.anthares_ci_quota_attempts"));
 assert.ok(sql.includes("data->>'source_sha'"));
 assert.ok(sql.includes("data->>'source_pipeline_blob'"));
 if(state==="FALLBACK_SUBMITTED"&&sql.includes("state='FALLBACK_SUBMITTED'")){
   state="FALLBACK_EXECUTING";return [{attempt_id:"harness:owned"}];
 }
 if(state==="FALLBACK_EXECUTING"&&sql.includes("state='FALLBACK_EXECUTING'")
    &&args.some(x=>x===runId)){
   state="FALLBACK_CONFIRMED";return [{attempt_id:"harness:owned"}];
 }
 return [];
};
const jwtVerify=async()=>({payload:{
 repository:"UniversoAnthares/anthares-kwai-runner",
 workflow_ref:wrongIdentity?"foreign":
 "UniversoAnthares/anthares-kwai-runner/.github/workflows/harness-quota-rescue.yml@refs/heads/main",
 ref:"refs/heads/main",event_name:"workflow_dispatch",run_id:runId
}});
const handler=new Function("neon","createRemoteJWKSet","jwtVerify","process","URL",
 transformed+";return handler;")(
 neon,()=>({}),jwtVerify,{env:{CI_QUOTA_MODE:"ENABLED",DATABASE_URL:"mock"}},URL);
async function invoke(phase,sha="a".repeat(40),execution="abcdefghijklmnop"){
 const output={statusCode:null,body:null};
 const res={setHeader(){},status(x){output.statusCode=x;return this;},
            json(x){output.body=x;return this;}};
 await handler({method:"POST",headers:{authorization:"Bearer synthetic"},
  body:{phase,source_sha:sha,harness_execution_id:execution}},res);
 return output;
}
const invalid=await invoke("start","not-a-sha");
assert.equal(invalid.statusCode,400);
wrongIdentity=true;
assert.equal((await invoke("start")).statusCode,403);
wrongIdentity=false;
assert.equal((await invoke("finish")).statusCode,409);
const start=await invoke("start");
assert.equal(start.statusCode,200);
assert.equal(start.body.code,"FALLBACK_EXECUTION_AUTHORIZED");
assert.equal((await invoke("start")).statusCode,409);
runId="456";
assert.equal((await invoke("finish")).statusCode,409);
runId="123";
const finish=await invoke("finish");
assert.equal(finish.statusCode,200);
assert.equal(finish.body.code,"FALLBACK_CONFIRMED");
assert.equal((await invoke("finish")).statusCode,409);
assert.equal(state,"FALLBACK_CONFIRMED");
assert.equal(queries.length,6);
assert.ok(queries.some(q=>q.includes("dispatch_accepted")));
assert.ok(queries.some(q=>q.includes("successor_run_id")));
console.log("HARNESS_FALLBACK_OIDC_NEON_FENCE=PASS CASES=8 MOCKED_IO=true");
