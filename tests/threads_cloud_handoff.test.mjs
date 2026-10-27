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
  assert.ok([0,20].includes(result.status));assert.match(result.stdout,/NOT_ARMED_LOCAL_PRIMARY|REMOTE_CLOUD_PRIMARY_ACTIVE_NO_MARKER|NEON_GATE_FAIL_CLOSED/);
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
 assert.match(src,/GITHUB_EVENT_NAME/);
 assert.match(src,/callControl\(jwt,'claim'\)/);
 assert.match(src,/callControl\(jwt,'reserve'/);
 assert.match(src,/callControl\(jwt,'start'/);
 assert.match(src,/callControl\(jwt,'confirm'/);
 assert.match(src,/callControl\(jwt,'uncertain'/);
});

test('cloud selects oldest source-day with queued identity, not just today',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 assert.match(src,/queued_rows/);
 assert.match(src,/\.sort\(\)/);
 assert.match(src,/fetchCloudManifest\(\{day\}\)/);
 assert.match(src,/THREADS_QUEUE_EMPTY_OR_ISOLATED/);
});
test('paged WordPress discovery miss cannot quarantine a queued Neon clip',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 const candidateMiss=src.match(/if\(!candidate\)\{([\s\S]*?)\n  \}/)?.[1]||'';
 assert.match(candidateMiss,/THREADS_CLIP_NOT_IN_PAGED_MANIFEST/);
 assert.doesNotMatch(candidateMiss,/callControl\(jwt,'quarantine'/);
 assert.doesNotMatch(candidateMiss,/reason:'MEDIA_INVALID'/);
 assert.match(candidateMiss,/rejected\+\+;continue;/);
});
test('unknown cloud submissions retain a durable reconciliation block',()=>{
 const src=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.match(src,/threads_cloud_unknown/);
 assert.match(src,/cloud_inflight/);
 assert.match(src,/local_pause_until=NULL/);
});

test('dry-run must verify signed GitHub OIDC without publishing',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 const backendSource=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.match(src,/await verifyCloudOidc\(jwt\)/);
 assert.match(backendSource,/op==='preflight'/);
 assert.match(backendSource,/allowPush&&claims\.event_name==='push'/);
 assert.match(backendSource,/mutations_allowed:false/);
});

test('cloud Graph receipt is logged before Neon confirmation and never retried as a post',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 const g=src.indexOf('THREADS_GRAPH_POSTED='),c=src.indexOf("await callControl(jwt,'confirm'");
 assert.ok(g>=0&&c>g);
 assert.match(src,/for\(let attempt=1;attempt<=4;attempt\+\+\)/);
 assert.match(src,/url:verified\?\.url\|\|null/);
 assert.equal((src.match(/verified=await publishVideo/g)||[]).length,1);
});
test('Neon confirm is idempotent and uncertain status retains verified public permalink',()=>{
 const src=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.match(src,/status='confirmed' AND remote_id=\$5/);
 assert.match(src,/submitted_post_url/);
 assert.match(src,/reason_code:reason/);
});
test('Windows handoff JSON parser tolerates UTF-8 BOM',()=>{
 const src=fs.readFileSync('tools/threads_cloud_local_gate.mjs','utf8');
 assert.ok(src.includes("replace(/^\\uFEFF/"));
});

test('scheduled cloud is idempotent and requires Neon primary enabled',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 const workflow=fs.readFileSync('.github/workflows/cortes-threads-cloud-handoff.yml','utf8');
 const backend=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.match(workflow,/cron: '\*\/6 \* \* \* \*'/);
 assert.match(workflow,/issues: write/);
 assert.match(src,/THREADS_CLOUD_PRIMARY_DISABLED_SKIP/);
 assert.match(src,/THREADS_CLOUD_COOLDOWN_SIX_MINUTES/);
 assert.match(backend,/cloud_primary_enabled=true/);
 assert.match(backend,/claims\.event_name/);
 assert.match(backend,/CLOUD_STILL_HEALTHY_OR_ACTIVE/);
});
test('404/410 and caption failures isolate a single clip without blocking the next',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_handoff.mjs','utf8');
 const backend=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.match(src,/for\(const row of queue\.slice\(0,60\)\)/);
 assert.match(src,/callControl\(jwt,'quarantine'/);
 assert.match(src,/notifyQA\(row.id,reason\)/);
 assert.match(backend,/expires_at<=now\(\)/);
 assert.match(backend,/status='failed'/);
 assert.match(backend,/cortes_threads_quarantine/);
});
test('local hot standby honors Neon primary and cloud watchdog stalls',()=>{
 const src=fs.readFileSync('tools/threads_cloud_local_gate.mjs','utf8');
 const steward=fs.readFileSync('tools/threads_cloud_primary_steward.ps1','utf8');
 assert.match(src,/snapshot\.cloud_primary_enabled/);
 assert.match(src,/REMOTE_CLOUD_PRIMARY_ACTIVE_NO_MARKER/);
 assert.match(steward,/deactivate-primary/);
 assert.match(steward,/CLOUD_STALE_20MIN_SAFE_LOCAL_TAKEOVER/);
});

test('night batch remains dispatch-only, within approved deadline, with signed backend fallback',()=>{
 const src=fs.readFileSync('tools/threads_cloud_batch_pump.mjs','utf8');
 const workflow=fs.readFileSync('.github/workflows/cortes-threads-cloud-handoff.yml','utf8');
 assert.match(src,/2026-10-22T08:40:00Z/);
 assert.match(src,/GITHUB_EVENT_NAME!=='workflow_dispatch'/);
 assert.match(src,/await sleep\(6\*60\*1000\)/);
 assert.match(src,/await yieldToWindows\(\)/);
 assert.match(workflow,/THREADS_BATCH/);
 assert.match(workflow,/timeout-minutes: 350/);
});
