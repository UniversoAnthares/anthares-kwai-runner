import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const script=path.resolve('tools/cortes_threads_continuity_guard.mjs');
test('repeat watchdog invocation deduplicates the same incident and preserves alarm time',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'threads-continuity-'));
 try{
  const id='fOmihuHUT1M|g1:fOmihuHUT1M:9600:9690';
  const now=new Date().toISOString();
  fs.writeFileSync(path.join(root,'threads-ledger.json'),JSON.stringify({lastPublished:now,items:{[id]:{status:'submitting_uncertain',submitAt:now}}}));
  fs.writeFileSync(path.join(root,'manifest-threads.json'),JSON.stringify({items:[{id,date:'2026-10-21'}]}));
  fs.writeFileSync(path.join(root,'threads-scheduler.log'),'healthy');
  const run=()=>spawnSync(process.execPath,[script],{env:{...process.env,CORTES_THREADS_LOCAL_ROOT:root},encoding:'utf8'});
  assert.equal(run().status,0);
  const first=JSON.parse(fs.readFileSync(path.join(root,'threads-continuity-state.json'),'utf8'));
  assert.equal(first.uncertain_count,1);
  assert.ok(first.last_alarm_at);
  assert.equal(run().status,0);
  const second=JSON.parse(fs.readFileSync(path.join(root,'threads-continuity-state.json'),'utf8'));
  assert.equal(second.last_alarm_at,first.last_alarm_at);
  assert.equal(second.last_alarm_fingerprint,first.last_alarm_fingerprint);
  assert.equal(fs.readdirSync(path.join(root,'qa-incidents')).length,1);
 }finally{fs.rmSync(root,{recursive:true,force:true})}
});