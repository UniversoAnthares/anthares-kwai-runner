import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareWake,notifyWakeAfterCommit,WAKE_URL,WAKE_DEVICE} from './wake-notifier.mjs';
const secret='EXAMPLE_TEST_ONLY_PUBLISHER_TOKEN_0000000000000000000000000';
const env={ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret};

test('default off makes no network call',async()=>{
  let called=false;
  assert.deepEqual(await notifyWakeAfterCommit(WAKE_DEVICE,{env:{},fetchImpl:async()=>{called=true;}}),
    {enabled:false,ok:false,reason:'disabled'});
  assert.equal(called,false);
});
test('secret missing or invalid fails closed',async()=>{
  for(const invalid of [undefined,'too-short','A'.repeat(33)+'\r']){
    let called=false;
    const ret=await notifyWakeAfterCommit(WAKE_DEVICE,{env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:invalid},
      fetchImpl:async()=>{called=true;}});
    assert.equal(ret.reason,'unconfigured');assert.equal(called,false);
  }
});
test('only device identity is transmitted, never jobs or commands',()=>{
  const req=prepareWake(WAKE_DEVICE,secret);
  assert.deepEqual(JSON.parse(req.body),{device_id:WAKE_DEVICE});
  assert.equal(req.headers['X-Anthares-Notify-Key'],secret);
  assert.throws(()=>prepareWake('WRONG-DEVICE',secret));
  assert.doesNotMatch(req.body,/command|args|job_id|token|secret/);
});
test('recorded wake returns broker sequence, not device delivery',async()=>{
  let calls=[];
  const ret=await notifyWakeAfterCommit(WAKE_DEVICE,{env,fetchImpl:async(u,o)=>{
    calls.push({u,o});return{status:202,json:async()=>({ok:true,protocol:'ara-wake-v1',sequence:42})};
  }});
  assert.deepEqual(ret,{enabled:true,ok:true,reason:'broker_recorded',sequence:42});
  assert.equal(calls[0].u,WAKE_URL);
  assert.equal(calls[0].o.method,'POST');
  assert.equal(calls[0].o.redirect,'error');
  assert.deepEqual(JSON.parse(calls[0].o.body),{device_id:WAKE_DEVICE});
});
test('HTTP success with wrong or missing receipt is unconfirmed',async()=>{
  for(const json of [{ok:true,delivered:1},{ok:true,protocol:'ara-wake-v1',sequence:0},
    {ok:false,protocol:'ara-wake-v1',sequence:2}]){
    const r=await notifyWakeAfterCommit(WAKE_DEVICE,{env,fetchImpl:async()=>({status:202,json:async()=>json})});
    assert.equal(r.ok,false);assert.equal(r.reason,'bad_receipt');
  }
});
test('HTTP status 200,401,403,409,429,503 are not broker receipts',async()=>{
  for(const status of [200,401,403,409,429,503]){
    const r=await notifyWakeAfterCommit(WAKE_DEVICE,{env,fetchImpl:async()=>({status})});
    assert.equal(r.ok,false);assert.equal(r.reason,'http_'+status);
  }
});
test('Hostinger outage never rejects the committed Neon insert',async()=>{
  const r=await notifyWakeAfterCommit(WAKE_DEVICE,{env,fetchImpl:async()=>{throw Error('network_down')}});
  assert.deepEqual(r,{enabled:true,ok:false,reason:'transport_unavailable'});
});
