import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const code=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
const confirm=code.slice(code.indexOf('async function kwaiPhysicalSourceFrameConfirm('),
                         code.indexOf('async function kwaiUnprovenAction('));
test('both physical account confirm paths accept verified source frames',()=>{
 assert.equal(code.split("return kwaiPhysicalSourceFrameConfirm(KWAI_TARGET,owner,b,proof,remote);").length-1,2);
 assert.match(code,/kwai_public_profile_source_frame_proof_v1/);
});
test('strict account, SHA, source URL, caption and 4 valid frame guards',()=>{
 for(const piece of ['proof.expected_account!==account','proof.actual_author_handle!==account',
 'proof.source_media_sha256!==proof.media_sha256','proof.source_video_url',
 'scores.length!==4','v<240','proof.caption_optional!==true',
 'proof.media_match.qualifying_distinct_frames!==4','proof.public_url!==publicUrl'])
  assert.ok(confirm.includes(piece),piece);
});
test('canonical exact video URL, started lease generation and unique remote post required',()=>{
 for(const piece of ["p.status='started'","p.lease_owner=$3","p.lease_generation=$4",
 "p.payload->>'video_url'=$7","p.remote_id IS NULL","d.status='confirmed' AND d.remote_id=$5"])
  assert.ok(confirm.includes(piece),piece);
});
test('publication clock must match verified public video and no auto retry',()=>{
 assert.match(confirm,/publication_started_at-to_timestamp\(\$8\/1000\.0\)/);
 assert.match(confirm,/now-evidenceTime>24\*3600000/);
 assert.doesNotMatch(confirm,/status='queued'/);
});
