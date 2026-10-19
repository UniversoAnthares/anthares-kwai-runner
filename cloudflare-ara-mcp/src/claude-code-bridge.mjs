// Scoped Cloudflare MCP bridge from the owner-authorized Claude session to a free
// GitHub Actions Claude Code runner. No shell, GitHub token or arbitrary repo inputs.
import {fetchWithoutRedirects} from './secure-fetch.mjs';
const REPO='UniversoAnthares/anthares-kwai-runner';
const API='https://api.github.com/repos/'+REPO;
const WORKFLOW='anthares-free-claude.yml';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RESERVED=/(?:^|\/)(?:\.git|\.github|node_modules|test-hub|\.env(?:\..*)?|\.ssh|secrets?|credentials?|cookies?|vault)(?:\/|$)/i;
const ARTIFACT_MAX=262144;
const RESULT_NAME='anthares-claude-result.txt';
function reject(code){const e=new Error(code);e.code=code;throw e;}
export function validateClaudeTask(a){
  if(!a||typeof a!=='object'||Array.isArray(a)||Object.keys(a).some(x=>!['mode','task','scope'].includes(x)))reject('invalid_task_fields');
  const mode=a.mode;
  if(mode!=='plan'&&mode!=='edit')reject('invalid_task_mode');
  const task=a.task;
  if(typeof task!=='string'||!task.trim()||task.length>5500||/[\x00-\x08\x0B-\x1F]/.test(task))reject('invalid_task_text');
  const scope=mode==='edit'?a.scope:'';
  if(mode==='edit'&&(
    typeof scope!=='string'||scope.length>170||! /^(?:tools|docs|ai-runners)\/[A-Za-z0-9._/-]+$/.test(scope)||
    scope.split('/').some(x=>x==='.'||x==='..'||!x)||RESERVED.test(scope)
  ))reject('invalid_or_protected_scope');
  if(mode==='plan'&&a.scope)reject('scope_only_for_edit');
  return {mode,task:task.trim(),scope:scope||''};
}
export function validateRequestId(a){
  if(!a||typeof a!=='object'||Array.isArray(a)||Object.keys(a).some(x=>x!=='request_id')||!UUID.test(a.request_id||''))reject('invalid_request_id');
  return a.request_id.toLowerCase();
}
function credentials(env){
  const key=String(env?.ANTHARES_GITHUB_TOKEN||'').trim();
  if(!key)reject('github_credential_unconfigured');
  return key;
}
async function request(env,path,{method='GET',body}={}){
  const headers={Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Anthares-Claude-Code-Bridge',Authorization:'Bearer '+credentials(env)};
  if(body!==undefined)headers['Content-Type']='application/json';
  const response=await fetchWithoutRedirects(API+path,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
  if(!response.ok)reject('github_actions_http_'+response.status);
  if(response.status===204)return null;
  return response.json();
}
const RUNS_PATH='/actions/workflows/'+WORKFLOW+'/runs?event=workflow_dispatch&per_page=100';
export function findRun(runs,id){
  const found=(runs?.workflow_runs||[]).filter(x=>
    x.event==='workflow_dispatch'&&x.head_branch==='main'&&
    x.display_title==='Anthares Claude Code '+id);
  if(found.length>1)reject('ambiguous_request_id');
  return found[0]||null;
}
async function listRuns(env){return request(env,RUNS_PATH);}
async function locatedRun(env,id){
  const result=await listRuns(env);
  const run=findRun(result,id);
  if(!run)return null;
  return {request_id:id,run_id:run.id,run_url:run.html_url,
    status:run.status,conclusion:run.conclusion||null};
}
export async function startClaudeCode(env,a){
  const task=validateClaudeTask(a);
  const existing=await listRuns(env);
  const active=(existing?.workflow_runs||[]).some(x=>
    x.event==='workflow_dispatch'&&['queued','in_progress','waiting','pending','requested'].includes(x.status));
  if(active)reject('remote_claude_code_busy');
  // Generate internally: caller cannot impersonate other request IDs.
  const request_id=crypto.randomUUID();
  await request(env,'/actions/workflows/'+WORKFLOW+'/dispatches',{
    method:'POST',
    body:{ref:'main',inputs:{...task,request_id}}
  });
  return {accepted:true,request_id,mode:task.mode,status:'queued',
    check_with:'get_claude_code_status',result_with:'get_claude_code_result',
    workflow_url:'https://github.com/'+REPO+'/actions/workflows/'+WORKFLOW,
    note:'Remote execution is queued. Call get_claude_code_status using this request_id.'};
}
export async function getClaudeCodeStatus(env,a){
  const id=validateRequestId(a),run=await locatedRun(env,id);
  return run||{request_id:id,status:'not_visible_yet',
    note:'GitHub may take several seconds to list a newly dispatched run.'};
}
function zipResult(bytes){
  if(bytes.byteLength>ARTIFACT_MAX)reject('artifact_too_large');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  const text=new TextDecoder('utf-8',{fatal:true});
  // Read the central directory, not local header sizes (ZIP data descriptors).
  let eocd=-1;
  for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--){
    if(view.getUint32(i,true)===0x06054b50){eocd=i;break;}
  }
  if(eocd<0)reject('artifact_invalid_zip');
  const entries=view.getUint16(eocd+10,true),cdOff=view.getUint32(eocd+16,true);
  if(entries<1||entries>8||cdOff>=bytes.length)reject('artifact_invalid_directory');
  let p=cdOff;
  for(let i=0;i<entries;i++){
    if(p+46>bytes.length||view.getUint32(p,true)!==0x02014b50)reject('artifact_invalid_entry');
    const method=view.getUint16(p+10,true),size=view.getUint32(p+20,true),
      rawSize=view.getUint32(p+24,true),namelen=view.getUint16(p+28,true),
      extra=view.getUint16(p+30,true),comment=view.getUint16(p+32,true),
      offset=view.getUint32(p+42,true);
    if(p+46+namelen>bytes.length)reject('artifact_bad_filename');
    const name=text.decode(bytes.slice(p+46,p+46+namelen));
    if(name===RESULT_NAME){
      if(method!==0)reject('artifact_not_stored');
      if(size>30000||rawSize!==size)reject('artifact_result_too_large');
      if(offset+30>bytes.length||view.getUint32(offset,true)!==0x04034b50)reject('artifact_invalid_local');
      const localName=view.getUint16(offset+26,true),localExtra=view.getUint16(offset+28,true);
      const from=offset+30+localName+localExtra;
      if(from+size>bytes.length)reject('artifact_truncated');
      return text.decode(bytes.slice(from,from+size));
    }
    p+=46+namelen+extra+comment;
  }
  reject('artifact_result_missing');
}
export {zipResult};
function allowedDownloadLocation(href){
  const u=new URL(href);
  if(u.protocol!=='https:'||u.username||u.password||u.port)reject('artifact_untrusted_redirect');
  const h=u.hostname.toLowerCase();
  if(!((h.endsWith('.blob.core.windows.net')||h.endsWith('.actions.githubusercontent.com')||
    h==='objects.githubusercontent.com'||h.endsWith('.githubusercontent.com')))&&h!=='github.com')
    reject('artifact_untrusted_redirect');
  return u.href;
}
async function artifactBytes(env,artifactId){
  if(!Number.isSafeInteger(artifactId)||artifactId<1)reject('invalid_artifact_id');
  const headers={Authorization:'Bearer '+credentials(env),Accept:'application/vnd.github+json',
    'User-Agent':'Anthares-Claude-Code-Bridge'};
  const response=await fetch(API+'/actions/artifacts/'+artifactId+'/zip',{headers,redirect:'manual'});
  if(response.status!==302)reject('artifact_download_http_'+response.status);
  const href=allowedDownloadLocation(response.headers.get('location')||'');
  // The signed download target never receives the private GitHub token.
  const content=await fetch(href,{redirect:'manual'});
  if(!content.ok)reject('artifact_blob_http_'+content.status);
  if(content.status>=300&&content.status<400)reject('artifact_blob_redirect');
  if(Number(content.headers.get('content-length')||0)>ARTIFACT_MAX)reject('artifact_too_large');
  const ab=await content.arrayBuffer();
  if(ab.byteLength>ARTIFACT_MAX)reject('artifact_too_large');
  return new Uint8Array(ab);
}
export async function getClaudeCodeResult(env,a){
  const id=validateRequestId(a),run=await locatedRun(env,id);
  if(!run)return {request_id:id,status:'not_visible_yet'};
  if(run.status!=='completed')return {...run,ready:false};
  if(run.conclusion!=='success')return {...run,ready:false,reason:'workflow_not_successful'};
  const artifacts=await request(env,'/actions/runs/'+run.run_id+'/artifacts?per_page=30');
  const match=(artifacts?.artifacts||[]).filter(x=>
    x.name==='anthares-free-claude-result-'+run.run_id&&!x.expired);
  if(match.length!==1)return {...run,ready:false,reason:'result_artifact_not_available'};
  const value=zipResult(await artifactBytes(env,match[0].id));
  return {...run,ready:true,result:value.slice(0,12000)};
}
export const claudeCodeTools=[
  {name:'run_claude_code',scope:'github.write',
    description:'Send one scoped plan/edit task directly to the remote FREE Claude Code GitHub Actions runner. No PC, VPS, or paid model. Returns request_id for async polling. edit needs exactly one file path, opens a draft PR; never merges.',
    inputSchema:{type:'object',additionalProperties:false,properties:{
      mode:{type:'string',enum:['plan','edit']},task:{type:'string',minLength:1,maxLength:5500},
      scope:{type:'string',description:'For edit only: exact path under tools/, docs/, ai-runners/'}},
      required:['mode','task']}},
  {name:'get_claude_code_status',scope:'github.read',
    description:'Check queued/in-progress/completed status of a run_claude_code request_id. Does not run a task.',
    inputSchema:{type:'object',additionalProperties:false,properties:{request_id:{type:'string'}},required:['request_id']}},
  {name:'get_claude_code_result',scope:'github.read',
    description:'Read the completed free Claude Code result text from short-retention GitHub Actions artifact, or report workflow error. No secret or external browser session.',
    inputSchema:{type:'object',additionalProperties:false,properties:{request_id:{type:'string'}},required:['request_id']}}
];
export async function callClaudeCodeTool(env,name,args){
  if(name==='run_claude_code')return startClaudeCode(env,args);
  if(name==='get_claude_code_status')return getClaudeCodeStatus(env,args);
  if(name==='get_claude_code_result')return getClaudeCodeResult(env,args);
  reject('unknown_claude_code_tool');
}
