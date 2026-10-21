import crypto from 'node:crypto';
const TARGET='linkedin:primary',AUD='https://anthares-remote-primary.vercel.app/api/cortes-queue',ISS='https://token.actions.githubusercontent.com';
let jwks=null,at=0;
const output=(o,s=200)=>Response.json(o,{status:s,headers:{'Cache-Control':'no-store'}});
const bad=(s=403,e='denied')=>output({ok:false,error:e},s);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
async function sql(q,p=[]){
 const uri=process.env.DATABASE_URL;if(!uri)throw Error('db_unavailable');
 const u=new URL(uri),d=u.hostname.split('.');
 if(d.length<4||!u.hostname.endsWith('.neon.tech'))throw Error('db_host_invalid');
 const r=await fetch('https://api.'+d.slice(1).join('.')+'/sql',{method:'POST',headers:{'Content-Type':'application/json','Neon-Connection-String':uri,'Neon-Raw-Text-Output':'true'},body:JSON.stringify({query:q,params:p}),signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error('db_http_'+r.status);const v=await r.json();if(!Array.isArray(v.rows))throw Error('db_result');
 for(const x of v.rows){if(typeof x.payload==='string')x.payload=JSON.parse(x.payload);if(typeof x.confirmation_evidence==='string')x.confirmation_evidence=JSON.parse(x.confirmation_evidence);if(x.lease_generation!==undefined)x.lease_generation=Number(x.lease_generation);}
 return {rows:v.rows,count:Number(v.rowCount??v.rows.length)};
}
async function auth(req){
 const m=/^Bearer\s+(.+)$/i.exec(req.headers.get('Authorization')||'');if(!m)return null;
 const seg=m[1].split('.');if(seg.length!==3)return null;let h,c;
 try{h=JSON.parse(Buffer.from(seg[0],'base64url'));c=JSON.parse(Buffer.from(seg[1],'base64url'));}catch{return null;}
 const now=Math.floor(Date.now()/1000);
 if(h.alg!=='RS256'||!h.kid||c.iss!==ISS||c.ref!=='refs/heads/main'||![c.aud].flat().includes(AUD)||c.exp<=now||c.iat>now+60||!['push','schedule','workflow_dispatch'].includes(c.event_name))return null;
 const wf=String(c.job_workflow_ref||c.workflow_ref||'');
 const runner='UniversoAnthares/anthares-kwai-runner',clipper='UniversoAnthares/anthares-clipper';
 const valid=(repo,name)=>c.repository===repo&&wf===repo+'/.github/workflows/'+name+'@refs/heads/main';
 const kind=valid(runner,'cortes-buffer-linkedin-cloud.yml')?'worker':
  valid(runner,'cortes-linkedin-neon-fanout.yml')||valid(clipper,'cortes-buffer-fanout-cloud.yml')?'producer':null;
 if(!kind)return null;
 try{
 if(!jwks||Date.now()>at){
 const cfg=await fetch(ISS+'/.well-known/openid-configuration');if(!cfg.ok)return null;
 const u=(await cfg.json()).jwks_uri;if(!String(u).startsWith(ISS+'/'))return null;
 const r=await fetch(u);if(!r.ok)return null;jwks=await r.json();at=Date.now()+300000;
 }
 const jwk=(jwks.keys||[]).find(x=>x.kid===h.kid&&x.kty==='RSA'&&(!x.alg||x.alg==='RS256'));
 return jwk&&crypto.verify('RSA-SHA256',Buffer.from(seg[0]+'.'+seg[1]),crypto.createPublicKey({key:jwk,format:'jwk'}),Buffer.from(seg[2],'base64url'))?kind:null;
 }catch{return null;}
}
function valid(b){
 if(!b||b.platform!=='linkedin'||b.target_key!==TARGET||b.account_id!=='primary'||b.executor!=='social_video'||b.duration_class!=='short')return false;
 const src=String(b.source_id||''),seg=String(b.segment_id||''),uri=String(b.media_url||'');
 let u;try{u=new URL(uri);}catch{return false;}
 if(!src||!seg||!b.title||b.video_url!==uri||!['anthares.us','www.anthares.us'].includes(u.hostname)||u.protocol!=='https:'||u.username||u.password||!u.pathname.toLowerCase().endsWith('.mp4'))return false;
 if(!(Number(b.duration_seconds)>=30&&Number(b.duration_seconds)<=90)||!(Number(b.cortes_attachment_id)>0))return false;
 if(!Number.isSafeInteger(Number(b.source_start))||!Number.isSafeInteger(Number(b.source_end))||Number(b.source_end)<=Number(b.source_start))return false;
 const id='cortes-fanout-linkedin-'+hash(src+'|'+seg+'|'+TARGET).slice(0,32);
 return b.id===id&&b.dedupe_key===id&&b.media_sha256===hash(src+'|'+seg+'|'+uri)&&b.master_id===src;
}
async function exec(action,b,role){
 if(action==='enqueue'){
 if(role!=='producer'||!valid(b))return {ok:false,error:'invalid_producer'};
 const args=[b.id,b.dedupe_key,TARGET,b.master_id,b.media_sha256,b.source_id,b.source_start,b.source_end,'short',JSON.stringify(b)];
 const r=await sql("INSERT INTO cortes_publications(id,dedupe_key,target_key,master_id,media_sha256,source_id,source_start,source_end,duration_class,payload) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb) ON CONFLICT DO NOTHING RETURNING *",args);
 if(r.count)return{ok:true,deduped:false,job:r.rows[0]};
 const old=await sql('SELECT * FROM cortes_publications WHERE id=$1 OR dedupe_key=$2 LIMIT 2',[b.id,b.dedupe_key]);
 const x=old.rows[0];
 return old.rows.length===1&&x.id===b.id&&x.target_key===TARGET&&x.dedupe_key===b.dedupe_key&&x.media_sha256===b.media_sha256?{ok:true,deduped:true,reason:'identity',job:x}:{ok:false,error:'conflicting_identity'};
 }
 if(role!=='worker')return{ok:false,error:'worker_required'};
 const id=String(b.id||''),owner=String(b.owner||''),gen=Number(b.lease_generation);
 if(action==='buffer-pending'){
 const r=await sql("SELECT id,remote_id,confirmation_evidence FROM cortes_publications WHERE target_key=$1 AND status='uncertain' AND confirmation_evidence->>'kind'='buffer_scheduled' ORDER BY updated_at LIMIT 2",[TARGET]);
 return{ok:true,jobs:r.rows};
 }
 if(action==='buffer-lease'){
 if(b.target_key!==TARGET||!owner.startsWith('buffer-linkedin:'))return{ok:false,error:'wrong_target'};
 const pending=await sql("SELECT count(*)::int AS n FROM cortes_publications WHERE target_key=$1 AND status='uncertain' AND confirmation_evidence->>'kind'='buffer_scheduled'",[TARGET]);
 if(Number(pending.rows[0]?.n||0)>=8)return{ok:true,job:null,buffer_pending_limit:true};
 const q="WITH chosen AS (SELECT id FROM cortes_publications WHERE target_key=$1 AND status='queued' AND (created_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE cortes_publications p SET status='leased',lease_owner=$2,lease_generation=p.lease_generation+1,lease_until=now()+interval '180 seconds',updated_at=now() FROM chosen WHERE p.id=chosen.id RETURNING p.*";
 const r=await sql(q,[TARGET,owner]);return{ok:true,job:r.rows[0]||null};
 }
 if(!id||!owner.startsWith('buffer-linkedin:')||!Number.isInteger(gen)||gen<1)return{ok:false,error:'bad_fence'};
 if(action==='buffer-start'||action==='buffer-fail'){
 const q=action==='buffer-start'?
 "UPDATE cortes_publications SET status='started',publication_started_at=COALESCE(publication_started_at,now()),updated_at=now() WHERE id=$1 AND target_key=$4 AND lease_owner=$2 AND lease_generation=$3 AND status='leased' AND lease_until>now() RETURNING *":
 "UPDATE cortes_publications SET status=CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain' END,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$4 AND lease_owner=$2 AND lease_generation=$3 AND status IN ('leased','started') RETURNING *";
 const r=await sql(q,[id,owner,gen,TARGET]);return r.count?{ok:true,job:r.rows[0]}:{ok:false,error:'bad_fence'};
 }
 if(action==='buffer-scheduled'){
 const remote=String(b.buffer_post_id||'');if(!/^[a-zA-Z0-9_:-]{1,160}$/.test(remote))return{ok:false,error:'bad_remote'};
 const ev={kind:'buffer_scheduled',buffer_post_id:remote,platform:'linkedin',confirmed_on_network:false};
 const r=await sql("UPDATE cortes_publications SET status='uncertain',remote_id=$4,confirmation_evidence=$5::jsonb,lease_until=NULL,lease_owner=NULL,updated_at=now() WHERE id=$1 AND target_key=$6 AND lease_owner=$2 AND lease_generation=$3 AND status='started' RETURNING id,target_key,status,remote_id",[id,owner,gen,remote,JSON.stringify(ev),TARGET]);
 return r.count?{ok:true,job:r.rows[0]}:{ok:false,error:'bad_schedule_fence'};
 }
 if(action==='buffer-reconcile'){
 const remote=String(b.remote_id||''),link=String(b.external_link||'');let u;try{u=new URL(link)}catch{return{ok:false,error:'bad_link'};}
 if(u.protocol!=='https:'||!['www.linkedin.com','linkedin.com'].includes(u.hostname)||!(u.pathname.startsWith('/feed/update/')||u.pathname.startsWith('/posts/')||u.pathname.startsWith('/company/')))return{ok:false,error:'bad_link'};
 const ev={kind:'buffer_linkedin_sent_verified',buffer_post_id:remote,external_link:link,confirmed_on_network:true};
 const r=await sql("UPDATE cortes_publications SET status='confirmed',confirmation_evidence=$3::jsonb,lease_until=NULL,updated_at=now() WHERE id=$1 AND target_key=$4 AND remote_id=$2 AND status='uncertain' AND confirmation_evidence->>'kind'='buffer_scheduled' RETURNING id,status,remote_id",[id,remote,JSON.stringify(ev),TARGET]);
 return r.count?{ok:true,job:r.rows[0]}:{ok:false,error:'not_scheduled'};
 }
 return {ok:false,error:'not_found'};
}
export default {async fetch(request){
 const u=new URL(request.url),action=u.searchParams.get('action');
 if(request.method==='GET'&&action==='health'){
 try{const r=await sql("SELECT count(*)::int AS n FROM cortes_publications WHERE target_key=$1",[TARGET]);return output({ok:true,backend:'neon-cortes-linkedin',database_ok:true,linkedin_jobs:Number(r.rows[0]?.n||0)});}
 catch{return bad(503,'database_unavailable');}
 }
 if(request.method!=='POST'||!['enqueue','buffer-lease','buffer-start','buffer-fail','buffer-scheduled','buffer-pending','buffer-reconcile'].includes(action))return bad(404,'not_found');
 const role=await auth(request);if(!role)return bad(401,'unauthorized');
 let b;try{if(Number(request.headers.get('content-length')||0)>131072)return bad(413,'too_large');b=await request.json();}catch{return bad(400,'invalid_json');}
 try{const r=await exec(action,b,role);return output(r,r.ok?200:409);}catch(e){console.error('FALLBACK_DB_OPERATION',String(e.message||'unknown').replace(/[^a-zA-Z0-9_]/g,'_').slice(0,40));return bad(503,'backend_unavailable');}
}};
