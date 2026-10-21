import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';
import vm from 'node:vm';

const dir=dirname(fileURLToPath(import.meta.url));
const code=readFileSync(resolve(dir,'../infra/neon-cortes-queue/index.mjs'),'utf8');
const start=code.indexOf('async function bufferAction(');
const end=code.indexOf('\nexport default ', start);
assert.ok(start>=0 && end>start,'bufferAction must be extractable');
const fn=code.slice(start,end)+'\nthis.callBuffer=bufferAction;';

function harness(){
  const statements=[];
  const context={
    target:()=> 'linkedin:primary',
    query:async(sql,params=[])=>{
      statements.push({sql,params});
      return [{id:'job1',status:'confirmed',remote_id:'post1'}];
    },
    Object,Number,String,Set,JSON,URL
  };
  vm.runInNewContext(fn,context,{timeout:1000});
  return {call:context.callBuffer,statements};
}

test('OIDC-reconcile succeeds with no stale lease owner or lease_generation',async()=>{
  const h=harness();
  const result=await h.call('reconcile',{
    id:'job1',remote_id:'post1',
    external_link:'https://www.linkedin.com/feed/update/urn:li:ugcPost:123'
  },'linkedin');
  assert.equal(result.ok,true);
  assert.equal(h.statements.length,1);
  assert.match(h.statements[0].sql,/status='uncertain'/);
  assert.match(h.statements[0].sql,/confirmation_evidence->>'kind'='buffer_scheduled'/);
  assert.deepEqual(Array.from(h.statements[0].params).slice(0,3),
                   ['job1','linkedin:primary','post1']);
});

test('lease-bound actions still reject missing owner and generation',async()=>{
  const h=harness();
  const result=await h.call('start',{id:'job1'},'linkedin');
  assert.equal(result.ok,false);
  assert.equal(result.error,'INVALID_FENCE');
  assert.equal(h.statements.length,0);
});

test('reconcile cannot confirm a wrong social host',async()=>{
  const h=harness();
  const result=await h.call('reconcile',{
    id:'job1',remote_id:'post1',
    external_link:'https://evil.example/feed/update/urn:li:ugcPost:123'
  },'linkedin');
  assert.equal(result.ok,false);
  assert.equal(result.error,'INVALID_PUBLIC_URL');
  assert.equal(h.statements.length,0);
});

test('reconcile requires a publication identifier',async()=>{
  const h=harness();
  const result=await h.call('reconcile',{
    remote_id:'post1',
    external_link:'https://www.linkedin.com/feed/update/urn:li:ugcPost:123'
  },'linkedin');
  assert.equal(result.ok,false);
  assert.equal(result.error,'INVALID_ID');
  assert.equal(h.statements.length,0);
});
