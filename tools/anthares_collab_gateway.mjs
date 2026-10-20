/**
 * Anthares multiagent collaboration v1: public owner-only plan tasks.
 * GitHub issue -> validated idempotent dispatch -> Claude Code cloud runner.
 * No paid services, no PC runtime, no direct main edits, no task result pasted to public issues.
 */
import {createHash} from 'node:crypto';
import {readFileSync,appendFileSync} from 'node:fs';

export const OWNER_ID=81930373;
export const REPO='UniversoAnthares/anthares-kwai-runner';
export const PREFIX='[ANTHARES-COLLAB-PLAN] ';
export const SCHEMA='anthares.collab.plan.v1';
export const MARKER='ANTHARES_COLLAB_V1_CLAIM';
export const WORKFLOW='anthares-free-claude.yml';
export const LIMIT=1600;

function fail(code){throw new Error(code)}
function assert(x,code){if(!x)fail(code)}
export function requestId(issueId){
  assert(Number.isSafeInteger(issueId)&&issueId>0,'invalid_issue_id');
  const h=createHash('sha256').update(REPO+':collab:v1:issue:'+issueId).digest('hex');
  return h.slice(0,8)+'-'+h.slice(8,12)+'-5'+h.slice(13,16)+'-a'+h.slice(17,20)+'-'+h.slice(20,32);
}
export function validateEvent(event){
  assert(event&&typeof event==='object'&&event.action==='opened','invalid_event_action');
  assert(event.repository?.full_name===REPO,'wrong_repository');
  assert(event.sender?.id===OWNER_ID&&event.issue?.user?.id===OWNER_ID,'unauthorized_issuer');
  assert(!event.issue.pull_request,'pull_request_not_a_task');
  const title=event.issue.title;
  assert(typeof title==='string'&&title.startsWith(PREFIX)&&title.length<=140&&title.length>PREFIX.length,'wrong_title');
  const raw=event.issue.body;
  assert(typeof raw==='string'&&raw.length<=2400,'bad_body');
  let a;try{a=JSON.parse(raw)}catch{fail('invalid_task_json')}
  assert(a&&typeof a==='object'&&!Array.isArray(a),'invalid_task_object');
  assert(Object.keys(a).sort().join(',')==='origin,schema,task','unexpected_task_fields');
  assert(a.schema===SCHEMA,'unsupported_schema');
  assert(['chatgpt','work','claude'].includes(a.origin),'invalid_origin');
  assert(typeof a.task==='string'&&a.task.trim().length>=5&&a.task.length<=LIMIT,'invalid_task_size');
  assert(!/[\x00-\x1F\x7F]/.test(a.task),'invalid_task_control_chars');
  // Public issue + public Actions logs: do not accept obvious secret material.
  assert(!/(?:github_pat_|gh[pousr]_|sk-[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|(?:password|api[_ -]?key|access[_ -]?token)\s*[:=]\s*\S+)/i.test(a.task),'sensitive_task_rejected');
  assert(Number.isSafeInteger(event.issue.number)&&event.issue.number>0,'invalid_issue_number');
  const id=event.issue.id;
  const request_id=requestId(id);
  return {request_id,issue_id:id,issue_number:event.issue.number,origin:a.origin,task:a.task.trim(),repo:REPO,mode:'plan'};
}
export function findRun(body,id){
  const runs=(body?.workflow_runs||[]).filter(x=>x.event==='workflow_dispatch'&&x.head_branch==='main'&&x.display_title==='Anthares Claude Code '+id);
  assert(runs.length<=1,'ambiguous_dispatch_run');
  return runs[0]||null;
}
const BASE='https://api.github.com/repos/'+REPO;
function token(){const value=process.env.GH_TOKEN||process.env.GITHUB_TOKEN;assert(value,'missing_workflow_token');return value}
async function api(method,path,body){
  assert(path.startsWith('/')&&!path.startsWith('//'),'bad_api_path');
  const r=await fetch(BASE+path,{method,redirect:'manual',headers:{
    Authorization:'Bearer '+token(),'User-Agent':'Anthares-Collab-Gateway',
    Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',
    ...(body===undefined?{}:{'Content-Type':'application/json'})
  },body:body===undefined?undefined:JSON.stringify(body)});
  if(!r.ok)fail('github_http_'+r.status+'_'+method);
  if(r.status===204)return null;
  return r.json();
}
const notesPath=n=>'/issues/'+n+'/comments';
async function note(n,text){return api('POST',notesPath(n),{body:text})}
async function comments(n){
  const a=await api('GET',notesPath(n)+'?per_page=100');
  assert(Array.isArray(a),'invalid_issue_comments');
  // At most 100 issue comments supported. Never bypass ambiguity by resubmitting.
  assert(a.length<100,'comments_pagination_ambiguous');
  return a;
}
function marker(id){return '['+MARKER+' '+id+']'}
export async function dispatch(event,{get=api,post=note,getComments=comments}={}){
  const q=validateEvent(event);
  const prior=await getComments(q.issue_number);
  if(prior.some(x=>typeof x.body==='string'&&x.body.includes(marker(q.request_id)))){
    return {...q,accepted:false,already_claimed:true};
  }
  // CLAIM FIRST: if dispatch response becomes uncertain, never repeat a costly task.
  await post(q.issue_number,marker(q.request_id)+' CLAIMED source='+q.origin+'; plan-only; preparing Claude Code remote dispatch. No secrets or merges.');
  try {
    await get('POST','/actions/workflows/'+WORKFLOW+'/dispatches',{
      ref:'main',inputs:{mode:'plan',task:q.task,scope:'',request_id:q.request_id,origin_issue:String(q.issue_number)}
    });
  } catch(e) {
    await post(q.issue_number,'[ANTHARES-COLLAB] DISPATCH_UNCERTAIN id='+q.request_id+' error='+String(e.message).slice(0,70)+'; do NOT re-dispatch automatically.');
    throw e;
  }
  await post(q.issue_number,'[ANTHARES-COLLAB] DISPATCH_ACCEPTED id='+q.request_id+'; GitHub Actions Claude Code in progress. This is a plan, not an edit.');
  return {...q,accepted:true,already_claimed:false};
}
async function waitForRun(q,{get=api,post=note,sleep=ms=>new Promise(r=>setTimeout(r,ms)),tries=28,delay=12000}={}){
  if(!q.accepted)return {...q,status:'already_claimed'};
  let run=null;
  for(let i=0;i<tries;i++){
    const o=await get('GET','/actions/workflows/'+WORKFLOW+'/runs?event=workflow_dispatch&per_page=100');
    run=findRun(o,q.request_id);
    if(run?.status==='completed')break;
    await sleep(delay);
  }
  const label=run?.status==='completed'?'COMPLETED':'AWAITING_RESULT';
  const url=run?.html_url||'https://github.com/'+REPO+'/actions/workflows/'+WORKFLOW;
  const conclusion=run?.conclusion||'pending';
  await post(q.issue_number,'[ANTHARES-COLLAB] '+label+' id='+q.request_id+' conclusion='+conclusion+' run='+url+'; inspect the GitHub Actions artifact with the matching ID. No automatic merge.');
  return {...q,status:label,conclusion,run_url:url};
}
/**
 * Strong gate for a nested workflow_dispatch issued by github-actions[bot].
 * The authoritative owner-created Issue supplies the task and deterministic UUID.
 * This does not enable bot-origin direct requests without a verified issue.
 */
export async function verifyDelegation({loadIssue=async n=>api('GET','/issues/'+n)}={}){
  const number=Number(process.env.ANTHARES_COLLAB_ORIGIN_ISSUE);
  assert(Number.isSafeInteger(number)&&number>0&&number<=10000000,'invalid_origin_issue');
  assert(process.env.ANTHARES_TASK_MODE==='plan'&&!process.env.ANTHARES_TASK_SCOPE,'invalid_delegated_mode');
  const issue=await loadIssue(number);
  const event={action:'opened',sender:{id:OWNER_ID},repository:{full_name:REPO},issue};
  const task=validateEvent(event);
  assert(task.issue_number===number,'origin_issue_mismatch');
  assert(task.task===process.env.ANTHARES_TASK_PROMPT,'origin_task_mismatch');
  assert(task.request_id===process.env.ANTHARES_REQUEST_ID,'origin_request_id_mismatch');
  return task;
}

export async function main(){
  if(process.argv[2]==='verify'){
    const t=await verifyDelegation();
    console.log('ANTHARES_COLLAB_OWNER_ORIGIN_VERIFIED='+t.request_id);
    return;
  }
  const event=JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH,'utf8'));
  const result=await dispatch(event);
  if(result.accepted)await waitForRun(result);
  console.log('ANTHARES_COLLAB_GATEWAY='+ (result.already_claimed?'IDEMPOTENT':result.accepted?'DISPATCHED':'NOOP'));
}
if(process.argv[1]&&import.meta.url==='file://'+process.argv[1].replaceAll('\\','/'))main().catch(e=>{console.error('ANTHARES_COLLAB_GATEWAY_ERROR='+e.message);process.exitCode=1});
