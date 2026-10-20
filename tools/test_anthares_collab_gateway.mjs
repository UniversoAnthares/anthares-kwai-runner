import assert from 'node:assert/strict';
import test from 'node:test';
import {OWNER_ID,REPO,PREFIX,SCHEMA,MARKER,requestId,validateEvent,findRun,dispatch,verifyDelegation} from './anthares_collab_gateway.mjs';
const example={action:'opened',repository:{full_name:REPO},sender:{id:OWNER_ID},
  issue:{id:380000001,number:222,title:PREFIX+'Plano de verificação',user:{id:OWNER_ID},
    body:JSON.stringify({schema:SCHEMA,origin:'chatgpt',task:'Planejar duas verificações estáticas seguras.'})}};
function v(x){return JSON.parse(JSON.stringify(x))}
test('Valid user-created issue returns stable UUID for Claude Code status/result',()=>{
  const a=validateEvent(example),b=validateEvent(example);
  assert.equal(a.request_id,b.request_id);
  assert.match(a.request_id,/^[a-f0-9]{8}-[a-f0-9]{4}-5[a-f0-9]{3}-a[a-f0-9]{3}-[a-f0-9]{12}$/);
  assert.equal(requestId(example.issue.id),a.request_id);
  assert.equal(a.mode,'plan');
});
for(const [name,patch] of [
  ['non owner issue',x=>x.issue.user.id=55],
  ['non owner event',x=>x.sender.id=55],
  ['unexpected action',x=>x.action='edited'],
  ['unexpected repository',x=>x.repository.full_name='other/repo'],
  ['ordinary issue',x=>x.issue.title='Help with Anthares'],
  ['pull request disguised as issue',x=>x.issue.pull_request={}],
  ['invalid JSON',x=>x.issue.body='{'],
  ['unsupported schema',x=>x.issue.body=JSON.stringify({schema:'v2',origin:'chatgpt',task:'A useful task'})],
  ['extra workflow injection',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'chatgpt',task:'A useful task',mode:'edit'})],
  ['unknown issuer',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'external',task:'A useful task'})],
  ['empty task',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'work',task:' '})],
  ['overlong task',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'work',task:'A'.repeat(1601)})],
  ['obvious token',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'claude',task:'Here is github_pat_FAKE_SUPERSECRET'})],
  ['newline controls',x=>x.issue.body=JSON.stringify({schema:SCHEMA,origin:'work',task:'Try this\nThen this'})]
])test('reject '+name,()=>{const x=v(example);patch(x);assert.throws(()=>validateEvent(x))});
test('accept all three source labels without granting source-based privilege',()=>{
  for(const origin of ['claude','work','chatgpt']){
    const x=v(example);x.issue.body=JSON.stringify({schema:SCHEMA,origin,task:'Prepare a bounded static validation plan'});
    assert.equal(validateEvent(x).origin,origin);
  }
});
test('idempotent claim means no second dispatch',async()=>{
  const id=validateEvent(example).request_id;
  let calls=0;const r=await dispatch(example,{
    getComments:async()=>[{body:'['+MARKER+' '+id+'] CLAIMED'}],
    post:async()=>{throw Error('should not post')},
    get:async()=>{calls++}
  });
  assert.equal(r.already_claimed,true);assert.equal(calls,0);
});
test('new issue creates claim BEFORE authenticated one-time dispatch',async()=>{
  const steps=[];
  const result=await dispatch(example,{
    getComments:async()=>[],
    post:async(_,message)=>{steps.push(['post',message]);return {id:1}},
    get:async(method,path,body)=>{steps.push(['api',path,body]);return null}
  });
  assert.equal(result.accepted,true);
  assert.equal(steps[0][0],'post');
  assert.match(steps[0][1],/CLAIMED/);
  assert.equal(steps[1][0],'api');
  assert.equal(steps[1][2].ref,'main');
  assert.equal(steps[1][2].inputs.mode,'plan');
  assert.equal(steps[1][2].inputs.request_id,result.request_id);
  assert.equal(steps[1][2].inputs.origin_issue,'222');
  assert.equal(steps.length,3);
});
test('failure after claim is marked uncertain and never retried automatically',async()=>{
  let claim=0,uncertain=0;
  await assert.rejects(()=>dispatch(example,{
    getComments:async()=>[],post:async(n,s)=>{if(s.includes('CLAIMED'))claim++;if(s.includes('DISPATCH_UNCERTAIN'))uncertain++;},
    get:async()=>{throw Error('github_http_403_POST')}
  }),/github_http_403_POST/);
  assert.equal(claim,1);assert.equal(uncertain,1);
});
test('findRun correlates only exact main workflow_dispatch title and rejects ambiguity',()=>{
  const id=validateEvent(example).request_id;
  const row={event:'workflow_dispatch',head_branch:'main',display_title:'Anthares Claude Code '+id,id:135,status:'completed',conclusion:'success'};
  assert.equal(findRun({workflow_runs:[{...row,head_branch:'test'},row,{...row,event:'push'}]},id)?.id,135);
  assert.equal(findRun({workflow_runs:[]},id),null);
  assert.throws(()=>findRun({workflow_runs:[row,row]},id),/ambiguous/);
});

test('GitHub bot delegation must verify owner-created issue, task, mode and exact UUID',async()=>{
 const original={...process.env};
 const id=validateEvent(example).request_id;
 try{
  process.env.ANTHARES_COLLAB_ORIGIN_ISSUE='222';
  process.env.ANTHARES_TASK_MODE='plan';
  process.env.ANTHARES_TASK_SCOPE='';
  process.env.ANTHARES_TASK_PROMPT=validateEvent(example).task;
  process.env.ANTHARES_REQUEST_ID=id;
  const ok=await verifyDelegation({loadIssue:async()=>example.issue});
  assert.equal(ok.request_id,id);
  process.env.ANTHARES_REQUEST_ID='00000000-0000-4000-a000-000000000000';
  await assert.rejects(verifyDelegation({loadIssue:async()=>example.issue}),/origin_request_id_mismatch/);
  process.env.ANTHARES_REQUEST_ID=id;
  process.env.ANTHARES_TASK_MODE='edit';
  await assert.rejects(verifyDelegation({loadIssue:async()=>example.issue}),/invalid_delegated_mode/);
  process.env.ANTHARES_TASK_MODE='plan';
  process.env.ANTHARES_TASK_PROMPT='a different injected prompt';
  await assert.rejects(verifyDelegation({loadIssue:async()=>example.issue}),/origin_task_mismatch/);
  process.env.ANTHARES_TASK_PROMPT=validateEvent(example).task;
  await assert.rejects(verifyDelegation({loadIssue:async()=>({...example.issue,user:{id:1}})}),/unauthorized_issuer/);
 }finally{process.env=original}
});
