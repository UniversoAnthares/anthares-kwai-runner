import test from 'node:test';
import {runInNewContext} from 'node:vm';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
const times=(s,x)=>s.split(x).length-1;

test('both account lease paths enforce the canonical verified Kwai gate',()=>{
 assert.equal(times(source,"const pacing=await kwaiDeadlinePacing(String(b.target_key||''),100);"),2);
 assert.equal(times(source,'async function kwaiDeadlinePacing('),1);
 assert.equal(times(source,"const pacing=await cortesDeadlinePacing(String(b.target_key||''),100);"),0);
});
test('both account stats paths report the same verified clock used by lease',()=>{
 assert.equal(times(source,'const pacing=await kwaiDeadlinePacing(KWAI_TARGET,100);'),2);
 assert.equal(times(source,'return {ok:true,...pacing,states:rows};'),2);
});
test('verified Kwai time is anchored to actual published media, never update timestamps',()=>{
 const beginning=source.indexOf('async function kwaiDeadlinePacing(');
 const ending=source.indexOf('async function cortesDeadlinePacing(',beginning);
 assert.ok(beginning>=0&&ending>beginning);
 const gate=source.slice(beginning,ending);
 assert.match(gate,/confirmation_evidence->>'public_post_timestamp_ms'/);
 assert.match(gate,/publication_started_at/);
 assert.doesNotMatch(gate,/updated_at/);
 assert.match(gate,/deriveKwaiPacing/);
});
test('Neon lease eligibility excludes duplicates and unresolved posts',()=>{
 const gate=source.slice(source.indexOf('async function kwaiDeadlinePacing('),
   source.indexOf('async function cortesDeadlinePacing('));
 assert.match(gate,/status IN \('leased','started','confirmed','uncertain'\)/);
 assert.match(gate,/status='queued'/);
 assert.match(gate,/source_start/);
 assert.match(gate,/source_end/);
});

test('Neon computes 06:00 open in America/Campo_Grande and passes it to both account gates',()=>{
 const a=source.indexOf('async function kwaiDeadlinePacing(');
 const z=source.indexOf('async function cortesDeadlinePacing(',a);
 const gate=source.slice(a,z);
 assert.match(gate,/interval '6 hours'/);
 assert.match(gate,/AT TIME ZONE 'America\/Campo_Grande'/);
 assert.match(gate,/AS open_at/);
 assert.match(gate,/b\.open_at AS window_open_at/);
 assert.match(gate,/window_open_at:row\.window_open_at/);
 assert.match(gate,/GROUP BY e\.n,b\.clock,b\.open_at,b\.end_at/);
 const policy=readFileSync(new URL('./kwai-pacing-policy.mjs',import.meta.url),'utf8');
 assert.match(policy,/if\(time<open\)\{result\.status='WAIT_OPEN'/);
 // Both lease routes require DUE, so WAIT_OPEN authorizes no job.
 const kwaiGate=/const pacing=await kwaiDeadlinePacing\(String\(b\.target_key\|\|''\),100\);\s*if\(pacing\.status!=='DUE'\)return\{ok:true,job:null,pacing\};/g;
 assert.equal([...source.matchAll(kwaiGate)].length,2);
});

test('both Kwai START transitions recheck 06h-23h inside atomic PostgreSQL UPDATE',()=>{
 const main=source.slice(source.indexOf('async function kwaiAction('),
                         source.indexOf('async function kwaiUnprovenAction('));
 const secondary=source.slice(source.indexOf('async function kwaiSecondaryAction('),
                              source.indexOf('async function cortesAction(',source.indexOf('async function kwaiSecondaryAction(')));
 for(const account of [main,secondary]){
   const start=account.indexOf("if(action==='kwai-start')");
   assert.ok(start>=0);
   const end=account.indexOf("if(action==='kwai-confirm')",start);
   assert.ok(end>start);
   const sql=account.slice(start,end);
   assert.match(sql,/WHERE p\.id=\$1 AND p\.target_key=\$2 AND p\.status='leased'/);
   assert.match(sql,/AND p\.publication_started_at IS NULL/);
   assert.match(sql,/AND p\.lease_generation=\$4 AND p\.lease_until>now\(\)/);
   assert.match(sql,/AT TIME ZONE 'America\/Campo_Grande'\)\:\:time >= time '06:00'/);
   assert.match(sql,/AT TIME ZONE 'America\/Campo_Grande'\)\:\:time < time '23:00'/);
   assert.equal((sql.match(/RETURNING p\.id,p\.status,p\.lease_generation/g)||[]).length,1);
 }
});


test('terminal ACK read is physical-RSA-only, account scoped and never writes SQL',async()=>{
 const a=source.indexOf('async function kwaiTerminalAckRead(');
 const z=source.indexOf('// Verified public timestamps',a);
 assert.ok(a>=0&&z>a);
 const handler=source.slice(a,z);
 assert.equal((source.match(/if\(action==='kwai-job-terminal-read'\)return kwaiTerminalAckRead\(b,actor,KWAI_TARGET\);/g)||[]).length,2);
 let lookup=[],row=null;
 const query=async(sql,args)=>{
   assert.match(sql,/^SELECT id,status,lease_generation/);
   assert.doesNotMatch(sql,/\bUPDATE\b|\bDELETE\b|\bINSERT\b/);
   lookup.push(args);
   return row?[row]:[];
 };
 const fn=runInNewContext(handler+';kwaiTerminalAckRead',{query});
 const auth={role:'kwai-physical',workflow:'physical:DESKTOP-FTDK0HP'};
 const id='kwai-cortes-ua-217fddfeae7c0a86be66d8e8511e2916';
 const request={id,lease_generation:1};
 const valid={id,status:'confirmed',lease_generation:1,lease_owner:null,
   remote_id:'https://www.kwai.com/@universoanthares/video/5244028928629526188',
   proof_kind:'kwai_three_public_sift_oidc_reconciled_v1',wp_callback_state:'completed'};
 row=valid;
 let receipt=await fn(request,auth,'kwai:universoanthares');
 assert.equal(receipt.terminal,'confirmed');
 assert.equal(lookup[0][1],'kwai:universoanthares');
 assert.equal((await fn(request,{role:'kwai-mobile',workflow:'mobile:M2004J19C:universoanthares'},'kwai:universoanthares')).ok,false);
 assert.equal((await fn({...request,lease_generation:2},auth,'kwai:universoanthares')).ok,false);
 row={...valid,remote_id:'https://www.kwai.com/@lucasrosalem/video/5244028928629526188'};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,null);
 row={...valid,status:'uncertain'};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,null);
 row={...valid,wp_callback_state:null};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,null);
 row={...valid,lease_owner:'physical_android:DESKTOP-FTDK0HP'};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,null);
 row={...valid,status:'cancelled',remote_id:null,lease_owner:null,
   proof_kind:'kwai_reconcile_then_disregard_v1',wp_callback_state:null};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,'cancelled');
 row={...row,proof_kind:'unverified_user_claim'};
 assert.equal((await fn(request,auth,'kwai:universoanthares')).terminal,null);
 assert.equal((await fn({id:'evil',lease_generation:1},auth,'kwai:universoanthares')).ok,false);
 assert.match(source,/kwai-job-terminal-read/);
});
