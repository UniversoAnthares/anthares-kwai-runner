import fs from 'node:fs';
import path from 'node:path';
const root=process.env.CORTES_THREADS_LOCAL_ROOT||'D:\\AntharsWork\\cortes-social-browser-20261020';
const marker=path.join(root,'threads-cloud-handoff-armed.json');
const ledgerFile=path.join(root,'threads-ledger.json');
const stateFile=path.join(root,'threads-cloud-handoff-local-status.json');
const remote='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/?action=gate';
const atomic=(file,data)=>{const tmp=file+'.tmp-'+process.pid;fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n','utf8');fs.renameSync(tmp,file)};
function report(result){atomic(stateFile,{at:new Date().toISOString(),...result});console.log('THREADS_CLOUD_LOCAL_GATE='+JSON.stringify(result))}
async function main(){
 if(!fs.existsSync(marker)){console.log('THREADS_CLOUD_LOCAL_GATE=NOT_ARMED_LOCAL_PRIMARY');return}
 const armed=JSON.parse(fs.readFileSync(marker,'utf8').replace(/^\uFEFF/,''));
 if(!armed||armed.enabled!==true||!Number.isSafeInteger(Number(armed.epoch_at_arm))){
  report({allow:false,reason:'INVALID_LOCAL_ARM_MARKER'});process.exitCode=20;return
 }
 let snapshot;
 try{
  const result=await fetch(remote,{signal:AbortSignal.timeout(10000)});
  if(!result.ok)throw Error('HTTP_'+result.status);
  snapshot=await result.json();
  if(!snapshot.ok||!['local','cloud'].includes(snapshot.owner)||!Array.isArray(snapshot.confirmed)||
     !Number.isSafeInteger(Number(snapshot.epoch))||!Number.isFinite(Number(snapshot.cloud_inflight)))
   throw Error('INVALID_CLOUD_GATE_DATA');
 }catch(e){report({allow:false,reason:'NEON_GATE_UNREACHABLE',error:String(e.message).slice(0,90)});process.exitCode=20;return}
 // Reconciling cloud-confirmed public URLs precedes every possible local resumption.
 let ledger;
 try{ledger=JSON.parse(fs.readFileSync(ledgerFile,'utf8').replace(/^\uFEFF/,''));if(!ledger.items)throw Error('NO_LEDGER_ITEMS')}
 catch{report({allow:false,reason:'LOCAL_LEDGER_UNAVAILABLE'});process.exitCode=20;return}
 let changed=0;
 for(const record of snapshot.confirmed){
  const id=String(record.id||''),url=String(record.url||'');
  if(!/^threads:[A-Za-z0-9_-]{11}\|g[0-9]+:[A-Za-z0-9_-]{11}:[0-9]+:[0-9]+$/.test(id))continue;
  if(!/^https:\/\/(www\.)?threads\.com\/@universoanthares\/post\/[A-Za-z0-9_-]+\/?$/.test(url))continue;
  const key=id.slice('threads:'.length);
  const old=ledger.items[key]||{};
  if(old.status==='published'&&old.url===url)continue;
  if(old.status==='published'&&old.url!==url){
   report({allow:false,reason:'REMOTE_LOCAL_CONFIRMATION_CONFLICT',id});process.exitCode=20;return;
  }
  ledger.items[key]={...old,status:'published',url,published_at:new Date().toISOString(),confirmation_method:'cloud_neon_graph_verification'};
  changed++;
 }
 if(changed){ledger.lastPublished=new Date().toISOString();atomic(ledgerFile,ledger)}
 const cloudActive=snapshot.owner==='cloud';
 const unknown=Number(snapshot.cloud_inflight)>0;
 const previouslyClaimed=Number(snapshot.epoch)>Number(armed.epoch_at_arm);
 const ackExpired=Date.now()>Date.parse(armed.expires_at);
 const mayResume=!cloudActive&&!unknown&&(previouslyClaimed||ackExpired);
 if(mayResume){
  fs.unlinkSync(marker);
  report({allow:true,reason:previouslyClaimed?'CLOUD_RELEASED_AND_RECONCILED':'HANDOFF_ACK_EXPIRED_WITHOUT_CLAIM',reconciled:changed,epoch:snapshot.epoch});
  return;
 }
 report({allow:false,reason:cloudActive?'CLOUD_LEASE_ACTIVE':unknown?'CLOUD_SUBMISSION_UNRESOLVED':'HANDOFF_WINDOW_ACTIVE',reconciled:changed,epoch:snapshot.epoch});
 process.exitCode=20;
}
main().catch(e=>{report({allow:false,reason:'GATE_UNHANDLED',error:String(e.message).slice(0,120)});process.exitCode=20});
