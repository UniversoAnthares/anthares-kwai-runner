import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac, timingSafeEqual } from 'node:crypto';
import { readFileSync } from 'node:fs';

const src=readFileSync('infra/neon-cortes-queue/index.mjs','utf8');
const start=src.indexOf("const KWAI_TARGET='kwai:lucasrosalem';");
const end=src.indexOf('async function enqueue(b){',start);
assert.ok(start>=0 && end>start,'isolated Kwai contract must exist');
const block=src.slice(start,end);

function load({secret='',rows=[]}={}){
 const calls=[];
 const query=async(sql,args)=>{calls.push({sql,args});return rows;};
 const crypto={createHmac,timingSafeEqual};
 const process={env:{CORTES_KWAI_CLOUD_PUBLISH_ENABLED:'1',
    CORTES_KWAI_INDEPENDENT_ATTESTATION_KEY:secret}};
 const fn=new Function('query','process','crypto','Buffer',block+';return kwaiAction');
 return {run:fn(query,process,crypto,Buffer),calls};
}
function sample(){
 const id='synthetic-kwai-attestation',gen=3,remote='123456789';
 const media='a'.repeat(64);
 const proof={public_url:'https://www.kwai.com/@lucasrosalem/photo/'+remote,
  kind:'kwai_account_media_readback_verified',
  method:'physical_profile_exact_account_timestamp_and_share_ui',
  verifier_id:'kwai-independent-account-readback-v1',
  account:'lucasrosalem',remote_id:remote,media_sha256:media,
  verified_at:new Date().toISOString()};
 const body={id,lease_generation:gen,target_key:'kwai:lucasrosalem',
  expected_account:'lucasrosalem',remote_id:remote,confirmation_evidence:proof};
 const actor={role:'kwai-publisher',workflow:'cortes-kwai-cloud-publisher.yml'};
 return{body,actor};
}
function sign(body,key){
 const p=body.confirmation_evidence;
 const data=JSON.stringify(['kwai-readback-v1',body.id,body.lease_generation,
  'kwai:lucasrosalem',p.account,body.remote_id,p.public_url,
  p.method,p.media_sha256,p.verified_at]);
 p.attestation_hmac=createHmac('sha256',key).update(data).digest('hex');
}

test('generic proof role cannot read private Kwai reconciliation records',async()=>{
 const ctx=load();
 const res=await ctx.run('kwai-uncertain-read',{},
  {role:'probe',workflow:'cortes-neon-ha-oidc-proof.yml'});
 assert.equal(res.error,'KWAI_READ_DENIED');
 assert.equal(ctx.calls.length,0);
});
test('publisher self-asserted URL, method and account never confirm without key',async()=>{
 const ctx=load(),{body,actor}=sample();
 const res=await ctx.run('kwai-confirm',body,actor);
 assert.equal(res.error,'KWAI_INDEPENDENT_ATTESTATION_REQUIRED');
 assert.equal(ctx.calls.length,0);
});
test('independent verifier must provide valid HMAC',async()=>{
 const key='synthetic-test-secret-ONLY-not-real-123456789';
 const ctx=load({secret:key}),{body,actor}=sample();
 body.confirmation_evidence.attestation_hmac='0'.repeat(64);
 const res=await ctx.run('kwai-confirm',body,actor);
 assert.equal(res.error,'KWAI_INDEPENDENT_ATTESTATION_INVALID');
 assert.equal(ctx.calls.length,0);
});
test('stale attestations and wrong fencing generations are rejected',async()=>{
 const key='synthetic-test-secret-ONLY-not-real-123456789';
 const ctx=load({secret:key}),{body,actor}=sample();
 body.confirmation_evidence.verified_at=new Date(Date.now()-700000).toISOString();
 sign(body,key);
 assert.equal((await ctx.run('kwai-confirm',body,actor)).error,'KWAI_INDEPENDENT_ATTESTATION_REQUIRED');
 body.confirmation_evidence.verified_at=new Date().toISOString();
 sign(body,key);
 body.lease_generation=4;
 assert.equal((await ctx.run('kwai-confirm',body,actor)).error,'KWAI_INDEPENDENT_ATTESTATION_INVALID');
 assert.equal(ctx.calls.length,0);
});
test('valid synthetic attestation proceeds only to fenced SQL and omits HMAC from evidence',async()=>{
 const key='synthetic-test-secret-ONLY-not-real-123456789';
 const ctx=load({secret:key}),{body,actor}=sample();
 sign(body,key);
 const res=await ctx.run('kwai-confirm',body,actor);
 assert.equal(res.error,'KWAI_STALE_FENCE_OR_MEDIA');
 assert.equal(ctx.calls.length,1);
 assert.match(ctx.calls[0].sql,/lease_generation=\$4/);
 assert.match(ctx.calls[0].sql,/status='started'/);
 assert.match(ctx.calls[0].sql,/media_sha256=\$7/);
 const evidence=JSON.parse(ctx.calls[0].args[5]);
 assert.equal(evidence.attestation_hmac,undefined);
 assert.equal(evidence.attestation_scheme,'hmac-sha256');
});
