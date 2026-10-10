import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {handleKwaiSessionVault} from '../cloudflare-worker/src/kwai_session_vault.js';

const URL='https://anthares-control.anthares1.workers.dev/kwai/session-vault';
const workflow='UniversoAnthares/anthares-kwai-runner/.github/workflows/kwai-queue-publisher.yml@refs/heads/main';
const claims={repository:'UniversoAnthares/anthares-kwai-runner',job_workflow_ref:workflow};
const ok=async()=>({ok:true,claims});
const denied=async()=>({ok:false});
function env(){
  const store=new Map();
  return {store,ANTHARES_STATE:{
    get:async k=>JSON.parse(store.get(k)||'null'),
    put:async(k,v)=>store.set(k,v)
  }};
}
function req(method='GET',body){
  return new Request(URL,{method,headers:{Authorization:'Bearer test-oidc-token'},body:body&&JSON.stringify(body)});
}
const ciphertext='U2FsdGVkX1'+'A'.repeat(100);
const sha256=createHash('sha256').update(ciphertext).digest('hex');

test('unauthorized request never reads vault',async()=>{
  const e=env();
  const r=await handleKwaiSessionVault(req(),e,denied);
  assert.equal(r.status,401);
});
test('no durable binding fails closed',async()=>{
  const r=await handleKwaiSessionVault(req(),{},ok);
  assert.equal(r.status,503);
});
test('rejects unencrypted Android archive and wrong digest',async()=>{
  const e=env();
  assert.equal((await handleKwaiSessionVault(req('POST',{account:'lucasrosalem',ciphertext:'raw cookies',sha256}),e,ok)).status,422);
  assert.equal((await handleKwaiSessionVault(req('POST',{account:'lucasrosalem',ciphertext,sha256:'0'.repeat(64)}),e,ok)).status,422);
  assert.equal(e.store.size,0);
});
test('ciphertext survives independent handler invocations with no plaintext stored',async()=>{
  const e=env();
  const post=await handleKwaiSessionVault(req('POST',{account:'lucasrosalem',ciphertext,sha256}),e,ok);
  assert.equal(post.status,200);
  const read=await handleKwaiSessionVault(req(),e,ok);
  const data=await read.json();
  assert.equal(data.ciphertext,ciphertext);
  assert.equal(data.sha256,sha256);
  assert.equal(data.account,'lucasrosalem');
  assert.equal(e.store.size,1);
  assert.equal(JSON.stringify([...e.store.values()]).includes('KWAI_PASSWORD'),false);
});
test('probe reveals only storage readiness, not encrypted session',async()=>{
  const e=env();
  const request=new Request(URL+'?probe=1',{headers:{Authorization:'Bearer test-oidc-token'}});
  const response=await handleKwaiSessionVault(request,e,ok);
  const data=await response.json();
  assert.equal(data.persistent,true);
  assert.equal(data.available,false);
  assert.equal('ciphertext' in data,false);
});
test('wrong workflow cannot access stored session',async()=>{
  const e=env();
  const bad=async()=>({ok:true,claims:{...claims,job_workflow_ref:'other.yml'}});
  assert.equal((await handleKwaiSessionVault(req(),e,bad)).status,401);
});
test('dedicated probe workflow cannot read or write any session ciphertext',async()=>{
  const e=env();
  const probeWorkflow='UniversoAnthares/anthares-kwai-runner/.github/workflows/kwai-private-vault-probe.yml@refs/heads/main';
  const probeAuth=async()=>({ok:true,claims:{...claims,job_workflow_ref:probeWorkflow}});
  const health=new Request(URL+'?probe=1',{headers:{Authorization:'Bearer test-oidc-token'}});
  assert.equal((await handleKwaiSessionVault(health,e,probeAuth)).status,200);
  assert.equal((await handleKwaiSessionVault(req(),e,probeAuth)).status,401);
  assert.equal((await handleKwaiSessionVault(req('POST',{account:'lucasrosalem',ciphertext,sha256}),e,probeAuth)).status,401);
});
test('tampered stored ciphertext is rejected',async()=>{
  const e=env();
  await handleKwaiSessionVault(req('POST',{account:'lucasrosalem',ciphertext,sha256}),e,ok);
  const [key,raw]=[...e.store.entries()][0];
  const row=JSON.parse(raw);row.ciphertext+='A';e.store.set(key,JSON.stringify(row));
  assert.equal((await handleKwaiSessionVault(req(),e,ok)).status,409);
});
