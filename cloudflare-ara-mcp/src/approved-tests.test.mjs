import test from 'node:test';
import assert from 'node:assert/strict';
import {approvedTestCommand,runApprovedTests} from './approved-tests.mjs';
const sha='a'.repeat(40),env={ARA_TEST_SOURCE_SHA:sha},args={suite:'mcp-regression',request_id:'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'};
test('approved regression rejects arbitrary command, source injection and unknown suites',async()=>{
 for(const a of [{...args,command:'whoami'},{...args,suite:'shell'},{...args,request_id:'bad'}])await assert.rejects(runApprovedTests(env,a,()=>{throw Error('must not execute')},async()=>true));
 assert.throws(()=>approvedTestCommand("a';whoami"));
 assert.match(approvedTestCommand(sha),/git -c safe.directory/);
 assert.match(approvedTestCommand(sha),/archive --format=zip/);
});
test('approved regression uses exact source, replay gate and safe summarized results',async()=>{
 let calls=0;
 const execute=async(type,a,timeout)=>{calls++;assert.equal(type,'shell');assert.equal(timeout,90);assert(a.command.includes(sha));return {ok:true,job_id:'job-proof',output:JSON.stringify({exit_code:0,stdout:JSON.stringify({ok:true,suite:'mcp-regression',tested_source_sha:sha,passed:25,failed:0,capabilities_passed:true})})}};
 const r=await runApprovedTests(env,args,execute,async()=>true);assert.equal(r.ok,true);assert.equal(r.tested_source_sha,sha);assert.equal(r.passed,25);
 await assert.rejects(runApprovedTests(env,args,execute,async()=>false),/replayed/);assert.equal(calls,1);
 await assert.rejects(runApprovedTests(env,args,async()=>({output:'secret raw failure'}),async()=>true),/invalid_response/);
});
