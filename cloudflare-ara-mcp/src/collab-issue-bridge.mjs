// Read-only GitHub Issue mailbox for an authorized Claude Free/Anthares MCP client.
// ChatGPT and Work use their connected GitHub app for write/review.
// This bridge does not grant any extra GitHub permissions or receive repository tokens.
import {fetchWithoutRedirects} from './secure-fetch.mjs';
const ROOT='https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner';
const OWNER_ID=81930373;
const PREFIX='[ANTHARES-COLLAB-PLAN] ';
const SCHEMA='anthares.collab.plan.v1';
function invalid(k){throw new Error(k)}
async function get(path){
  const r=await fetchWithoutRedirects(ROOT+path,{method:'GET',headers:{
    Accept:'application/vnd.github+json',
    'X-GitHub-Api-Version':'2022-11-28',
    'User-Agent':'Anthares-Owner-Scoped-Collab-Reader'
  }});
  if(!r.ok)invalid('collab_public_github_http_'+r.status);
  return r.json();
}
function isTask(v){
  return v&&typeof v==='object'&&!v.pull_request&&v.user?.id===OWNER_ID&&
    typeof v.title==='string'&&v.title.startsWith(PREFIX);
}
function sanitize(v){
  if(!isTask(v))invalid('collab_issue_not_found_or_not_owned');
  const t=String(v.body||'');let obj;
  try{obj=JSON.parse(t)}catch{invalid('collab_issue_bad_schema')}
  if(obj?.schema!==SCHEMA || !['chatgpt','work','claude'].includes(obj.origin)||
     typeof obj.task!=='string'||obj.task.length>1600||obj.task.length<5)
    invalid('collab_issue_bad_schema');
  return {issue_number:v.number,issue_id:v.id,title:v.title,
    origin:obj.origin,task:obj.task,updated_at:v.updated_at,
    url:v.html_url||'https://github.com/UniversoAnthares/anthares-kwai-runner/issues/'+v.number,
    state:v.state};
}
export const collabIssueTools=[
  {name:'collab_list_tasks',scope:'github.read',
    description:'Read the latest public owner-authored collaboration planning issues shared by ChatGPT, Claude and Work. Read-only; does not run a task.',
    inputSchema:{type:'object',additionalProperties:false,properties:{repo:{type:'string'}},required:['repo']}},
  {name:'collab_get_task',scope:'github.read',
    description:'Read one owner-authored collaboration issue, its Claude Code request_id and linked GitHub Actions status. No secret or write permissions.',
    inputSchema:{type:'object',additionalProperties:false,properties:{repo:{type:'string'},issue_number:{type:'integer',minimum:1}},required:['repo','issue_number']}}
];
export async function callCollabIssueTool(env,name,a={}){
  if(a.repo!=='UniversoAnthares/anthares-kwai-runner')invalid('collab_repository_not_allowed');
  if(name==='collab_list_tasks'){
    const issues=await get('/issues?state=open&sort=updated&direction=desc&per_page=80');
    if(!Array.isArray(issues))invalid('collab_invalid_response');
    const items=[];
    for(const issue of issues){
      if(!isTask(issue))continue;
      try{items.push(sanitize(issue))}catch{}
      if(items.length>=20)break;
    }
    return {tasks:items,read_only:true,owner_id:OWNER_ID};
  }
  if(name==='collab_get_task'){
    if(!Number.isSafeInteger(a.issue_number)||a.issue_number<1||a.issue_number>10000000)invalid('invalid_issue_number');
    const issue=await get('/issues/'+a.issue_number);
    const item=sanitize(issue);
    const comments=await get('/issues/'+a.issue_number+'/comments?per_page=100');
    if(!Array.isArray(comments)||comments.length>=100)invalid('collab_comments_incomplete');
    item.events=comments.filter(c=>c.user?.type==='Bot'||c.user?.id===OWNER_ID)
      .map(c=>String(c.body||'').slice(0,1200))
      .filter(s=>s.startsWith('[ANTHARES-COLLAB'));
    return {task:item,read_only:true};
  }
  invalid('unknown_collab_issue_tool');
}
