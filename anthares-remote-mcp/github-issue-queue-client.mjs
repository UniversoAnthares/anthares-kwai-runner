import { randomUUID } from 'node:crypto';

const API='https://api.github.com';
const REPO=(process.env.ARA_GITHUB_QUEUE_REPOSITORY||'UniversoAnthares/anthares-ara-queue').trim();
const TOKEN=(process.env.ARA_GITHUB_QUEUE_TOKEN||'').trim();
const LABEL=(process.env.ARA_GITHUB_QUEUE_LABEL||'ara-queued').trim();
const POLL_MS=Math.max(2000,Math.min(15000,Number(process.env.ARA_GITHUB_QUEUE_RESULT_POLL_MS||5000)));

export class IssueQueueUncertainError extends Error {
  constructor(message,details={}){super(message);this.name='IssueQueueUncertainError';this.details=details;}
}

export function issueQueueConfigured(){
  return /^[^/\s]+\/[^/\s]+$/.test(REPO) && TOKEN.length>=20 && LABEL.length>0;
}

function headers(){
  return {
    'Authorization':`Bearer ${TOKEN}`,
    'Accept':'application/vnd.github+json',
    'X-GitHub-Api-Version':'2022-11-28',
    'User-Agent':'AntharesRemoteMCP/1.0',
    'Content-Type':'application/json'
  };
}

async function gh(path,{method='GET',body,timeoutMs=15000}={}){
  const res=await fetch(`${API}${path}`,{method,headers:headers(),body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(timeoutMs)});
  const raw=await res.text();
  let data; try{data=raw?JSON.parse(raw):null;}catch{data={raw};}
  if(!res.ok){
    const e=new Error(`github queue ${res.status}: ${data?.message||data?.raw||'request failed'}`);
    e.status=res.status; throw e;
  }
  return data;
}

function sleep(ms){return new Promise(r=>setTimeout(r,ms));}

function decodeResult(comments){
  const parts=new Map(); let total=0;
  for(const c of comments||[]){
    const body=String(c?.body||'');
    const m=body.match(/^ARA_RESULT_B64 part=(\d+)\/(\d+)\s*\n([A-Za-z0-9+/=]+)\s*$/m);
    if(!m) continue;
    const n=Number(m[1]),t=Number(m[2]);
    if(!Number.isInteger(n)||!Number.isInteger(t)||n<1||t<1||n>t) continue;
    if(total && total!==t) continue;
    total=t; parts.set(n,m[3]);
  }
  if(!total||parts.size!==total) return null;
  let encoded=''; for(let i=1;i<=total;i++){if(!parts.has(i))return null;encoded+=parts.get(i);}
  try{return JSON.parse(Buffer.from(encoded,'base64').toString('utf8'));}catch{return null;}
}

export async function executeViaIssueQueue({deviceId,type,args={},timeoutSeconds=30}){
  if(!issueQueueConfigured()) throw new Error('github issue queue not configured');
  const jobId=`mcp-gh-${Date.now()}-${randomUUID()}`;
  const envelope={job_id:jobId,device_id:deviceId,type,args,timeout_seconds:Math.max(1,Math.min(120,timeoutSeconds))};
  let issue;
  try{
    issue=await gh(`/repos/${REPO}/issues`,{method:'POST',body:{title:`ARA ${type} ${jobId}`,body:JSON.stringify(envelope),labels:[LABEL]},timeoutMs:15000});
  }catch(e){
    e.issueQueueSubmitted=false;
    throw e;
  }
  const number=Number(issue?.number);
  if(!number) throw new IssueQueueUncertainError('github queue accepted request without issue number',{job_id:jobId});
  const deadline=Date.now()+Math.min(150000,(timeoutSeconds+35)*1000);
  while(Date.now()<deadline){
    try{
      const comments=await gh(`/repos/${REPO}/issues/${number}/comments?per_page=100`,{timeoutMs:15000});
      const result=decodeResult(comments);
      if(result) return {...result,transport:'github-issues',queue_issue:number,queue_job_id:jobId};
    }catch(e){
      // Once submitted, never fall through to another executor: the outcome may already exist.
    }
    await sleep(POLL_MS);
  }
  throw new IssueQueueUncertainError('github queue execution outcome unknown; fallback suppressed to prevent duplicate side effects',{issue_number:number,job_id:jobId});
}

export function issueQueueHealth(){
  return {configured:issueQueueConfigured(),repository:REPO,label:LABEL,poll_ms:POLL_MS};
}
