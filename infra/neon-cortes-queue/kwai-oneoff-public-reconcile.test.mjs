import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateOneoffKwaiPublicProof,ONEOFF_WORKFLOW,ONEOFF_RECONCILED_KIND} from './kwai-oneoff-public-reconcile.mjs';
const evidence=JSON.parse(readFileSync(new URL('../../test-hub/findings/20261113-kwai-three-public-matches.json',import.meta.url),'utf8'));
const data=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
const body=p=>({id:p.id,target_key:'kwai:'+p.account,expected_account:p.account,result:p});
test('three actual six-frame video proofs validate against exact immutable allowlist',()=>{
 assert.equal(evidence.results.length,3);
 assert.equal(evidence.queue_mutations,0);assert.equal(evidence.posts_submitted,0);
 for(const r of evidence.results){
   const p=validateOneoffKwaiPublicProof(body(r));
   assert.ok(p,r.id);assert.equal(p.id,r.id);
   assert.equal(p.publicUrl,r.public_url);
   assert.equal(p.scores.length,6);
   assert.ok(p.scores.every(x=>x>=240));
 }
});
test('forged account, URLs, timestamps, duplicate posts and content hashes are rejected',()=>{
 const base=body(evidence.results[0]);
 const mutate=(path,value)=>{const b=structuredClone(base);path(b,value);return b;};
 for(const [mut,val] of [
   [(b,v)=>b.result.public_media_sha256=v,'0'.repeat(64)],
   [(b,v)=>b.result.observed_source_file_sha256=v,'0'.repeat(64)],
   [(b,v)=>b.result.photo_id=v,'5000000000000000000'],
   [(b,v)=>b.result.posted_ms=v,base.result.posted_ms+1000],
   [(b,v)=>b.result.started_ms=v,base.result.started_ms+1000],
   [(b,v)=>b.result.source_sha256=v,'1'.repeat(64)],
   [(b,v)=>b.result.proof.best_source_frame_inliers=v,[100,100,100,100,100,100]],
   [(b,v)=>b.result.proof.media_matched=v,false],
   [(b,v)=>b.result.status=v,'UNVERIFIED'],
   [(b,v)=>b.result.account=v,'universoanthares'],
   [(b,v)=>b.expected_account=v,'universoanthares'],
   [(b,v)=>b.id=v,'another'],
   [(b,v)=>b.result.observed_source_file_bytes=v,12]
 ])assert.equal(validateOneoffKwaiPublicProof(mutate(mut,val)),null);
});
test('one-off OIDC writer was revoked after all three real video confirmations',()=>{
 assert.equal(ONEOFF_WORKFLOW,'kwai-three-verified-reconcile.yml');
 assert.equal(ONEOFF_RECONCILED_KIND,'kwai_three_public_sift_oidc_reconciled_v1');
 assert.doesNotMatch(data,/else if\(wf===ONEOFF_WORKFLOW\)\{role='kwai-oneoff-reconciler';platform='kwai';\}/);
 assert.doesNotMatch(data,/if\(action==='kwai-oneoff-confirm-public'\)/);
 const workflow=readFileSync(new URL('../../.github/workflows/kwai-three-verified-reconcile.yml',import.meta.url),'utf8');
 assert.match(workflow,/GITHUB_OIDC_TOKEN_ACCESS=DISABLED/);
 assert.doesNotMatch(workflow,/id-token:\s*write/);
 assert.doesNotMatch(workflow,/schedule:\s*|cron:\s*/);
 assert.doesNotMatch(workflow,/^  push:/m);
 assert.match(data,/ONEOFF_CANCEL_PROOF_MISMATCH/);
 assert.match(data,/ONEOFF_STARTED_OWNER_MISMATCH/);
 assert.match(data,/ONEOFF_ATOMIC_RECONCILE_CONFLICT/);
});
test('CAS binds source identity, generation, status, original start, expired lease and unique remote',()=>{
 const start=data.indexOf('async function kwaiOneoffPublicReconcile(');
 const end=data.indexOf('async function kwaiSyncReconciledWordpress(',start);
 assert.ok(start>0&&end>start);
 const code=data.slice(start,end);
 for(const term of ['p.id=$1','p.target_key=$2','p.media_sha256=$3','p.status=$6',
  'p.remote_id IS NULL','p.lease_generation=$7',"p.payload->>'video_url'=$9",
  'p.publication_started_at-to_timestamp($8/1000.0)',
  'p.lease_until IS NULL OR p.lease_until<now()',
  'p.lease_owner IS NULL OR p.lease_owner=',
  'd.status=\'confirmed\' AND d.remote_id=$4','public_post_timestamp_ms:p.posted',
  'source_best_inliers:p.scores'])assert.ok(code.includes(term),term);
 assert.equal(code.includes("status='queued'"),false);
});
