import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateClaudeTask,validateRequestId,findRun,zipResult,claudeCodeTools,
  startClaudeCode,getClaudeCodeStatus,getClaudeCodeResult
} from './claude-code-bridge.mjs';
import {githubTools} from './github-bridge.mjs';
const ID='fab01234-1234-4abc-8abc-1234567890ab';
const auth={ANTHARES_GITHUB_TOKEN:'unit-only-nonprod-token'};
function json(value,status=200){return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}})}
function run(status='completed',conclusion='success'){return {
 id:445566,head_branch:'main',event:'workflow_dispatch',
 display_title:'Anthares Claude Code '+ID,html_url:'https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/445566',status,conclusion
}}
function buildZipStore(name,text){
  const n=Buffer.from(name),d=Buffer.from(text),a=Buffer.alloc(30+n.length+d.length),b=Buffer.alloc(46+n.length),end=Buffer.alloc(22);
  a.writeUInt32LE(0x04034b50,0);a.writeUInt16LE(20,4);a.writeUInt16LE(0,8);
  a.writeUInt32LE(d.length,18);a.writeUInt32LE(d.length,22);a.writeUInt16LE(n.length,26);
  n.copy(a,30);d.copy(a,30+n.length);
  b.writeUInt32LE(0x02014b50,0);b.writeUInt16LE(20,4);b.writeUInt16LE(20,6);
  b.writeUInt16LE(0,10);b.writeUInt32LE(d.length,20);b.writeUInt32LE(d.length,24);
  b.writeUInt16LE(n.length,28);b.writeUInt32LE(0,42);n.copy(b,46);
  end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(1,8);end.writeUInt16LE(1,10);
  end.writeUInt32LE(b.length,12);end.writeUInt32LE(a.length,16);
  return Buffer.concat([a,b,end]);
}
function withFetch(fn,runTest){const previous=globalThis.fetch;globalThis.fetch=fn;return Promise.resolve().then(runTest).finally(()=>globalThis.fetch=previous)}
test('exposed MCP tool names and OAuth write/read scopes',()=>{
 for(const [name,scope] of [['run_claude_code','github.write'],['get_claude_code_status','github.read'],['get_claude_code_result','github.read']]){
  assert.equal(claudeCodeTools.find(t=>t.name===name).scope,scope);
  assert.equal(githubTools.find(t=>t.name===name).scope,scope);
 }
});
test('only plans and one restricted file are accepted',()=>{
 assert.deepEqual(validateClaudeTask({mode:'plan',task:' analyze '}),{mode:'plan',task:'analyze',scope:''});
 assert.equal(validateClaudeTask({mode:'edit',task:'x',scope:'docs/proof.md'}).scope,'docs/proof.md');
 for(const path of ['.github/workflows/publish.yml','docs/../.env','tools/node_modules/file.js','test-hub/README.md','docs/secrets/a','docs/hello\\x','docs/a/./b','docs/a/../b','docs/.env'])assert.throws(()=>validateClaudeTask({mode:'edit',task:'x',scope:path}));
 assert.throws(()=>validateClaudeTask({mode:'edit',task:'x'}));
 assert.throws(()=>validateClaudeTask({mode:'plan',task:'x',scope:'docs/p.md'}));
 assert.throws(()=>validateClaudeTask({mode:'plan',task:'x',token:'surprise'}));
 assert.throws(()=>validateClaudeTask({mode:'plan',task:'x'.repeat(5501)}));
 assert.throws(()=>validateClaudeTask({mode:'plan',task:'hi\x00'}));
});
test('correlation ID is exact, run title and source branch are fenced',()=>{
 assert.equal(validateRequestId({request_id:ID}),ID);
 for(const id of ['x','',123,'1'.repeat(35),ID+'X'])assert.throws(()=>validateRequestId({request_id:id}));
 assert.deepEqual(findRun({workflow_runs:[run()]},ID),run());
 assert.equal(findRun({workflow_runs:[{...run(),head_branch:'foo'}]},ID),null);
 assert.equal(findRun({workflow_runs:[{...run(),display_title:'Other: '+ID}]},ID),null);
 assert.throws(()=>findRun({workflow_runs:[run(),run()]},ID));
});
test('dispatch calls only fixed GitHub workflow with owner secret and UUID, no user-selected repo',async()=>{
 const seen=[];
 await withFetch(async (url,init)=>{seen.push({url,init});return seen.length===1?json({workflow_runs:[]}):new Response(null,{status:204})},async()=>{
   const v=await startClaudeCode(auth,{mode:'plan',task:'Read and plan'});
   assert.equal(v.accepted,true);assert.match(v.request_id,/^[0-9a-f-]{36}$/);
   assert.equal(seen.length,2);
   assert.match(seen[0].url,/actions\/workflows\/anthares-free-claude\.yml\/runs/);
   assert.match(seen[1].url,/actions\/workflows\/anthares-free-claude\.yml\/dispatches$/);
   assert.equal(seen[1].init.method,'POST');
   const payload=JSON.parse(seen[1].init.body);
   assert.equal(payload.ref,'main');assert.equal(payload.inputs.request_id,v.request_id);
   assert.equal(payload.inputs.mode,'plan');assert.equal(payload.inputs.scope,'');
   assert.equal(seen[1].init.headers.Authorization,'Bearer unit-only-nonprod-token');
 });
});
test('busy workflow blocks parallel dispatch without mutating any queue',async()=>{
 await withFetch(async()=>json({workflow_runs:[run('in_progress',null)]}),async()=>{
   await assert.rejects(()=>startClaudeCode(auth,{mode:'edit',task:'x',scope:'docs/a.md'}),/remote_claude_code_busy/);
 });
});
test('status reports pending and completed using authenticated GitHub metadata',async()=>{
 await withFetch(async()=>json({workflow_runs:[run()]}),async()=>{
   const s=await getClaudeCodeStatus(auth,{request_id:ID});
   assert.equal(s.run_id,445566);assert.equal(s.conclusion,'success');
 });
 await withFetch(async()=>json({workflow_runs:[]}),async()=>{
   const s=await getClaudeCodeStatus(auth,{request_id:ID});
   assert.equal(s.status,'not_visible_yet');
 });
});
test('GitHub artifact ZIP STORE text extraction is safe and bounded',()=>{
 const data=buildZipStore('anthares-claude-result.txt','Plano real OK.');
 assert.equal(zipResult(data),'Plano real OK.');
 assert.throws(()=>zipResult(buildZipStore('../bad.txt','x')),/artifact_result_missing/);
 const corrupt=Buffer.from(data);corrupt[8]=8;corrupt[data.length-22-46-'anthares-claude-result.txt'.length+10]=8;
 assert.throws(()=>zipResult(corrupt));
});
test('result retrieval never forwards GitHub credential to external signed blob host',async()=>{
 const calls=[];
 await withFetch(async(url,init={})=>{
  calls.push({url,init});
  if(calls.length===1)return json({workflow_runs:[run()]});
  if(calls.length===2)return json({artifacts:[{id:455,name:'anthares-free-claude-result-445566',expired:false}]});
  if(calls.length===3)return new Response(null,{status:302,headers:{Location:'https://test.blob.core.windows.net/verified-object?sig=local'}});
  if(calls.length===4)return new Response(buildZipStore('anthares-claude-result.txt','Plano de dois passos validado.'));
  throw Error('unexpected_network_request');
 },async()=>{
  const r=await getClaudeCodeResult(auth,{request_id:ID});
  assert.equal(r.ready,true);assert.equal(r.result,'Plano de dois passos validado.');
  assert.equal(calls.length,4);
  assert.equal(calls[2].init.headers.Authorization,'Bearer unit-only-nonprod-token');
  assert.equal(calls[3].init.headers,undefined);
 });
});
test('result does not pretend completion when workflow failed',async()=>{
 await withFetch(async()=>json({workflow_runs:[run('completed','failure')]}),async()=>{
  const r=await getClaudeCodeResult(auth,{request_id:ID});
  assert.equal(r.ready,false);assert.equal(r.reason,'workflow_not_successful');
 });
});
test('rejects external artifact downloads to unexpected origins',async()=>{
 let count=0;
 await withFetch(async(url)=>{
  count++;
  if(count===1)return json({workflow_runs:[run()]});
  if(count===2)return json({artifacts:[{id:455,name:'anthares-free-claude-result-445566',expired:false}]});
  if(count===3)return new Response(null,{status:302,headers:{Location:'https://malicious.invalid/collect'}});
  throw Error('credential_leak_risk');
 },async()=>await assert.rejects(()=>getClaudeCodeResult(auth,{request_id:ID}),/artifact_untrusted_redirect/));
 assert.equal(count,3);
});
