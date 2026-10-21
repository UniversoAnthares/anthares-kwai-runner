import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import backend from '../infra/neon-cortes-threads-execution/index.mjs';
const endpoint='https://neon.example.invalid/?action=control';
test('cloud mutation rejects missing GitHub OIDC token',async()=>{
 const response=await backend.fetch(new Request(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:'{"action":"claim"}'}));
 assert.equal(response.status,401);
});
test('cloud mutation rejects forged device identity',async()=>{
 const response=await backend.fetch(new Request(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Anthares-Device':'DESKTOP-FTDK0HP','Authorization':'Bearer fake'},body:'{"action":"ack-pause"}'}));
 assert.equal(response.status,401);
});
test('backend declines arbitrary URL',async()=>{
 const response=await backend.fetch(new Request('https://neon.example.invalid/?action=publish',{method:'POST',body:'{}'}));
 assert.equal(response.status,404);
});
test('local gate permits normal local publishing before cloud handoff',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'threads-cloud-gate-'));
 try{
  const p=path.resolve('tools/threads_cloud_local_gate.mjs');
  const result=spawnSync(process.execPath,[p],{env:{...process.env,CORTES_THREADS_LOCAL_ROOT:root},encoding:'utf8'});
  assert.equal(result.status,0);assert.match(result.stdout,/NOT_ARMED_LOCAL_PRIMARY/);
 }finally{fs.rmSync(root,{recursive:true,force:true})}
});
test('invalid handoff marker prevents uncoordinated local publications',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'threads-cloud-gate-'));
 try{
  fs.writeFileSync(path.join(root,'threads-cloud-handoff-armed.json'),'{"enabled":true}');
  const p=path.resolve('tools/threads_cloud_local_gate.mjs');
  const result=spawnSync(process.execPath,[p],{env:{...process.env,CORTES_THREADS_LOCAL_ROOT:root},encoding:'utf8'});
  assert.equal(result.status,20);assert.match(result.stdout,/INVALID_LOCAL_ARM_MARKER/);
 }finally{fs.rmSync(root,{recursive:true,force:true})}
});
test('cloud publisher cannot post on an automated push event',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 assert.match(src,/THREADS_ALLOW_PUBLISH==='1'/);
 assert.match(src,/GITHUB_EVENT_NAME==='workflow_dispatch'/);
 assert.match(src,/callControl\(jwt,'claim'\)/);
 assert.match(src,/callControl\(jwt,'reserve'/);
 assert.match(src,/callControl\(jwt,'start'/);
 assert.match(src,/callControl\(jwt,'confirm'/);
 assert.match(src,/callControl\(jwt,'uncertain'/);
});
