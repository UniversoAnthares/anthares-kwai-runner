import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {signedWake,notifyWakeAfterCommit,WAKE_URL,WAKE_DEVICE} from './wake-notifier.mjs';
const secret='ONLY-UNIT-TEST-EXAMPLE-NOT-A-PRODUCTION-SECRET-0123456789';
const time=Date.parse('2026-10-28T18:00:00Z');
const nonce='11111111-2222-4333-8444-555555555555';

test('wake disabled by default: no network access at all',async()=>{
  let calls=0;
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{env:{},
    fetchImpl:async()=>{calls++;throw Error('network_called')}});
  assert.deepEqual(r,{enabled:false,ok:false,reason:'disabled'});
  assert.equal(calls,0);
});
test('enabled without secret fails closed and never sends',async()=>{
  let calls=0;
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{
    env:{ARA_WAKE_NOTIFY_ENABLED:'1'},
    fetchImpl:async()=>{calls++;throw Error('unexpected_network')}});
  assert.equal(r.reason,'unconfigured');assert.equal(calls,0);
});
test('exact HMAC signature and no job/body/argument leakage',()=>{
  const payload=signedWake(WAKE_DEVICE,secret,time,nonce);
  assert.equal(payload.headers['X-ARA-Wake-Timestamp'],String(time));
  assert.equal(payload.headers['X-ARA-Wake-Signature'],
    crypto.createHmac('sha256',secret).update(String(time)+'\n'+payload.body).digest('hex'));
  assert.deepEqual(Object.keys(JSON.parse(payload.body)).sort(),
    ['created_at_ms','device_id','kind','nonce']);
  assert.doesNotMatch(payload.body,/command|args|job_id|token|secret/);
  assert.throws(()=>signedWake('ANOTHER-PC',secret,time,nonce));
});
test('signed receipt with connected agent confirms delivery count',async()=>{
  const hits=[];
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{
    env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},
    now:time,nonce,fetchImpl:async(url,options)=>{
      hits.push([url,options]);
      return{ok:true,json:async()=>({ok:true,delivered:1})};
    }});
  assert.equal(r.ok,true);assert.equal(r.delivered,1);
  assert.equal(hits.length,1);assert.equal(hits[0][0],WAKE_URL);
  assert.equal(hits[0][1].redirect,'error');
  assert.equal(hits[0][1].headers['X-ARA-Wake-Signature'].length,64);
});
test('no agent connected is not proof of receipt',async()=>{
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{
    env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},
    fetchImpl:async()=>({ok:true,json:async()=>({ok:true,delivered:0})})});
  assert.equal(r.ok,false);assert.equal(r.delivered,0);
});
test('network failure cannot reject the canonical Neon INSERT',async()=>{
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{
    env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},
    fetchImpl:async()=>{throw Error('cloudflare_offline')}});
  assert.equal(r.ok,false);assert.equal(r.reason,'transport_unavailable');
});
test('429/401/403 failures are not silently reported as delivered',async()=>{
  for(const status of [401,403,429,503]){
    const r=await notifyWakeAfterCommit(WAKE_DEVICE,{
      env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},
      fetchImpl:async()=>({ok:false,status})});
    assert.equal(r.ok,false);assert.equal(r.reason,'http_'+status);
  }
});
