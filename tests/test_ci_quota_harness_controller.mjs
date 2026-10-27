// Contract test of the serverless controller with dependency injection.
// Does not use a real JWT, provider credential, or Neon connection.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {randomUUID} from "node:crypto";

const local = new URL("../deploy/anthares-ci-quota-controller/api/provider-cancel.mjs", import.meta.url);
const source = process.env.ANTHARES_CONTROLLER_SOURCE_URL
  ? await (await fetch(process.env.ANTHARES_CONTROLLER_SOURCE_URL)).text()
  : readFileSync(local, "utf8");
assert.ok(source.includes("export default async function handler"), "source unavailable");
const body = source.replace(/^import .*;\s*$/gm, "")
  .replace("export default async function handler", "async function handler");
const requests = [];
let simulatedLeaseExpired = false;
const pg = () => async (strings, ...args) => {
  requests.push(args);
  if (strings.join("").includes("INSERT INTO")) return [{attempt_id: "claimed"}];
  if (strings.join("").includes("UPDATE public.")) {
    assert.ok(strings.join("").includes("lease_until>now()"),
              "expired claim must not be allowed to report");
    return simulatedLeaseExpired ? [] : [{attempt_id: "claimed"}];
  }
  throw Error("UNEXPECTED_QUERY");
};
const fakeJwtVerify = async () => ({payload:{
  repository:"UniversoAnthares/anthares-kwai-runner",
  workflow_ref:"UniversoAnthares/anthares-kwai-runner/.github/workflows/ci-quota-external-cancel.yml@refs/heads/main",
  ref:"refs/heads/main", event_name:"workflow_dispatch", run_id:"123"
}});
const handler = new Function("neon","createRemoteJWKSet","jwtVerify","randomUUID",
  "createPublicKey","verify","process","URL", body + ";return handler;")(
  pg, ()=>({}), fakeJwtVerify,randomUUID,()=>{throw Error("RSA_NOT_USED");},
  ()=>{throw Error("RSA_NOT_USED");},{env:{CI_QUOTA_MODE:"ENABLED",DATABASE_URL:"mock"}},URL);

async function invoke(payload){
  const result={statusCode:0,response:null};
  const res={setHeader(){},status(x){result.statusCode=x;return this;},
             json(v){result.response=v;return this;}};
  await handler({method:"POST",headers:{authorization:"Bearer synthetic"},
                 body:payload},res);
  return result;
}
const event={provider:"harness",target:"abcdef0123456789ABCDabcd",
  code:"quota_exceeded",sha:"a".repeat(40)};
const good=await invoke({...event,phase:"claim"});
assert.equal(good.statusCode,200);assert.equal(good.response.code,"CLAIMED");
assert.equal(requests.length,1);
const invalid=await invoke({...event,target:"short",phase:"claim"});
assert.equal(invalid.statusCode,400);
assert.equal(invalid.response.code,"INVALID_HARNESS_EXECUTION");
assert.equal(requests.length,1);
const unauthorizedProvider=await invoke({...event,provider:"other",phase:"claim"});
assert.equal(unauthorizedProvider.statusCode,400);
assert.equal(requests.length,1);
const permission=await invoke({...event,code:"forbidden",phase:"claim"});
assert.equal(permission.statusCode,400);
assert.equal(requests.length,1);
const report=await invoke({...event,phase:"report",owner_token:randomUUID(),
  outcome:"CANCEL_UNCONFIRMED"});
assert.equal(report.statusCode,200);assert.equal(report.response.code,"RECORDED");
assert.equal(requests.length,2);
simulatedLeaseExpired = true;
const expired=await invoke({...event,phase:"report",owner_token:randomUUID(),
  outcome:"CANCEL_UNCONFIRMED"});
assert.equal(expired.statusCode,409);
assert.equal(expired.response.code,"FENCING_REJECTED");
assert.equal(requests.length,3);
// An explicit reserve is allowed only after the report on the exact owner
// token and source SHA. Mocked Neon validates lease and CAS predicate text.
simulatedLeaseExpired = false;
const reviewedBlob="bdbbd74b693d2f9fdd6c08b94cc03d8921ebce18";
const fallbackEvent={...event,owner_token:randomUUID(),
                     pipeline_blob:reviewedBlob};
const foreignSource=await invoke({...fallbackEvent,phase:"reserve",
                                    pipeline_blob:"f".repeat(40)});
assert.equal(foreignSource.statusCode,409);
assert.equal(foreignSource.response.code,"SIDE_EFFECT_FREE_PIPELINE_NOT_PROVEN");
const reserve=await invoke({...fallbackEvent,phase:"reserve"});
assert.equal(reserve.statusCode,200);
assert.equal(reserve.response.code,"FALLBACK_RESERVED");
const reserveQuery=requests.at(-1);
assert.ok(reserveQuery.includes("harness:"+event.target));
const reserveRejected=await invoke({...fallbackEvent,phase:"ack",
                                     dispatch_status:"200"});
assert.equal(reserveRejected.statusCode,400);
const ack=await invoke({...fallbackEvent,phase:"ack",dispatch_status:"204"});
assert.equal(ack.statusCode,200);
assert.equal(ack.response.code,"FALLBACK_SUBMITTED");
simulatedLeaseExpired = true;
const stale=await invoke({...fallbackEvent,phase:"reserve"});
assert.equal(stale.statusCode,409);
assert.equal(stale.response.code,"FALLBACK_RESERVATION_REJECTED");
assert.ok(source.includes("provider_terminal_reported"));
assert.ok(source.includes("data->>'owner_run'"));
assert.ok(source.includes("lease_generation=2"));
assert.ok(source.includes("lease_generation=3"));
console.log("HARNESS_NEON_CONTROLLER_CONTRACT=PASS CASES=11 MOCKED_IO=true EXPIRED_LEASE=REJECTED");
