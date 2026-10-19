import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateRepo, validateBranch, validatePath, validateSha,
  callGithubTool, githubTools
} from './github-bridge.mjs';

const REPO = 'UniversoAnthares/anthares-kwai-runner';
const BRANCH = 'claude/ci-contract';
const HEAD = 'a'.repeat(40);
const FILE_SHA = 'b'.repeat(40);
const LEASE = 'test-hub/findings/lease-claude-github-ci.md';
const LEASE_CONTENT = [
  'STATUS: RUNNING','LEASE_OWNER: claude-free-mcp',
  'REPO: ' + REPO,'BRANCH: ' + BRANCH,
  'START_UTC: ' + new Date(Date.now()-60_000).toISOString(),
  'EXPIRES_UTC: ' + new Date(Date.now()+600_000).toISOString()
].join('\n');
const token = { ANTHARES_GITHUB_TOKEN: 'qa-fake-token-never-production' };
const common = { repo: REPO, branch: BRANCH, expected_head_sha: HEAD, lease_path: LEASE };

function response(body, status=200) {
  return {ok: status < 400, status, async json(){ return body; }};
}
function mockResponse(url, init={}) {
  const u = new URL(url);
  const path = u.pathname + u.search;
  if(path.includes('/contents/test-hub?'))
    return response([{name:'findings',type:'dir',sha:'f'.repeat(40)}]);
  if(path.includes('/git/trees/' + 'f'.repeat(40)))
    return response({truncated:false,tree:[{type:'blob',path:LEASE.split('/').at(-1)}]});
  if(path.includes('/contents/' + LEASE))
    return response({type:'file',content:Buffer.from(LEASE_CONTENT).toString('base64')});
  if(path.includes('/git/ref/heads/')) return response({object:{sha:HEAD}});
  if(path.includes('/contents/docs/unit.txt?ref='+'c'.repeat(40)))
    return response({type:'file',size:3,sha:'d'.repeat(40),content:Buffer.from('new').toString('base64')});
  if(path==='/graphql' && init.method==='POST'){
    const p=JSON.parse(init.body).variables.input;
    assert.equal(p.expectedHeadOid,HEAD);assert.equal(p.branch.branchName,BRANCH);assert.equal(p.branch.repositoryNameWithOwner,REPO);
    return response({data:{createCommitOnBranch:{commit:{oid:'c'.repeat(40)}}}});
  }
  if(path.includes('/contents/docs/unit.txt?'))
    return response({type:'file',size:8,sha:FILE_SHA,content:Buffer.from('old text').toString('base64')});
  if(path.includes('/contents/docs/unit.txt') && init.method==='PUT')
    return response({commit:{sha:'c'.repeat(40)},content:{sha:'d'.repeat(40)}});
  if(path.includes('/pulls?')) return response([]);
  if(path.endsWith('/pulls') && init.method==='POST')
    return response({number:17,html_url:'https://github.com/test/pr/17',draft:true,head:{sha:HEAD}});
  return response({message:'not found'},404);
}
async function withMock(task,responder=mockResponse) {
  const original = globalThis.fetch;
  globalThis.fetch = async (url, init) => responder(url, init);
  try{return await task();}finally{globalThis.fetch=original;}
}
test('approved repositories only', () => {
  for(const name of ['anthares-kwai-runner','anthares-clipper','anthares-wordpress','home','anthares-transcricao'])
    assert.equal(validateRepo('UniversoAnthares/'+name),'UniversoAnthares/'+name);
  for(const name of ['other/repo','UniversoAnthares/anthares-kwai-session-vault','UniversoAnthares/unknown'])
    assert.throws(()=>validateRepo(name));
});
test('default branch, unsafe refs and path traversal denied', () => {
  for(const ref of ['main','master','claude/../main','claude/bad.lock','claude//oops','refs/heads/main'])
    assert.throws(()=>validateBranch(ref));
  assert.equal(validateBranch(BRANCH),BRANCH);
  for(const path of ['../a','src//x','.env','src/.env.prod','credentials.json','x%2fy',
    'test-hub/findings/lease.md','a\\b','/absolute','a/../../x'])
    assert.throws(()=>validatePath(path));
  assert.equal(validatePath('docs/unit.txt'),'docs/unit.txt');
});
test('commit SHAs must be exact',()=>{
  assert.equal(validateSha(HEAD),HEAD);
  for(const input of ['', 'abc', 'a'.repeat(39), 'z'.repeat(40)])
    assert.throws(()=>validateSha(input));
});
test('all exposed mutators are narrow, and no main writer is exposed',()=>{
  assert.deepEqual(githubTools.map(x=>x.name).sort(),
    ['github_begin_task','github_create_branch','github_draft_pr','github_get_file','github_put_file'].sort());
  assert.equal(githubTools.filter(x=>x.scope==='github.write').length,4);
});
test('public code file can be read without credential',async()=>{
  await withMock(async()=>{
    const result=await callGithubTool({},'github_get_file',{repo:REPO,path:'docs/unit.txt',ref:BRANCH});
    assert.equal(result.content,'old text');
    assert.equal(result.sha,FILE_SHA);
  });
});
test('file update requires correct SHA and a live matching Test Hub lease',async()=>{
  await withMock(async()=>{
    const result=await callGithubTool(token,'github_put_file',{
      ...common,path:'docs/unit.txt',content:'new',expected_file_sha:FILE_SHA,message:'unit change'
    });
    assert.equal(result.commit,'c'.repeat(40));
    await assert.rejects(callGithubTool(token,'github_put_file',{
      ...common,path:'docs/unit.txt',content:'new',expected_file_sha:'0'.repeat(40),message:'unit change'
    }),/stale_file_sha/);
  });
});
test('Claude only opens draft PRs, with matching task lease',async()=>{
  await withMock(async()=>{
    const r=await callGithubTool(token,'github_draft_pr',{
      ...common,title:'Claude fixes unit test'
    });
    assert.equal(r.draft,true);
    assert.equal(r.number,17);
  });
});
test('write denied with absent token and forbidden paths',async()=>{
  await withMock(async()=>{
    await assert.rejects(callGithubTool({},'github_put_file',{
      ...common,path:'docs/unit.txt',content:'x',expected_file_sha:FILE_SHA,message:'test'
    }),/github_server_credential_unconfigured/);
    await assert.rejects(callGithubTool(token,'github_put_file',{
      ...common,branch:'main',path:'docs/unit.txt',content:'x',message:'test'
    }),/invalid_claude_branch/);
    await assert.rejects(callGithubTool(token,'github_put_file',{
      ...common,path:'.env',content:'x',message:'test'
    }),/sensitive_path_denied/);
    await assert.rejects(callGithubTool(token,'github_put_file',{
      ...common,repo:'UniversoAnthares/anthares-wordpress',path:'docs/unit.txt',
      content:'x',message:'test'
    }),/lease_mismatch/);
  });
});

test('file reads bind returned content to an immutable branch HEAD',async()=>{
 await withMock(async()=>{
  const r=await callGithubTool({},'github_get_file',{repo:REPO,path:'docs/unit.txt',ref:BRANCH});
  assert.equal(r.head_sha,HEAD);
 },(url,init)=>{
  if(new URL(url).pathname.endsWith('/contents/docs/unit.txt'))assert.equal(new URL(url).searchParams.get('ref'),HEAD);
  return mockResponse(url,init);
 });
});
test('an atomic GitHub stale-head rejection cannot fall back to an unsafe Contents write',async()=>{
 let mutations=0;
 await withMock(async()=>{
  await assert.rejects(callGithubTool(token,'github_put_file',{...common,path:'docs/unit.txt',
   content:'new',expected_file_sha:FILE_SHA,message:'race test'}),/github_commit_rejected/);
  assert.equal(mutations,1);
 },(url,init)=>{
  if(init?.method!=='GET'){
   mutations++;assert.equal(new URL(url).pathname,'/graphql');
   return response({errors:[{type:'STALE_DATA',message:'branch advanced'}]});
  }
  return mockResponse(url,init);
 });
});
test('begin-task returns the current main HEAD after its own Test Hub lease commit',async()=>{
 let saved=null,leasePath='',heads=0;
 await withMock(async()=>{
  const r=await callGithubTool(token,'github_begin_task',{repo:REPO,branch:BRANCH,goal:'isolated acceptance'});
  assert.equal(r.base_sha,'e'.repeat(40));assert(r.lease_path);
  assert.match(Buffer.from(saved,'base64').toString(),/BASELINE_PROVEN/);
 },(url,init)=>{
  const path=new URL(url).pathname;
  if(path.includes('/git/ref/heads/'))return response({object:{sha:++heads===1?HEAD:'e'.repeat(40)}});
  if(path.includes('/git/trees/'))return response({truncated:false,tree:leasePath?[{type:'blob',path:leasePath.split('/').at(-1)}]:[]});
  if(path.includes('/contents/test-hub/findings/')){
   if(init.method==='PUT'){const p=JSON.parse(init.body);saved=p.content;leasePath=path.split('/contents/')[1];return response({commit:{sha:'e'.repeat(40)}})}
   return response({type:'file',content:saved});
  }
  return mockResponse(url,init);
 });
});
