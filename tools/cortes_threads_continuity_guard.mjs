// CORTES Threads continuity watchdog. Independent from the publishing worker.
// No browser tabs and no publication attempts originate in this module.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
const root=process.env.CORTES_THREADS_LOCAL_ROOT || path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/,'$1');
const at=n=>path.join(root,n);
const read=(f,fb)=>{try{return JSON.parse(fs.readFileSync(at(f),'utf8').replace(/^\uFEFF/,''))}catch{return fb}};
const stat=n=>{try{return fs.statSync(at(n)).mtimeMs}catch{return 0}};
const atomic=(name,obj)=>{
 const target=at(name),tmp=target+'.tmp-'+process.pid;
 fs.writeFileSync(tmp,JSON.stringify(obj,null,2)+'\n','utf8');fs.renameSync(tmp,target);
};
const now=Date.now(),day=new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Campo_Grande',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
const ledger=read('threads-ledger.json',{items:{}}),manifest=read('manifest-threads.json',{items:[]}), previous=read('threads-continuity-state.json',{});
const rows=Object.values(ledger.items||{});
const currentCount=rows.filter(x=>x.status==='published'&&x.published_at&&new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Campo_Grande',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(x.published_at))===day).length;
const eligible=(manifest.items||[]).filter(x=>x.date>='2026-10-20');
const pending=eligible.filter(x=>!['published','submitting_uncertain'].includes(ledger.items?.[x.id]?.status));
const uncertain=eligible.filter(x=>ledger.items?.[x.id]?.status==='submitting_uncertain');
const freshLog=stat('threads-scheduler.log'),freshEvents=stat('threads-events.log');
const lastSuccess=Date.parse(ledger.lastPublished||'')||0;
const ageLogMin=Math.round((now-freshLog)/60000),ageSuccessMin=lastSuccess?Math.round((now-lastSuccess)/60000):null;
const active=currentCount<100&&pending.length>0;
const problems=[];
if(active && ageLogMin>12)problems.push('SCHEDULER_NO_HEARTBEAT');
if(active && (!lastSuccess||now-lastSuccess>22*60000))problems.push('PUBLICATION_PROGRESS_STALLED');
if(uncertain.length)problems.push('POST_SUBMISSION_RECONCILIATION_REQUIRED');
const recentErrors=(()=>{try{return fs.readFileSync(at('threads-events.log'),'utf8').split(/\r?\n/).slice(-350).filter(line=>{try{const t=Date.parse(line.slice(0,24)),e=JSON.parse(line.slice(25));return now-t<30*60000&&e.action==='ERROR'}catch{return false}}).length}catch{return 0}})();
if(recentErrors>=3)problems.push('RECURRENT_PUBLICATION_ERRORS');
const state={schema:'anthares.threads.continuity.v1',checked_at:new Date(now).toISOString(),day,confirmed_today:currentCount,manifest_count:eligible.length,pending_count:pending.length,uncertain_count:uncertain.length,last_success:ledger.lastPublished||null,age_scheduler_min:ageLogMin,age_success_min:ageSuccessMin,recent_errors_30m:recentErrors,problems,disposition:problems.length?'ATTENTION':'HEALTHY',last_alarm_at:previous.last_alarm_at||null,last_alarm_fingerprint:previous.last_alarm_fingerprint||null,last_recovery_at:previous.last_recovery_at||null,last_browser_recovery_at:previous.last_browser_recovery_at||null};
atomic('threads-continuity-state.json',state);
const critical=problems.some(x=>x==='PUBLICATION_PROGRESS_STALLED'||x==='SCHEDULER_NO_HEARTBEAT'||x==='RECURRENT_PUBLICATION_ERRORS');
const browserRecoveryEligible=recentErrors>=3 && ageSuccessMin!==null && ageSuccessMin>22 &&
 !fs.existsSync(at('threads-worker.lock')) &&
 now-Date.parse(previous.last_browser_recovery_at||0)>45*60000;
if(browserRecoveryEligible && process.argv.includes('--recover')){
 const result=spawnSync('powershell.exe',['-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',at('threads-headless-autoheal.ps1')],{windowsHide:true,timeout:30000,encoding:'utf8'});
 state.browser_recovery={attempted_at:new Date().toISOString(),exit_code:result.status,detail:(result.stderr||'').slice(0,160)};
 if(result.status===0){state.last_browser_recovery_at=state.browser_recovery.attempted_at;}
 atomic('threads-continuity-state.json',state);
}
const canRetry=critical && now-Date.parse(previous.last_recovery_at||0)>25*60000;
if(canRetry && process.argv.includes('--recover')){
 const result=spawnSync('schtasks.exe',['/Run','/TN','Anthares CORTES Threads Browser Publisher'],{windowsHide:true,timeout:12000,encoding:'utf8'});
 state.recovery={attempted_at:new Date().toISOString(),exit_code:result.status,detail:(result.stderr||result.stdout||'').slice(0,300)};
 state.last_recovery_at=state.recovery.attempted_at;
 atomic('threads-continuity-state.json',state);
}
if(problems.length){
 const fingerprint=crypto.createHash('sha256').update(problems.slice().sort().join('|')).digest('hex').slice(0,16);
 const previousAlarm=Date.parse(previous.last_alarm_at||0);
 if(previous.last_alarm_fingerprint!==fingerprint||now-previousAlarm>30*60000){
  const dir=at('qa-incidents');fs.mkdirSync(dir,{recursive:true});
  const incident={priority:critical?'P0':'P1',project:'CORTES',network:'threads',kind:'CONTINUITY_FAILURE',fingerprint,created_at:new Date().toISOString(),state,requires_reconciliation:uncertain.map(x=>x.id),automatic_republish_of_uncertain:false};
  const name='threads-'+new Date().toISOString().replace(/[:.]/g,'-')+'-'+fingerprint+'.json';
  fs.writeFileSync(path.join(dir,name),JSON.stringify(incident,null,2),'utf8');
  state.last_alarm_at=new Date().toISOString();state.last_alarm_fingerprint=fingerprint;
  atomic('threads-continuity-state.json',state);
 }
}
console.log(JSON.stringify({ok:true,...state}));
process.exitCode=critical?2:0;