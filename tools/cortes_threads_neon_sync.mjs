// Periodic one-way reconciliation: authoritative local Threads ledger -> Neon queue.
// The script never clicks Post and never retries uncertain publications.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=process.env.CORTES_THREADS_LOCAL_ROOT||'D:\\AntharsWork\\cortes-social-browser-20261020';
const token=process.env.ANTHARES_DEVICE_TOKEN||'';
const base='https://anthares-remote-primary.vercel.app/api/cortes-queue';
const neonSync='https://br-crimson-unit-b89nau08-threadsync.compute.c-14.us-east-1.aws.neon.tech/';
const target='threads:universoanthares';
const read=n=>{try{return JSON.parse(fs.readFileSync(path.join(root,n),'utf8').replace(/^\uFEFF/,''))}catch{return {}}};
const write=(n,data)=>{const f=path.join(root,n),tmp=f+'.tmp-'+process.pid;fs.writeFileSync(tmp,JSON.stringify(data,null,2),'utf8');fs.renameSync(tmp,f)};
const ledger=read('threads-ledger.json'),manifest=read('manifest-threads.json');
const previous=read('threads-neon-sync-state.json'),fingerprints=previous.fingerprints||{};
const known=read('threads-neon-known-manifest.json');
const existing=new Set(known.ids||[]);
async function call(action,data){
 if(!token||token.length<8)throw Error('DEVICE_AUTH_UNAVAILABLE');
 const uri=action==='threads-ledger-sync'?neonSync:base;
 const response=await fetch(uri+'?action='+encodeURIComponent(action),{
  method:'POST',headers:{'Authorization':'Bearer '+token,'X-Anthares-Device':'DESKTOP-FTDK0HP','Content-Type':'application/json'},
  body:JSON.stringify(data),signal:AbortSignal.timeout(30000)
 });
 const result=await response.json().catch(()=>({}));
 if(!response.ok||!result.ok)throw Error('QUEUE_'+action+'_HTTP_'+response.status+'_'+String(result.error||'unknown'));
 return result;
}
const status={checked_at:new Date().toISOString(),mode:'device_scoped_neon_reconciliation',local_only:false,ready:false,unsynced:0,enqueued:0,reconciled:0,conflicts:[]};
try{
 if(!Array.isArray(manifest.items)||!manifest.items.length)throw Error('EMPTY_MANIFEST');
 // Hash NEW media once, using the actual bytes, before enqueuing.
 for(const item of manifest.items){
  if(existing.has(item.id))continue;
  const match=/^g\d+:([A-Za-z0-9_-]{11}):(\d+):(\d+)$/.exec(item.clip_id||'');
  if(!match||match[1]!==item.source)throw Error('INVALID_NEW_MEDIA_SEGMENT');
  if(!/^https:\/\/anthares\.us\/.*\.mp4(?:\?.*)?$/.test(item.url||''))throw Error('INVALID_NEW_MEDIA_URL');
  const response=await fetch(item.url,{signal:AbortSignal.timeout(60000)});
  if(!response.ok||!response.body)throw Error('NEW_MEDIA_DOWNLOAD_HTTP_'+response.status);
  const digester=crypto.createHash('sha256');let size=0;
  for await(const buffer of response.body){size+=buffer.length;if(size>60e6)throw Error('MEDIA_TOO_LARGE');digester.update(buffer)}
  if(size<100000||size!==Number(item.size))throw Error('NEW_MEDIA_SIZE_MISMATCH');
  await call('enqueue',{id:'threads:'+item.id,dedupe_key:target+'|'+item.id,target_key:target,master_id:item.id,media_sha256:digester.digest('hex'),source_id:item.source,
   source_start:Number(match[2]),source_end:Number(match[3]),duration_class:'short',
   media_url:item.url,video_url:item.url,clip_id:item.clip_id,source_day:item.date});
  existing.add(item.id);status.enqueued++;
  write('threads-neon-known-manifest.json',{ids:[...existing],updated_at:new Date().toISOString()});
 }
 const updates=[],map=new Map();
 for(const [key,entry] of Object.entries(ledger.items||{})){
  const value=entry.status==='published'?{status:'confirmed',post_url:entry.url}:entry.status==='submitting_uncertain'?{status:'uncertain',post_url:''}:null;
  if(!value)continue;
  const id='threads:'+key;
  const fingerprint=value.status+'|'+value.post_url;
  if(fingerprints[id]===fingerprint)continue;
  updates.push({id,...value,submitted_at:entry.submitAt||''});
  map.set(id,fingerprint);
 }
 status.unsynced=updates.length;
 for(let index=0;index<updates.length;index+=100){
  const batch=updates.slice(index,index+100);
  const result=await call('threads-ledger-sync',{entries:batch});
  const conflicts=new Set((result.conflicts||[]).map(x=>x.id));
  for(const entry of batch){if(!conflicts.has(entry.id))fingerprints[entry.id]=map.get(entry.id)}
  status.reconciled+=(result.confirmed||0)+(result.already_confirmed||0)+(result.uncertain||0);
  status.conflicts.push(...(result.conflicts||[]));
  write('threads-neon-sync-state.json',{...status,fingerprints});
 }
 status.ready=true;
 status.unsynced=Object.keys(map).filter(id=>fingerprints[id]!==map.get(id)).length;
}catch(err){status.error=String(err.message||err).slice(0,250);process.exitCode=2}
finally{write('threads-neon-sync-state.json',{...status,fingerprints});console.log(JSON.stringify(status))}