import test from 'node:test';
import assert from 'node:assert/strict';
import {collabIssueTools,callCollabIssueTool} from './collab-issue-bridge.mjs';
const repo='UniversoAnthares/anthares-kwai-runner';
const good={number:222,id:380000001,user:{id:81930373},state:'open',title:'[ANTHARES-COLLAB-PLAN] Canary',
  html_url:'https://github.com/'+repo+'/issues/222',body:JSON.stringify({
    schema:'anthares.collab.plan.v1',origin:'work',task:'Prepare um plano seguro e sem publicacao'
  })};
async function withMock(fn,issues=[good],comments=[{body:'[ANTHARES-COLLAB] DISPATCH_ACCEPTED id=test',user:{type:'Bot'}}]){
  const orig=globalThis.fetch;
  globalThis.fetch=async(input,opts)=>{
    assert.equal(opts.method,'GET'); assert(!opts.headers.Authorization);
    const pathname=new URL(input).pathname;
    const data=pathname.endsWith('/comments')?comments:pathname.endsWith('/issues')?issues:good;
    return {ok:true,json:async()=>data};
  };
  try{return await fn()}finally{globalThis.fetch=orig}
}
test('only read-only GitHub-scoped collaboration tools',()=>{
 assert.deepEqual(collabIssueTools.map(x=>x.name).sort(),['collab_list_tasks','collab_get_task'].sort());
 assert(collabIssueTools.every(x=>x.scope==='github.read'));
});
test('only pinned owner issues, never pull requests or another user',async()=>{
 await withMock(async()=>{
  const a=await callCollabIssueTool({},'collab_list_tasks',{repo});
  assert.equal(a.tasks.length,1);assert.equal(a.tasks[0].origin,'work');
 },[{...good}, {...good,number:225,user:{id:123}}, {...good,number:226,pull_request:{url:'x'}}]);
});
test('get includes only actor/bot collaboration markers',async()=>{
 await withMock(async()=>{
 const a=await callCollabIssueTool({},'collab_get_task',{repo,issue_number:222});
 assert.equal(a.task.events.length,1);assert.equal(a.task.issue_number,222);
 assert.equal(a.task.origin,'work');
 });
});
test('reject invalid repository or issue numbers',async()=>{
 for(const v of [0,1.5,-1,Number.MAX_SAFE_INTEGER]){
  await assert.rejects(callCollabIssueTool({},'collab_get_task',{repo,issue_number:v}));
 }
 await assert.rejects(callCollabIssueTool({},'collab_list_tasks',{repo:'other/repo'}));
});
test('reject nonowner issue even by exact number',async()=>{
 await withMock(async()=>assert.rejects(callCollabIssueTool({},'collab_get_task',{repo,issue_number:222})),[],
 []);
});
test('bad schema denied and HTTP error propagates',async()=>{
 await withMock(async()=>assert.rejects(callCollabIssueTool({},'collab_get_task',{repo,issue_number:222})),[{...good,body:'{'}]);
});
