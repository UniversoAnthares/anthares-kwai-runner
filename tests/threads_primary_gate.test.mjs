import test from 'node:test';
import assert from 'node:assert/strict';
import {decide} from '../tools/threads_primary_gate.mjs';
const now=Date.parse('2026-10-21T14:00:00Z');
test('local continues when no verified cloud primary exists',()=>assert.equal(decide(null,now).allow,true));
test('a GitHub Actions success alone has no authority to stop local',()=>assert.equal(decide({enabled:false,workflow_success:true},now).allow,true));
test('unverified cloud activation blocks unsafe dual publish',()=>assert.equal(decide({enabled:true},now).allow,false));
test('expired acknowledgement blocks until Neon reconciliation',()=>assert.equal(decide({enabled:true,lease_authority:'neon',verified_identity:'universoanthares',last_remote_post_url:'https://www.threads.com/@universoanthares/post/a',verified_at:'2026-10-21T12:00:00Z'},now).allow,false));
test('validated recent cloud activation blocks the local publisher',()=>assert.equal(decide({enabled:true,lease_authority:'neon',verified_identity:'universoanthares',last_remote_post_url:'https://www.threads.com/@universoanthares/post/a',verified_at:'2026-10-21T13:55:00Z'},now).allow,false));