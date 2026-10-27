import test from "node:test";
import assert from "node:assert/strict";
import {validateIntent,dispatchCodeberg,verifyReadback} from "../tools/codeberg_fenced_dispatch.mjs";
const base={repository:"UniversoAnthares/anthares-video-studio",workflow:"avs-d1-live-homologation.yml",ref:"main",sha:"a".repeat(40),attemptId:"gitlab:12345678",nonpublishing:true,originalTerminal:true,sideEffects:"NOT_APPLIED",fenceWon:true,independentQuotaHealthy:true};
test("reject publishing, absent fence, uncertain side effects",()=>{
  for(const delta of [{nonpublishing:false},{fenceWon:false},{sideEffects:"UNKNOWN"},{originalTerminal:false},{independentQuotaHealthy:false}])
    assert.throws(()=>validateIntent({...base,...delta}),/GUARD_REJECTED/);
});
test("dispatch with pin and durable receipt; never retry",async()=>{
 const states=[];
 const fetcher=async(u,opts)=>u.endsWith("/branches/main")?{ok:true,json:async()=>({commit:{id:base.sha}})}:{status:204};
 const a=await dispatchCodeberg({intent:base,token:"valid-test-token",fetcher,receipt:async r=>(states.push(r.status),true)});
 assert.equal(a.state,"DISPATCH_ACCEPTED");assert.deepEqual(states,["DISPATCH_INTENT","DISPATCH_ACCEPTED"]);
});
test("ambiguous response is never retried",async()=>{
 const states=[];
 const fetcher=async(u)=>u.endsWith("/branches/main")?{ok:true,json:async()=>({commit:{id:base.sha}})}:Promise.reject(Error("timeout"));
 const a=await dispatchCodeberg({intent:base,token:"valid-test-token",fetcher,receipt:async r=>(states.push(r.status),true)});
 assert.equal(a.state,"DISPATCH_UNCERTAIN");assert.equal(a.retryAllowed,false);
});
test("pin mismatch prevents write",async()=>{
 let calls=0;const fetcher=async()=>{calls++;return {ok:true,json:async()=>({commit:{id:"b".repeat(40)}})}};
 await assert.rejects(dispatchCodeberg({intent:base,token:"valid-test-token",fetcher,receipt:async()=>true}),/HEAD_MISMATCH/);
 assert.equal(calls,1);
});
test("readback requires pinned terminal success",()=>{
 assert.equal(verifyReadback({id:2,sha:base.sha,conclusion:"success"},base.sha).state,"SUCCESS");
 assert.equal(verifyReadback({id:2,sha:base.sha,conclusion:"success"},"b".repeat(40)).state,"UNVERIFIED");
});
