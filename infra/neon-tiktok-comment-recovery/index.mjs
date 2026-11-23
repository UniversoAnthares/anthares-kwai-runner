// Comment-only recovery ledger for TikTok CORTES.
// Isolated from every video publication route; signed GitHub OIDC only.
import crypto from 'node:crypto';

const AUDIENCE='https://anthares-remote-primary.vercel.app/api/cortes-tiktok';
const REPO='UniversoAnthares/anthares-kwai-runner';
const JOB_REF=REPO+'/.github/workflows/cortes-tiktok-deferred-comments.yml@refs/heads/main';
const ACCOUNT=process.env.COMMENT_ACCOUNT||'';
const ID=/^\d{12,25}$/;
const ACCOUNTS=new Set(['universo.anthares','lucasrosalem4']);
let keys=null,keysUntil=0;

function response(status,body){
  return Response.json(body,{status,headers:{'Cache-Control':'no-store',
    'X-Anthares-TikTok':'comment-recovery-only'}});
}
function validInput(v){
  return v&&typeof v==='object'&&!Array.isArray(v)&&
    ID.test(String(v.source_video_id||''))&&ID.test(String(v.target_video_id||''))&&
    String(v.target_video_id)!==String(v.source_video_id)&&
    typeof v.comment_text==='string'&&v.comment_text.trim()===v.comment_text&&
    v.comment_text.length>=12&&v.comment_text.length<=300;
}
async function sql(query,params=[]){
  const conn=process.env.DATABASE_URL;
  if(!conn)throw Error('DB_CONFIG_MISSING');
  const u=new URL(conn);
  if(!['postgres:','postgresql:'].includes(u.protocol)||
     !u.hostname.endsWith('.neon.tech'))throw Error('DB_HOST_INVALID');
  const host='https://api.'+u.hostname.split('.').slice(1).join('.')+'/sql';
  const r=await fetch(host,{method:'POST',headers:{
    'Content-Type':'application/json',
    'Neon-Connection-String':conn,
    'Neon-Raw-Text-Output':'true'
  },body:JSON.stringify({query,params}),signal:AbortSignal.timeout(12000)});
  if(!r.ok)throw Error('DB_HTTP_'+r.status);
  const data=await r.json();
  if(!Array.isArray(data.rows))throw Error('DB_FORMAT_INVALID');
  return data.rows;
}
async function authorized(request){
  const match=/^Bearer\s+(.+)$/i.exec(request.headers.get('Authorization')||'');
  if(!match||match[1].length<200||match[1].length>16000)return false;
  const parts=match[1].split('.');
  if(parts.length!==3)return false;
  let head,claim;
  try{
    head=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
    claim=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
  }catch{return false;}
  if(head.alg!=='RS256'||!/^[a-zA-Z0-9_.-]{1,200}$/.test(head.kid||''))return false;
  const now=Math.floor(Date.now()/1000);
  const audiences=Array.isArray(claim.aud)?claim.aud:[claim.aud];
  if(claim.iss!=='https://token.actions.githubusercontent.com'||
     !audiences.includes(AUDIENCE)||
     claim.repository!==REPO||claim.ref!=='refs/heads/main'||
     (claim.job_workflow_ref||claim.workflow_ref)!==JOB_REF||
     !['schedule','workflow_dispatch','push'].includes(claim.event_name)||
     !Number.isFinite(claim.iat)||claim.iat>now+60||
     !Number.isFinite(claim.exp)||claim.exp<=now||claim.exp>now+3600||
     (claim.nbf!==undefined&&Number(claim.nbf)>now+60))return false;
  try{
    if(!keys||Date.now()>keysUntil){
      const doc=await fetch('https://token.actions.githubusercontent.com/.well-known/openid-configuration',
        {signal:AbortSignal.timeout(7500)});
      if(!doc.ok)return false;
      const discovery=await doc.json();
      if(!String(discovery.jwks_uri||'').startsWith('https://token.actions.githubusercontent.com/'))
        return false;
      const r=await fetch(discovery.jwks_uri,{signal:AbortSignal.timeout(7500)});
      if(!r.ok)return false;
      keys=(await r.json()).keys;keysUntil=Date.now()+300000;
    }
    const k=(keys||[]).find(v=>v.kid===head.kid&&v.kty==='RSA'&&(!v.alg||v.alg==='RS256'));
    if(!k)return false;
    const key=crypto.createPublicKey({key:k,format:'jwk'});
    return crypto.verify('RSA-SHA256',
      Buffer.from(parts[0]+'.'+parts[1]),key,
      Buffer.from(parts[2],'base64url'));
  }catch{return false;}
}
export default {async fetch(request){
  const u=new URL(request.url);
  const action=u.searchParams.get('action')||'';
  if(!ACCOUNTS.has(ACCOUNT))return response(503,{ok:false,error:'ACCOUNT_UNCONFIGURED'});
  if(action==='health'&&request.method==='GET'){
    try{
      const rows=await sql('SELECT count(*)::int AS n FROM public.anthares_tiktok_comment_sources WHERE account=$1',[ACCOUNT]);
      return response(200,{ok:true,service:'anthares-tiktok-comment-recovery',
        account:ACCOUNT,sources:Number(rows[0]?.n||0)});
    }catch{return response(503,{ok:false,error:'LEDGER_UNAVAILABLE'});}
  }
  if(!await authorized(request))return response(401,{ok:false,error:'OIDC_REQUIRED'});
  if(request.method==='GET'&&action==='comment-pending'){
    try{
      const rows=await sql(
        'SELECT s.source_video_id FROM public.anthares_tiktok_comment_sources s '+
        'WHERE s.account=$1 AND NOT EXISTS ('+
        'SELECT 1 FROM public.anthares_tiktok_comment_receipts r '+
        'WHERE r.account=s.account AND r.source_video_id=s.source_video_id) '+
        'ORDER BY s.confirmed_at ASC LIMIT 5',[ACCOUNT]);
      return response(200,{ok:true,account:ACCOUNT,pending:rows});
    }catch{return response(503,{ok:false,error:'PENDING_DB_UNAVAILABLE'});}
  }
  if(request.method==='GET'&&action==='comment-recent'){
    try{
      const rows=await sql(
        'SELECT comment_text,target_video_id,status,source_video_id FROM '+
        'public.anthares_tiktok_comment_receipts WHERE account=$1 '+
        'ORDER BY created_at DESC LIMIT 30',[ACCOUNT]);
      return response(200,{ok:true,account:ACCOUNT,recent:rows});
    }catch{return response(503,{ok:false,error:'HISTORY_DB_UNAVAILABLE'});}
  }
  if(request.method==='POST'&&['comment-reserve','comment-complete'].includes(action)){
    if(!(request.headers.get('content-type')||'').includes('application/json'))
      return response(415,{ok:false,error:'JSON_REQUIRED'});
    const raw=await request.text();
    if(raw.length>4096)return response(413,{ok:false,error:'BODY_TOO_LARGE'});
    let body;
    try{body=JSON.parse(raw);}catch{return response(400,{ok:false,error:'INVALID_JSON'});}
    if(action==='comment-reserve'){
      if(!validInput(body))return response(400,{ok:false,error:'INVALID_COMMENT_REQUEST'});
      try{
        const rows=await sql(
          'INSERT INTO public.anthares_tiktok_comment_receipts('+
          'account,source_video_id,target_video_id,comment_text,status) '+
          'SELECT $1,$2,$3,$4,\'started\' FROM public.anthares_tiktok_comment_sources s '+
          'WHERE s.account=$1 AND s.source_video_id=$2 '+
          'AND NOT EXISTS (SELECT 1 FROM (SELECT comment_text,target_video_id FROM '+
          'public.anthares_tiktok_comment_receipts WHERE account=$1 '+
          'ORDER BY created_at DESC LIMIT 30) z WHERE lower(z.comment_text)=lower($4) '+
          'OR z.target_video_id=$3) '+
          'ON CONFLICT DO NOTHING RETURNING source_video_id',
          [ACCOUNT,String(body.source_video_id),String(body.target_video_id),body.comment_text]);
        return response(200,{ok:true,reserved:rows.length===1});
      }catch{return response(503,{ok:false,error:'RESERVATION_DB_UNAVAILABLE'});}
    }
    if(!ID.test(String(body?.source_video_id||''))||
       !ID.test(String(body?.target_video_id||''))||
       !['uncertain','posted'].includes(body?.status))
      return response(400,{ok:false,error:'INVALID_COMPLETION'});
    try{
      const rows=await sql(
        'UPDATE public.anthares_tiktok_comment_receipts '+
        'SET status=$4, completed_at=now() '+
        'WHERE account=$1 AND source_video_id=$2 AND target_video_id=$3 '+
        'AND status=\'started\' RETURNING source_video_id',
        [ACCOUNT,String(body.source_video_id),String(body.target_video_id),body.status]);
      return response(200,{ok:rows.length===1,completed:rows.length===1});
    }catch{return response(503,{ok:false,error:'COMPLETION_DB_UNAVAILABLE'});}
  }
  return response(404,{ok:false,error:'COMMENT_ROUTE_ONLY'});
}};
