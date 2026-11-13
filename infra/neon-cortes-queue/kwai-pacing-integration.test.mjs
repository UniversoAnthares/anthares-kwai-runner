import test from 'node:test';
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
 assert.equal(times(source,"if(pacing.status!=='DUE')return{ok:true,job:null,pacing};"),2);
});
