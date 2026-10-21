import crypto from 'node:crypto';
const DEVICE='DESKTOP-FTDK0HP',TARGET='threads:universoanthares';
const HASH_URL='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices/'+DEVICE+'.sha256';
let cachedHash='',cacheExpires=0;
const respond=(obj,status=200)=>Response.json(obj,{status,headers:{'Cache-Control':'no-store'}});
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
async function authorize(request){
 const h=request.headers.get('x-anthares-device'),token=/^Bearer\s+(.+)$/i.exec(request.headers.get('authorization')||'')?.[1]||'';
 if(h!==DEVICE||token.length<20||token.length>4096)return false;
 if(!cachedHash||Date.now()>cacheExpires){
  const r=await fetch(HASH_URL,{signal:AbortSignal.timeout(8000),headers:{'Cache-Control':'no-cache'}});
  if(!r.ok)return false;
  const value=(await r.text()).trim().toLowerCase();
  if(!/^[0-9a-f]{64}$/.test(value))return false;
  cachedHash=value;cacheExpires=Date.now()+60000;
 }
 const got=Buffer.from(sha(token)),expected=Buffer.from(cachedHash);
 return got.length===expected.length&&crypto.timingSafeEqual(got,expected);
}
async function query(sql,params=[]){
 const conn=process.env.DATABASE_URL;
 if(!conn)throw Error('DATABASE_CONFIG_MISSING');
 const db=new URL(conn);
 if(!['postgresql:','postgres:'].includes(db.protocol)||!db.hostname.endsWith('.neon.tech'))throw Error('DATABASE_URL_INVALID');
 const host='https://api.'+db.hostname.split('.').slice(1).join('.')+'/sql';
 const r=await fetch(host,{method:'POST',headers:{'Content-Type':'application/json','Neon-Connection-String':conn,'Neon-Raw-Text-Output':'true'},body:JSON.stringify({query:sql,params}),signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error('NEON_QUERY_'+r.status);
 const obj=await r.json();if(!Array.isArray(obj.rows))throw Error('NEON_RESPONSE_INVALID');
 return obj.rows;
}
function validate(entries){
 if(!Array.isArray(entries)||!entries.length||entries.length>150)return 'INVALID_BATCH';
 const seen=new Set();
 for(const row of entries){
  if(!row||typeof row!=='object'||Array.isArray(row))return 'INVALID_ROW';
  if(!/^threads:[A-Za-z0-9_-]{11}\|g[0-9]+:[A-Za-z0-9_-]{11}:[0-9]+:[0-9]+$/.test(row.id||'')||seen.has(row.id))return 'INVALID_ID';
  seen.add(row.id);
  if(!['confirmed','uncertain'].includes(row.status))return 'INVALID_STATUS';
  if(row.status==='uncertain'&&row.post_url)return 'UNCERTAIN_CANNOT_CLAIM_PUBLIC_URL';
  if(row.status==='confirmed'){
   let url;try{url=new URL(row.post_url||'')}catch{return 'INVALID_POST_URL'}
   if(url.protocol!=='https:'||!['www.threads.com','threads.com'].includes(url.hostname)||
      !/^\/@universoanthares\/post\/[A-Za-z0-9_-]+\/?$/.test(url.pathname)||
      url.username||url.password||url.port||url.search||url.hash)return 'INVALID_ACCOUNT_OR_POST_URL';
  }
 }
 return null;
}
const UPSERT=[
"WITH input AS (SELECT v->>'id' id,v->>'status' next_status,v->>'post_url' post_url FROM jsonb_array_elements($1::jsonb) AS v),",
"changed AS (UPDATE cortes_publications p SET status=i.next_status,",
"remote_id=CASE WHEN i.next_status='confirmed' THEN i.post_url ELSE p.remote_id END,",
"confirmation_evidence=CASE WHEN i.next_status='confirmed' THEN jsonb_build_object('kind','threads_local_profile_verified','public_url',i.post_url,'verified_by_device','DESKTOP-FTDK0HP','synchronized_at',now()) ELSE p.confirmation_evidence END,",
"publication_started_at=CASE WHEN i.next_status='uncertain' THEN COALESCE(p.publication_started_at,now()) ELSE p.publication_started_at END,",
"lease_until=NULL,lease_owner=NULL,updated_at=now() FROM input i",
"WHERE p.id=i.id AND p.target_key=$2 AND p.status IN ('queued','uncertain')",
"AND (p.remote_id IS NULL OR p.remote_id=i.post_url OR i.next_status='uncertain') RETURNING p.id)",
"SELECT id FROM changed"
].join(' ');
async function sync(body){
 const err=validate(body?.entries);
 if(err)return{ok:false,error:err};
 const rows=await query(UPSERT,[JSON.stringify(body.entries),TARGET]);
 const changed=new Set(rows.map(r=>r.id));
 const remaining=body.entries.filter(x=>!changed.has(x.id));
 const statuses=remaining.length?await query('SELECT id,status,remote_id FROM cortes_publications WHERE target_key=$1 AND id=ANY($2::text[])',[TARGET,remaining.map(x=>x.id)]):[];
 const found=new Map(statuses.map(r=>[r.id,r]));
 let already_confirmed=0;const conflicts=[];
 for(const item of remaining){
  const previous=found.get(item.id);
  if(previous?.status==='confirmed'&&item.status==='confirmed'&&previous.remote_id===item.post_url)already_confirmed++;
  else if(previous?.status==='uncertain'&&item.status==='uncertain')continue;
  else conflicts.push({id:item.id,reason:previous?'STATUS_OR_EVIDENCE_CONFLICT':'NOT_ENQUEUED'});
 }
 return{ok:true,target_key:TARGET,updated:changed.size,already_confirmed,conflicts};
}
export default{async fetch(request){
 const u=new URL(request.url),action=u.searchParams.get('action');
 if(request.method==='GET'&&u.pathname==='/health')return respond({ok:true,service:'anthares-threads-neon-reconciliation',posts_sent:0});
 if(request.method!=='POST'||!['threads-ledger-sync','sync'].includes(action))return respond({ok:false,error:'NOT_FOUND'},404);
 if(Number(request.headers.get('content-length')||0)>100000)return respond({ok:false,error:'TOO_LARGE'},413);
 try{if(!(await authorize(request)))return respond({ok:false,error:'UNAUTHORIZED'},401)}
 catch{return respond({ok:false,error:'DEVICE_AUTH_UNAVAILABLE'},503)}
 let body;try{body=await request.json()}catch{return respond({ok:false,error:'INVALID_JSON'},400)}
 if(JSON.stringify(body).length>100000)return respond({ok:false,error:'TOO_LARGE'},413);
 try{const result=await sync(body);return respond(result,result.ok?200:409)}
 catch(e){return respond({ok:false,error:'DATABASE_UNAVAILABLE',class:e?.name||'Error'},503)}
}};