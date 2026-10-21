import crypto from 'node:crypto';
const TARGET='threads:universoanthares';
const DEVICE='DESKTOP-FTDK0HP';
const HASH_URL='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices/'+DEVICE+'.sha256';
let hashCache='',hashCacheUntil=0;
function answer(data,status=200){return Response.json(data,{status,headers:{'Cache-Control':'no-store'}})}
function validUrl(value){
 try{
  const u=new URL(value);
  return u.protocol==='https:'&&['threads.com','www.threads.com'].includes(u.hostname)&&
    /^\/@universoanthares\/post\/[A-Za-z0-9_-]+\/?$/.test(u.pathname)&&
    !u.username&&!u.password&&!u.port&&!u.search&&!u.hash;
 }catch{return false}
}
async function authorized(request){
 if(request.headers.get('x-anthares-device')!==DEVICE)return false;
 const match=/^Bearer\s+(.+)$/i.exec(request.headers.get('authorization')||'');
 if(!match||match[1].length<16||match[1].length>4000)return false;
 if(!hashCache||Date.now()>hashCacheUntil){
  const r=await fetch(HASH_URL,{signal:AbortSignal.timeout(9000),headers:{'User-Agent':'AntharesCortesThreadsNeonSync/1.0','Cache-Control':'no-cache'}});
  if(!r.ok)return false;
  const v=(await r.text()).trim().toLowerCase();
  if(!/^[a-f0-9]{64}$/.test(v))return false;
  hashCache=v;hashCacheUntil=Date.now()+60000;
 }
 const got=crypto.createHash('sha256').update(match[1]).digest('hex');
 const a=Buffer.from(hashCache,'hex'),b=Buffer.from(got,'hex');
 return a.length===b.length&&crypto.timingSafeEqual(a,b);
}
async function query(sql,params=[]){
 const c=process.env.DATABASE_URL||'';
 if(!c)throw Error('DATABASE_URL_MISSING');
 const u=new URL(c);
 if(!['postgresql:','postgres:'].includes(u.protocol)||!u.hostname.endsWith('.neon.tech'))throw Error('DATABASE_URL_INVALID');
 const endpoint='https://api.'+u.hostname.split('.').slice(1).join('.')+'/sql';
 const r=await fetch(endpoint,{method:'POST',
 headers:{'Content-Type':'application/json','Neon-Connection-String':c,'Neon-Raw-Text-Output':'true'},
 body:JSON.stringify({query:sql,params}),signal:AbortSignal.timeout(15000)});
 if(!r.ok)throw Error('NEON_SQL_HTTP_'+r.status);
 const json=await r.json();
 if(!Array.isArray(json.rows))throw Error('NEON_SQL_INVALID_RESPONSE');
 return json.rows;
}
const UPDATE_SQL=`WITH incoming AS (
 SELECT x.id,x.status,x.post_url FROM jsonb_to_recordset($1::jsonb) AS x(id text,status text,post_url text)
), updated AS (
 UPDATE cortes_publications p
 SET status=CASE WHEN i.status='confirmed' THEN 'confirmed' ELSE 'uncertain' END,
 remote_id=CASE WHEN i.status='confirmed' THEN i.post_url ELSE p.remote_id END,
 confirmation_evidence=CASE WHEN i.status='confirmed'
    THEN jsonb_build_object('kind','threads_local_profile_verified','public_url',i.post_url,'verified_by_device','DESKTOP-FTDK0HP','sync_at',now())
    ELSE p.confirmation_evidence END,
 publication_started_at=CASE WHEN i.status='uncertain' THEN coalesce(p.publication_started_at,now()) ELSE p.publication_started_at END,
 updated_at=now()
 FROM incoming i
 WHERE p.id=i.id AND p.target_key='threads:universoanthares'
   AND ((p.status='queued' AND i.status='uncertain') OR (p.status IN ('queued','uncertain') AND i.status='confirmed'))
 RETURNING p.id
)
SELECT i.id, i.status AS requested, i.post_url AS requested_url,
 p.status AS actual, p.remote_id AS actual_url, (u.id IS NOT NULL) AS changed
FROM incoming i
LEFT JOIN updated u ON u.id=i.id
LEFT JOIN cortes_publications p ON p.id=i.id AND p.target_key='threads:universoanthares'
ORDER BY i.id`;
export default {async fetch(request){
 const url=new URL(request.url),action=url.searchParams.get('action')||'';
 if(request.method==='GET'&&action==='health'){
  try{await query('SELECT 1 AS ok');return answer({ok:true,backend:'neon-functions-threads',database_ok:true,device_scoped:true,publishes_media:false})}
  catch{return answer({ok:false,backend:'neon-functions-threads',database_ok:false},503)}
 }
 if(request.method!=='POST'||!['threads-ledger-sync','stats'].includes(action))return answer({ok:false,error:'NOT_FOUND'},404);
 try{if(!await authorized(request))return answer({ok:false,error:'UNAUTHORIZED'},401)}
 catch{return answer({ok:false,error:'AUTH_BACKEND_UNAVAILABLE'},503)}
 let data;try{
  const raw=await request.text();
  if(raw.length>65000)return answer({ok:false,error:'PAYLOAD_TOO_LARGE'},413);
  data=JSON.parse(raw);
 }catch{return answer({ok:false,error:'INVALID_JSON'},400)}
 try{
  if(action==='stats'){
   if(data?.target_key!==TARGET)return answer({ok:false,error:'TARGET_FORBIDDEN'},403);
   const rows=await query('SELECT status,count(*)::int AS count FROM cortes_publications WHERE target_key=$1 GROUP BY status',[TARGET]);
   return answer({ok:true,target_key:TARGET,counts:Object.fromEntries(rows.map(x=>[x.status,Number(x.count)]))});
  }
  const entries=Array.isArray(data?.entries)?data.entries:null;
  if(!entries||entries.length<1||entries.length>120)return answer({ok:false,error:'INVALID_BATCH'},400);
  const ids=new Set(),normalized=[];
  for(const row of entries){
   const id=String(row?.id||''),status=String(row?.status||''),post_url=String(row?.post_url||'');
   if(!/^threads:[A-Za-z0-9_-]{11}\|g\d+:[A-Za-z0-9_-]{11}:\d+:\d+$/.test(id)||
       ids.has(id)||!['confirmed','uncertain'].includes(status)||
       (status==='confirmed'&&!validUrl(post_url))||(status==='uncertain'&&post_url))
     return answer({ok:false,error:'INVALID_THREADS_ID_OR_EVIDENCE'},400);
   ids.add(id);normalized.push({id,status,post_url});
  }
  const rows=await query(UPDATE_SQL,[JSON.stringify(normalized)]);
  const result={ok:true,target_key:TARGET,confirmed:0,uncertain:0,already_confirmed:0,conflicts:[]};
  for(const row of rows){
   if(row.requested==='confirmed'&&row.actual==='confirmed'&&row.actual_url===row.requested_url){
    if(String(row.changed)==='true')result.confirmed++;else result.already_confirmed++;
   }else if(row.requested==='uncertain'&&row.actual==='uncertain')result.uncertain++;
   else result.conflicts.push({id:row.id,reason:row.actual?'current_status_'+row.actual:'not_enqueued'});
  }
  return answer(result);
 }catch{return answer({ok:false,error:'THREADS_SYNC_BACKEND_UNAVAILABLE'},503)}
}};
