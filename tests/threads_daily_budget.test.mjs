import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const src=fs.readFileSync('tools/cortes_threads_local_publisher.mjs','utf8');
test('daily cap counts confirmed and uncertain posts before submitting',()=>{
 assert.match(src,/const publishedToday=/);
 assert.match(src,/const uncertainToday=/);
 assert.match(src,/publishedToday\s*\+\s*uncertainToday\s*>=\s*maxPerDay/);
 assert.match(src,/const maxPerDay=100/);
});
test('uncertain posts must never be selected for blind automatic retry',()=>{
 assert.match(src,/shouldAttemptPreSubmit\(state\)/);
 assert.match(fs.readFileSync('tools/threads_queue_policy.mjs','utf8'),/state\.status!=='failed_pre_submit'/);
});