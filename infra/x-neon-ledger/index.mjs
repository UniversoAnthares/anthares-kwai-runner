import crypto from 'node:crypto';

// Independently hosted X-only ledger. Do not touch the cross-network CORTES queue.
const ACCOUNT='lucasyahn', REPO='UniversoAnthares/anthares-kwai-runner';
const hash=s=>crypto.createHash('sha256').update(String(s)).digest('hex');
const keyOk=s=>/^[A-Za-z0-9_.:-]{12,160}$/.test(s||'');
const urlOk=s=>/^https:\/\/x\.com\/lucasyahn\/status\/[0-9]+$/.test(s||'');
const out=(status,obj)=>Response.json(obj,{status,headers:{'Cache-Control':'no-store'}});
const authCache=new Map();

function db() {
  const conn=process.env.DATABASE_URL;
  if(!conn)throw Error('NEON_DATABASE_REQUIRED');
  const u=new URL(conn);
  if(!['postgres:','postgresql:'].includes(u.protocol)||!u.hostname.endsWith('.neon.tech'))
    throw Error('NEON_DATABASE_HOST_DENIED');
  return {conn,host:'https://api.'+u.hostname.split('.').slice(1).join('.')+'/sql'};
}
async function query(q,params=[]) {
  const d=db();
  const r=await fetch(d.host,{method:'POST',headers:{
    'Content-Type':'application/json','Neon-Connection-String':d.conn,
    'Neon-Raw-Text-Output':'true'
  },body:JSON.stringify({query:q,params}),signal:AbortSignal.timeout(12000)});
  if(!r.ok)throw Error('NEON_QUERY_FAILED');
  const data=await r.json();
  if(!data||!Array.isArray(data.rows))throw Error('NEON_BAD_ROWS');
  return data.rows;
}
async function transaction(queries) {
  const d=db();
  const r=await fetch(d.host,{method:'POST',headers:{
    'Content-Type':'application/json','Neon-Connection-String':d.conn,
    'Neon-Raw-Text-Output':'true','Neon-Batch-Isolation-Level':'ReadCommitted',
  },body:JSON.stringify({queries}),signal:AbortSignal.timeout(12000)});
  if(!r.ok)throw Error('NEON_TRANSACTION_FAILED');
  const data=await r.json();
  if(!Array.isArray(data)||data.length!==queries.length||
     data.some(x=>!Array.isArray(x.rows)))throw Error('NEON_TRANSACTION_BAD_RESPONSE');
  return data.map(x=>x.rows);
}
async function authorized(request) {
  const m=/^Bearer\s+([^\s]+)$/i.exec(request.headers.get('authorization')||'');
  if(!m||m[1].length<25||m[1].length>1000)return false;
  const token=m[1],k=hash(token);
  if(authCache.get(k)>Date.now())return true;
  const headers={'Authorization':'Bearer '+token,
    'User-Agent':'Anthares-X-Neon-Ledger','Accept':'application/vnd.github+json'};
  async function check(path) {
    const r=await fetch('https://api.github.com'+path,{headers,
       signal:AbortSignal.timeout(9500)});
    return r.ok?await r.json():null;
  }
  const user=await check('/user');
  if(String(user?.login||'').toLowerCase()!=='universoanthares')return false;
  const issue=await check('/repos/'+REPO+'/issues/1002');
  if(issue?.number!==1002)return false;
  if(authCache.size>80)authCache.clear();
  authCache.set(k,Date.now()+45000);
  return true;
}
export default {async fetch(request){
  const u=new URL(request.url),action=u.searchParams.get('action')||'';
  if(action==='health'&&request.method==='GET'){
    try {
      const r=await query('SELECT COUNT(*)::int AS confirmed FROM anthares_x_submission_ledger WHERE status=$1',['confirmed']);
      return out(200,{ok:true,backend:'neon',confirmed:Number(r[0]?.confirmed)});
    }catch{return out(503,{ok:false,error:'LEDGER_UNAVAILABLE'});}
  }
  try {
    if(!(await authorized(request)))return out(401,{ok:false,error:'unauthorized'});
    const payload=request.method==='POST'?await request.json():{};
    const key=action==='post-status'?u.searchParams.get('idempotency_key')||'':
      String(payload.idempotency_key||'');
    if(!keyOk(key))return out(400,{ok:false,error:'invalid_key'});
    const rowId=hash('x:'+ACCOUNT+':'+key);
    if(action==='post-status'&&request.method==='GET'){
      const rows=await query(
        'SELECT status,post_url FROM anthares_x_submission_ledger WHERE idempotency_sha256=$1 AND account=$2',
        [rowId,ACCOUNT]);
      const row=rows[0];
      return out(200,{ok:true,status:!row?'NOT_FOUND':row.status==='confirmed'?'CONFIRMED':'UNCERTAIN',
        post_url:row?.status==='confirmed'?row.post_url:null});
    }
    if(action==='claim-local'&&request.method==='POST'){
      if(payload.account!==ACCOUNT)return out(400,{ok:false,error:'account_mismatch'});
      // Lock and write MUST share one read-committed transaction, not separate
      // HTTP requests. The second statement obtains a fresh MVCC snapshot.
      const [_,rows]=await transaction([
        {query:"SELECT pg_advisory_xact_lock(hashtext('anthares-x:lucasyahn:daily'))",params:[]},
        {query:"WITH quota AS (SELECT COUNT(*)::int AS n FROM anthares_x_submission_ledger "+
          "WHERE account=$2 AND status IN ('started','confirmed') AND "+
          "(created_at AT TIME ZONE 'America/Campo_Grande')::date = "+
          "(now() AT TIME ZONE 'America/Campo_Grande')::date), "+
          "ins AS (INSERT INTO anthares_x_submission_ledger (idempotency_sha256,account,status) "+
          "SELECT $1,$2,'started' FROM quota WHERE n<10 ON CONFLICT DO NOTHING "+
          "RETURNING idempotency_sha256) SELECT (SELECT n FROM quota) AS used, "+
          "(SELECT COUNT(*)::int FROM ins) AS inserted",params:[rowId,ACCOUNT]}
      ]);
      const result=rows[0]||{};
      if(Number(result.used)>=10)return out(429,{ok:false,error:'daily_limit_10'});
      if(Number(result.inserted)!==1)return out(409,{ok:false,error:'already_started_reconcile'});
      return out(200,{ok:true,claimed:true,account:ACCOUNT});
    }
    if(action==='confirm-local'&&request.method==='POST'){
      if(payload.account!==ACCOUNT||payload.video_verified!==true||
         payload.caption_verified!==true||!urlOk(String(payload.post_url||'')))
        return out(400,{ok:false,error:'invalid_confirmation'});
      const rows=await query(
        "UPDATE anthares_x_submission_ledger SET status='confirmed',post_url=$1,"+
        "confirmed_at=now() WHERE idempotency_sha256=$2 AND account=$3 "+
        "AND status='started' RETURNING idempotency_sha256",
        [String(payload.post_url),rowId,ACCOUNT]);
      if(rows.length!==1)return out(409,{ok:false,error:'confirmation_conflict'});
      return out(200,{ok:true,confirmed:true,account:ACCOUNT,post_url:payload.post_url,video_verified:true});
    }
    return out(404,{ok:false,error:'unknown_action'});
  }catch{
    return out(503,{ok:false,error:'LEDGER_UNAVAILABLE'});
  }
}};
