// Anthares GitHub bridge for Claude Free: reviewed branches and draft PRs only.
// All privileged actions require OAuth github.write plus a server-side GitHub credential.
// Cloudflare secret: ANTHARES_GITHUB_TOKEN (fine-grained; only approved repositories).
const ROOT = 'https://api.github.com';
const OWNER = 'UniversoAnthares';
const APPROVED = new Set([
  'anthares-kwai-runner','anthares-clipper','anthares-wordpress',
  'home','anthares-transcricao'
]);
const HUB = OWNER + '/anthares-kwai-runner';
const LEASE_PREFIX = 'test-hub/findings/lease-claude-github-';
const branchPattern = /^claude\/[a-z0-9][a-z0-9._/-]{0,70}$/;
const shaPattern = /^[0-9a-f]{40}$/i;
const SAFE_STATUSES = new Set(['PARTIAL','PROVEN','FAILED']);

function problem(message, status=400) {
  const e = new Error(message); e.status = status; throw e;
}
function validateRepo(value) {
  const raw = String(value || '');
  if (!raw.startsWith(OWNER + '/') || !APPROVED.has(raw.slice(OWNER.length + 1))) problem('repository_not_allowed',403);
  return raw;
}
function validateBranch(value) {
  const s=String(value||'');
  if (!branchPattern.test(s) || s.includes('..') || s.includes('//') || s.endsWith('.') || s.endsWith('.lock')) problem('invalid_claude_branch');
  return s;
}
function validatePath(value) {
  const s=String(value||'');
  if (!s || s.length>240 || s.startsWith('/') || s.includes('\\') || /[\x00-\x1f]/.test(s) || s.includes('%') || s.includes(':')) problem('invalid_path');
  const segments=s.split('/');
  if (segments.some(x=>!x || x==='.' || x==='..' || x==='.git')) problem('path_traversal');
  if (segments.some(x=>/^(?:\.env(?:\..*)?|\.npmrc|\.pypirc|id_rsa|credentials(?:\..*)?|secret(?:s)?(?:\..*)?|cookies(?:\..*)?)$/i.test(x))) problem('sensitive_path_denied',403);
  if (s.startsWith('test-hub/findings/') || s.startsWith('anthares-kwai-session-vault/')) problem('reserved_path',403);
  return s;
}
function validateSha(v){const s=String(v||'');if(!shaPattern.test(s))problem('expected_sha_required');return s;}
function utf8Base64(s){
  const bytes=new TextEncoder().encode(s); let raw='';
  for(let i=0;i<bytes.length;i+=8192) raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
  return btoa(raw);
}
function decodeB64(s){
  const raw=atob(String(s||'').replace(/\s/g,'')); const bytes=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++) bytes[i]=raw.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}
function encPath(p){return p.split('/').map(encodeURIComponent).join('/');}
function token(env){const v=String(env.ANTHARES_GITHUB_TOKEN||'').trim();if(!v)problem('github_server_credential_unconfigured',503);return v;}
async function api(env,method,path,body,accept404=false){
  const url=ROOT+path;
  const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
  // Public reads may work without a GitHub credential; writes always require one.
  const credential=String(env.ANTHARES_GITHUB_TOKEN||'').trim();
  if(credential)headers.Authorization='Bearer '+credential;
  else if(method!=='GET')token(env);
  if(body!==undefined)headers['Content-Type']='application/json';
  const response=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body),redirect:'error'});
  if(response.status===404 && accept404)return null;
  if(!response.ok)problem('github_http_'+response.status, response.status===401||response.status===403?503:409);
  const result=await response.json();
  return result;
}
function repoUrl(repo){return '/repos/'+repo;}
async function getHead(env,repo,branch) {
  const r=await api(env,'GET',repoUrl(repo)+'/git/ref/heads/'+encPath(branch));
  const sha=r?.object?.sha;
  if(!shaPattern.test(sha||''))problem('unexpected_ref');
  return sha;
}
async function getFile(env,repo,path,branch,optional=false){
  return api(env,'GET',repoUrl(repo)+'/contents/'+encPath(path)+'?ref='+encodeURIComponent(branch),undefined,optional);
}
function leaseBody(repo,branch,goal,created,expires,id){
  return '# Claude GitHub task '+id+'\nSTATUS: RUNNING\nAREA: claude-github-tools\nLEASE_OWNER: claude-free-mcp\nREPO: '+repo+'\nBRANCH: '+branch+'\nSTART_UTC: '+created+'\nEXPIRES_UTC: '+expires+'\nGOAL: '+goal.replace(/[\r\n]/g,' ').slice(0,200)+'\n';
}
function leaseFields(content){
  const f={};
  for(const line of content.split(/\r?\n/)){
    const m=/^([A-Z_]+):\s*(.*)$/.exec(line);
    if(m)f[m[1]]=m[2].trim();
  }
  return f;
}
async function leaseEntries(env){
  // GitHub Contents directory listings stop at 1,000 entries. The Test Hub
  // already has hundreds of findings; read the exact Git tree instead.
  const dirs=await api(env,'GET',repoUrl(HUB)+'/contents/test-hub?ref=main');
  const findings=Array.isArray(dirs) && dirs.find(e=>e.name==='findings' && e.type==='dir' && shaPattern.test(e.sha||''));
  if(!findings)problem('invalid_test_hub');
  const listing=await api(env,'GET',repoUrl(HUB)+'/git/trees/'+findings.sha);
  if(listing?.truncated || !Array.isArray(listing?.tree))problem('truncated_test_hub');
  return listing.tree
    .filter(e=>e.type==='blob' && e.path?.startsWith('lease-claude-github-') && e.path.endsWith('.md'))
    .map(e=>({name:e.path,path:'test-hub/findings/'+e.path}));
}
async function validateLease(env,repo,branch,path){
  if(!String(path||'').startsWith(LEASE_PREFIX) || !String(path).endsWith('.md') || String(path).includes('..'))problem('lease_required',403);
  const lease=await getFile(env,HUB,path,'main');
  if(lease?.type!=='file')problem('missing_lease',403);
  const fields=leaseFields(decodeB64(lease.content));
  if(fields.STATUS!=='RUNNING'||fields.LEASE_OWNER!=='claude-free-mcp'||fields.REPO!==repo||fields.BRANCH!==branch)problem('lease_mismatch',403);
  const until=Date.parse(fields.EXPIRES_UTC||'');
  if(!Number.isFinite(until)||until<=Date.now()||until>Date.now()+31*60000)problem('lease_expired_or_invalid',403);
  // Another earlier active Claude lease for same repository must win.
  const entries=await leaseEntries(env);
  const active=[];
  for(const item of entries){
    if(item.path===path)continue;
    const remote=await getFile(env,HUB,item.path,'main',true);
    if(!remote?.content)continue;
    const meta=leaseFields(decodeB64(remote.content));
    if(meta.STATUS==='RUNNING'&&meta.REPO===repo&&Date.parse(meta.EXPIRES_UTC||'')>Date.now())active.push(meta);
  }
  const start=Date.parse(fields.START_UTC||'');
  if(active.some(x=>Date.parse(x.START_UTC||'')<=start))problem('another_claude_lease_active',409);
  return fields;
}
async function startTask(env,{repo,branch,goal}){
  repo=validateRepo(repo); branch=validateBranch(branch);
  if(!String(goal||'').trim()||String(goal).length>250)problem('goal_required');
  const items=await leaseEntries(env);
  for(const item of items){
    const file=await getFile(env,HUB,item.path,'main',true);
    if(!file?.content)continue;
    const f=leaseFields(decodeB64(file.content));
    if(f.STATUS==='RUNNING'&&f.REPO===repo&&Date.parse(f.EXPIRES_UTC||'')>Date.now())problem('another_claude_lease_active',409);
  }
  const id=new Date().toISOString().replace(/\D/g,'').slice(0,14)+'-'+crypto.randomUUID().slice(0,8);
  const path=LEASE_PREFIX+id+'.md';
  const created=new Date().toISOString();
  const expires=new Date(Date.now()+20*60000).toISOString();
  await api(env,'PUT',repoUrl(HUB)+'/contents/'+encPath(path),{
    message:'docs(test-hub): Claude GitHub task lease [skip ci]',
    branch:'main',content:utf8Base64(leaseBody(repo,branch,goal,created,expires,id))
  });
  await validateLease(env,repo,branch,path);
  return {repo,branch,lease_path:path,expires,authorized_actions:'branch-and-draft-pr'};
}
export const githubTools=[
  {name:'github_get_file',description:'Read an approved Anthares GitHub repository file and its SHA.',inputSchema:{type:'object',properties:{repo:{type:'string'},path:{type:'string'},ref:{type:'string'}},required:['repo','path']},scope:'github.read'},
  {name:'github_begin_task',description:'Create a 20-minute Test Hub lease before making a Claude draft-branch change.',inputSchema:{type:'object',properties:{repo:{type:'string'},branch:{type:'string'},goal:{type:'string'}},required:['repo','branch','goal']},scope:'github.write'},
  {name:'github_create_branch',description:'Create an isolated claude/* branch from an exact expected main SHA, with valid lease.',inputSchema:{type:'object',properties:{repo:{type:'string'},branch:{type:'string'},base_sha:{type:'string'},lease_path:{type:'string'}},required:['repo','branch','base_sha','lease_path']},scope:'github.write'},
  {name:'github_put_file',description:'Create or update one UTF-8 code file on a claude/* branch with an exact HEAD and expected file SHA; rejects main.',inputSchema:{type:'object',properties:{repo:{type:'string'},branch:{type:'string'},path:{type:'string'},content:{type:'string'},expected_head_sha:{type:'string'},expected_file_sha:{type:'string'},lease_path:{type:'string'},message:{type:'string'}},required:['repo','branch','path','content','expected_head_sha','lease_path','message']},scope:'github.write'},
  {name:'github_draft_pr',description:'Open a draft pull request from claude/* into main after lease/head validation.',inputSchema:{type:'object',properties:{repo:{type:'string'},branch:{type:'string'},expected_head_sha:{type:'string'},title:{type:'string'},body:{type:'string'},lease_path:{type:'string'}},required:['repo','branch','expected_head_sha','title','lease_path']},scope:'github.write'}
];
export async function callGithubTool(env,name,args={}){
  const repo=validateRepo(args.repo);
  if(name==='github_get_file'){
    const path=validatePath(args.path);
    const ref=String(args.ref||'main');
    if(ref!=='main')validateBranch(ref);
    const f=await getFile(env,repo,path,ref);
    if(f.type!=='file'||f.size>250000)problem('file_not_supported');
    return {repo,path,ref,sha:f.sha,content:decodeB64(f.content)};
  }
  const branch=validateBranch(args.branch);
  if(name==='github_begin_task')return startTask(env,{repo,branch,goal:args.goal});
  await validateLease(env,repo,branch,args.lease_path);
  if(name==='github_create_branch'){
    const base=validateSha(args.base_sha);
    if(await getHead(env,repo,'main')!==base)problem('stale_base_sha',409);
    const existing=await api(env,'GET',repoUrl(repo)+'/git/ref/heads/'+encPath(branch),undefined,true);
    if(existing)problem('branch_already_exists',409);
    const x=await api(env,'POST',repoUrl(repo)+'/git/refs',{ref:'refs/heads/'+branch,sha:base});
    return {created:true,repo,branch,sha:x.object?.sha};
  }
  const expected=validateSha(args.expected_head_sha);
  if(await getHead(env,repo,branch)!==expected)problem('stale_branch_head',409);
  if(name==='github_put_file'){
    const path=validatePath(args.path);
    const data=String(args.content??'');
    if(new TextEncoder().encode(data).length>200000)problem('content_too_large');
    const prior=await getFile(env,repo,path,branch,true);
    const expectedFile=args.expected_file_sha;
    if(prior && (prior.type!=='file'||!shaPattern.test(String(expectedFile||''))||prior.sha!==expectedFile))problem('stale_file_sha',409);
    if(!prior && expectedFile)problem('file_missing_expected_sha',409);
    const message=String(args.message||'').slice(0,120).trim();
    if(!message)problem('commit_message_required');
    if(await getHead(env,repo,branch)!==expected)problem('stale_branch_head',409);
    const payload={branch,message:message+' [skip ci]',content:utf8Base64(data)};
    if(prior)payload.sha=prior.sha;
    const changed=await api(env,'PUT',repoUrl(repo)+'/contents/'+encPath(path),payload);
    return {repo,branch,path,commit:changed.commit?.sha,blob_sha:changed.content?.sha};
  }
  if(name==='github_draft_pr'){
    const title=String(args.title||'').trim().slice(0,120);
    if(!title)problem('title_required');
    const open=await api(env,'GET',repoUrl(repo)+'/pulls?state=open&head='+encodeURIComponent(OWNER+':'+branch));
    if(open.length)problem('pull_request_already_open',409);
    const pr=await api(env,'POST',repoUrl(repo)+'/pulls',{
      title,body:String(args.body||'').slice(0,4000),
      head:branch,base:'main',draft:true,maintainer_can_modify:true
    });
    return {repo,number:pr.number,url:pr.html_url,draft:pr.draft,head_sha:pr.head?.sha};
  }
  problem('unknown_github_tool',404);
}
export {validateRepo,validateBranch,validatePath,validateSha,leaseFields};
