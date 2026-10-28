'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {notifyWakeAfterCommit,SIGNAL_URL,DEVICE}=require('./wake-notifier');
const goodSecret='PUBLISHER_TOKEN_TEST_ONLY_0123456789abcdefghijklmnopqrstuvwxyz';
const env={ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:goodSecret};
test('off by default does not access network',async()=>{
 let called=false;const r=await notifyWakeAfterCommit(DEVICE,{env:{},fetchImpl:async()=>{called=true}});
 assert.equal(r.reason,'disabled');assert.equal(called,false);
});
test('fails closed on missing/invalid key',async()=>{
 for(const secret of [undefined,'short',' '.repeat(64),'x'.repeat(30)+'\n']){
  let called=false;const r=await notifyWakeAfterCommit(DEVICE,{env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},fetchImpl:async()=>{called=true}});
  assert.equal(r.reason,'unconfigured');assert.equal(called,false);
 }
});
test('wrong device never publishes',async()=>{
 let called=false;const r=await notifyWakeAfterCommit('OTHER',{env,fetchImpl:async()=>{called=true}});
 assert.equal(r.reason,'other_device');assert.equal(called,false);
});
test('202 receipt records sequence and sends only device identity',async()=>{
 let seen={};const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async(url,opts)=>{
  seen={url,opts};return{status:202,json:async()=>({ok:true,sequence:17})};
 }});
 assert.deepEqual(r,{enabled:true,ok:true,reason:'broker_recorded',sequence:17});
 assert.equal(seen.url,SIGNAL_URL);assert.equal(seen.opts.method,'POST');assert.equal(seen.opts.redirect,'error');
 assert.deepEqual(JSON.parse(seen.opts.body),{device_id:DEVICE});
 assert.equal(seen.opts.headers['X-Anthares-Notify-Key'],goodSecret);
 assert.doesNotMatch(seen.opts.body,/job|args|secret|token|command/);
});
test('202 without sequence remains accepted without false sequence proof',async()=>{
 const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>({status:202,json:async()=>({ok:true})})});
 assert.deepEqual(r,{enabled:true,ok:true,reason:'broker_accepted'});
});
test('non-202 response returns diagnostic without throwing',async()=>{
 for(const code of [200,400,401,403,409,429,503]){
  const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>({status:code})});
  assert.equal(r.ok,false);assert.equal(r.reason,'http_'+code);
 }
});
test('transport exceptions and timeouts are fail-open to caller',async()=>{
 const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>{throw Error('unavailable')}});
 assert.equal(r.reason,'transport_error');
 const t=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>{throw Object.assign(Error('timeout'),{name:'TimeoutError'})}});
 assert.equal(t.reason,'timeout');
});
