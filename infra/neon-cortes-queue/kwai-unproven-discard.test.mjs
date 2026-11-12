import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const src=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
const part=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a)));

test('only RSA-attested physical Android publisher can discard or confirm',()=>{
 const s=part('async function kwaiUnprovenAction','async function kwaiSecondaryAction');
 assert.match(s,/actor\.role!==['"]kwai-physical['"]/);
 assert.match(s,/actor\.workflow!==['"]physical:DESKTOP-FTDK0HP['"]/);
 assert.match(s,/KWAI_UNPROVEN_ACCOUNT_MISMATCH/);
});
test('both Kwai accounts expose the same guarded unproven action',()=>{
 assert.equal(src.split("if(action==='kwai-unproven')return kwaiUnprovenAction").length-1,2);
 assert.match(src,/mode==='list'/);
 assert.match(src,/mode==='confirm'/);
 assert.match(src,/mode!=='discard'/);
});
test('terminal discard requires age, expiry and no remote id',()=>{
 const s=part('async function kwaiUnprovenAction','async function kwaiSecondaryAction');
 assert.match(s,/publication_started_at<now\(\)-interval '45 minutes'/);
 assert.match(s,/publication_started_at<now\(\)-interval '90 minutes'/);
 assert.match(s,/lease_until<now\(\)-interval '30 minutes'/);
 assert.match(s,/p\.remote_id IS NULL/);
 assert.match(s,/no_retry',true/);
 assert.match(s,/possible_publication',true/);
 assert.match(s,/status='cancelled'/);
 assert.doesNotMatch(s,/status='queued'/);
});
test('confirmation requires exact media and account proof, with idempotent URL',()=>{
 const s=part('async function kwaiUnprovenAction','async function kwaiSecondaryAction');
 assert.match(s,/kwai_logged_source_to_public_four_frame_v1/);
 assert.match(s,/frameScores\.length!==4/);
 assert.match(s,/source_url!==proof\.source_url/);
 assert.match(s,/KWAI_UNPROVEN_TIME_MISMATCH/);
 assert.match(s,/d\.status='confirmed' AND d\.remote_id=\$3/);
 assert.match(s,/p\.status IN \('uncertain','started'\)/);
});
