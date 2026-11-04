import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {DEVICE_ID,sha256hex,safeHexEquals,validAgentToken,wakeMac,
        verifyWakeNotification,makeWakeMessage} from './protocol.mjs';
const c=globalThis.crypto||webcrypto;
const secret='ONLY-UNIT-TEST-EXAMPLE-NOT-A-PRODUCTION-SECRET-0123456789';
const now=Date.parse('2026-10-28T18:00:00Z');
const body=JSON.stringify({device_id:DEVICE_ID,kind:'jobs_available',
  created_at_ms:now,nonce:'11111111-2222-4333-8444-555555555555'});
async function signed(payload=body,timestamp=now,overrideMac=null){
  return new Request('https://wake.invalid/notify',{method:'POST',
    headers:{'X-ARA-Wake-Timestamp':String(timestamp),
      'X-ARA-Wake-Signature':overrideMac||await wakeMac(secret,timestamp,payload,c)},
    body:payload});
}
test('valid wake contains no job or command',async()=>{
  assert.deepEqual(await verifyWakeNotification(await signed(),secret,now,c),
    {ok:true,code:'authorized_wake',device_id:DEVICE_ID});
  assert.deepEqual(Object.keys(JSON.parse(makeWakeMessage(now,'test-nonce'))).sort(),
    ['at_ms','nonce','type']);
});
test('missing secret and invalid HMAC fail closed',async()=>{
  assert.equal((await verifyWakeNotification(await signed(),'',now,c)).code,'not_configured');
  assert.equal((await verifyWakeNotification(await signed(body,now,'0'.repeat(64)),secret,now,c)).code,'invalid_signature');
});
test('stale timestamp is rejected',async()=>{
  assert.equal((await verifyWakeNotification(await signed(body,now-31_000),secret,now,c)).code,'invalid_timestamp');
});
test('tampering with signed content is rejected',async()=>{
  const x=new Request('https://wake.invalid/notify',{method:'POST',
    headers:{'X-ARA-Wake-Timestamp':String(now),'X-ARA-Wake-Signature':await wakeMac(secret,now,body,c)},
    body:body.replace(DEVICE_ID,'FOREIGN-PC')});
  assert.equal((await verifyWakeNotification(x,secret,now,c)).code,'invalid_signature');
});
test('foreign device, commands and unknown event types fail',async()=>{
  for(const v of [{...JSON.parse(body),device_id:'FOREIGN-PC'},
                   {...JSON.parse(body),command:'shell'},
                   {...JSON.parse(body),kind:'execute'}]){
    assert.equal((await verifyWakeNotification(await signed(JSON.stringify(v)),secret,now,c)).code,'invalid_event');
  }
});
test('oversized payload is rejected',async()=>{
  assert.equal((await verifyWakeNotification(await signed('x'.repeat(257)),secret,now,c)).code,'oversized_body');
});
test('canonical bearer SHA-256 is verified, not token presence',async()=>{
  const token='example-long-device-secret-for-test-only';
  const hash=await sha256hex(token,c);
  assert.equal(await validAgentToken(token,hash,c),true);
  assert.equal(await validAgentToken(token+'x',hash,c),false);
  assert.equal(await validAgentToken('',hash,c),false);
  assert.equal(safeHexEquals('g'.repeat(64),hash),false);
});
