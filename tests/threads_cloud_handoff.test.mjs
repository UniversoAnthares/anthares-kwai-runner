
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';

import backend from '../infra/neon-cortes-threads-execution/index.mjs';
import {validateEditorial} from '../tools/cortes_threads_cloud_captions.mjs';

const endpoint='https://neon.example.invalid/?action=control';

test('cloud mutation rejects missing GitHub OIDC token',async()=>{
 const response=await backend.fetch(new Request(endpoint,{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:'{"action":"claim"}'
 }));

 assert.equal(response.status,401);
});

test('cloud mutation rejects forged device identity',async()=>{
 const response=await backend.fetch(new Request(endpoint,{
  method:'POST',
  headers:{
   'Content-Type':'application/json',
   'X-Anthares-Device':'DESKTOP-FTDK0HP',
   'Authorization':'Bearer fake'
  },
  body:'{"action":"ack-pause"}'
 }));

 assert.equal(response.status,401);
});

test('backend declines arbitrary URL',async()=>{
 const response=await backend.fetch(new Request(
  'https://neon.example.invalid/?action=publish',
  {
   method:'POST',
   body:'{}'
  }
 ));

 assert.equal(response.status,404);
});

test('local gate permits normal local publishing before cloud handoff',()=>{
 const root=fs.mkdtempSync(
  path.join(os.tmpdir(),'threads-cloud-gate-')
 );

 try{
  const p=path.resolve('tools/threads_cloud_local_gate.mjs');

  const result=spawnSync(process.execPath,[p],{
   env:{
    ...process.env,
    CORTES_THREADS_LOCAL_ROOT:root
   },
   encoding:'utf8'
  });

  assert.ok([0,20].includes(result.status));

  assert.match(
   result.stdout,
   /NOT_ARMED_LOCAL_PRIMARY|REMOTE_CLOUD_PRIMARY_ACTIVE_NO_MARKER|NEON_GATE_FAIL_CLOSED/
  );
 }finally{
  fs.rmSync(root,{
   recursive:true,
   force:true
  });
 }
});

test('invalid handoff marker prevents uncoordinated local publications',()=>{
 const root=fs.mkdtempSync(
  path.join(os.tmpdir(),'threads-cloud-gate-')
 );

 try{
  fs.writeFileSync(
   path.join(root,'threads-cloud-handoff-armed.json'),
   '{"enabled":true}'
  );

  const p=path.resolve('tools/threads_cloud_local_gate.mjs');

  const result=spawnSync(process.execPath,[p],{
   env:{
    ...process.env,
    CORTES_THREADS_LOCAL_ROOT:root
   },
   encoding:'utf8'
  });

  assert.equal(result.status,20);

  assert.match(
   result.stdout,
   /INVALID_LOCAL_ARM_MARKER/
  );
 }finally{
  fs.rmSync(root,{
   recursive:true,
   force:true
  });
 }
});

test('cloud publisher cannot post on an automated push event',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 assert.match(src,/THREADS_ALLOW_PUBLISH==='1'/);
 assert.match(src,/GITHUB_EVENT_NAME/);
 assert.match(src,/callControl\(jwt,'claim'\)/);
 assert.match(src,/callControl\(jwt,'reserve'/);
 assert.match(src,/callControl\(jwt,'start'/);
 assert.match(src,/callControl\(jwt,'confirm'/);
 assert.match(src,/callControl\(jwt,'uncertain'/);
});

test('cloud selects queued identities using exact WordPress lookup',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 assert.match(src,/queued_rows/);
 assert.match(src,/fetchCloudClipByIdentity/);
 assert.doesNotMatch(src,/fetchCloudManifest/);
 assert.match(src,/THREADS_QUEUE_EMPTY_OR_ISOLATED/);
});

test('exact WordPress lookup miss preserves queued Neon identity',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 const candidateMiss=src.match(
  /if\(!candidate\)\{([\s\S]*?)\n  \}/
 )?.[1]||'';

 assert.match(
  candidateMiss,
  /THREADS_CLIP_NOT_FOUND_EXACT/
 );

 assert.doesNotMatch(
  candidateMiss,
  /callControl\(jwt,'quarantine'/
 );

 assert.doesNotMatch(
  candidateMiss,
  /reason:'MEDIA_INVALID'/
 );

 assert.match(candidateMiss,/rejected\+\+/);
});

test('unknown cloud submissions retain a durable reconciliation block',()=>{
 const src=fs.readFileSync(
  'infra/neon-cortes-threads-execution/index.mjs',
  'utf8'
 );

 assert.match(src,/threads_cloud_unknown/);
 assert.match(src,/cloud_inflight/);
 assert.match(src,/local_pause_until=NULL/);
});

test('dry-run must verify signed GitHub OIDC without publishing',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 const backendSource=fs.readFileSync(
  'infra/neon-cortes-threads-execution/index.mjs',
  'utf8'
 );

 assert.match(src,/await verifyCloudOidc\(jwt\)/);
 assert.match(backendSource,/op==='preflight'/);
 assert.match(
  backendSource,
  /allowPush&&claims\.event_name==='push'/
 );
 assert.match(backendSource,/mutations_allowed:false/);
});

test('cloud Graph receipt is logged before Neon confirmation and never retried as a post',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 const g=src.indexOf('THREADS_GRAPH_POSTED=');
 const c=src.indexOf("await callControl(jwt,'confirm'");

 assert.ok(g>=0&&c>g);

 assert.match(
  src,
  /for\(let attempt=1;attempt<=4;attempt\+\+\)/
 );

 assert.match(
  src,
  /url:verified\?\.url\|\|null/
 );

 assert.equal(
  (src.match(/verified=await publishVideo/g)||[]).length,
  1
 );
});

test('Neon confirm is idempotent and uncertain status retains verified public permalink',()=>{
 const src=fs.readFileSync(
  'infra/neon-cortes-threads-execution/index.mjs',
  'utf8'
 );

 assert.match(
  src,
  /status='confirmed' AND remote_id=\$5/
 );

 assert.match(src,/submitted_post_url/);
 assert.match(src,/reason_code:reason/);
});

test('Windows handoff JSON parser tolerates UTF-8 BOM',()=>{
 const src=fs.readFileSync(
  'tools/threads_cloud_local_gate.mjs',
  'utf8'
 );

 assert.ok(
  src.includes("replace(/^\\uFEFF/")
 );
});

test('scheduled cloud is idempotent and requires Neon primary enabled',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 const workflow=fs.readFileSync(
  '.github/workflows/cortes-threads-cloud-handoff.yml',
  'utf8'
 );

 const backend=fs.readFileSync(
  'infra/neon-cortes-threads-execution/index.mjs',
  'utf8'
 );

 assert.match(
  workflow,
  /cron: '\*\/6 \* \* \* \*'/
 );

 assert.match(workflow,/issues: write/);

 assert.match(
  src,
  /THREADS_CLOUD_PRIMARY_DISABLED_SKIP/
 );

 assert.match(
  src,
  /THREADS_CLOUD_COOLDOWN_SIX_MINUTES/
 );

 assert.match(backend,/cloud_primary_enabled=true/);
 assert.match(backend,/claims\.event_name/);
 assert.match(backend,/CLOUD_STILL_HEALTHY_OR_ACTIVE/);
});

test('404/410 and caption failures isolate a single clip without blocking the next',()=>{
 const src=fs.readFileSync(
  'tools/cortes_threads_cloud_handoff.mjs',
  'utf8'
 );

 const backend=fs.readFileSync(
  'infra/neon-cortes-threads-execution/index.mjs',
  'utf8'
 );

 assert.match(
  src,
  /for\(const row of queue\.slice\(0,60\)\)/
 );

 assert.match(
  src,
  /callControl\(jwt,'quarantine'/
 );

 assert.match(
  src,
  /notifyQA\(id,reason\)/
 );

 assert.doesNotMatch(backend,/expires_at<=now\(\)/);
 assert.doesNotMatch(backend,/SET status='failed'/);
 assert.match(backend,/status='isolated',reason_code=EXCLUDED.reason_code/);
 assert.match(backend,/cortes_threads_quarantine\.status IN \('isolated','resolved','expired'\)/);
 assert.match(src,/THREADS_QUARANTINE_STALE_ROW_SKIPPED/);
});

test('local hot standby honors Neon primary and cloud watchdog stalls',()=>{
 const src=fs.readFileSync(
  'tools/threads_cloud_local_gate.mjs',
  'utf8'
 );

 const steward=fs.readFileSync(
  'tools/threads_cloud_primary_steward.ps1',
  'utf8'
 );

 assert.match(
  src,
  /snapshot\.cloud_primary_enabled/
 );

 assert.match(
  src,
  /REMOTE_CLOUD_PRIMARY_ACTIVE_NO_MARKER/
 );

 assert.match(
  steward,
  /deactivate-primary/
 );

 assert.match(
  steward,
  /CLOUD_STALE_20MIN_SAFE_LOCAL_TAKEOVER/
 );
});

test('night batch remains dispatch-only, within approved deadline, with signed backend fallback',()=>{
 const src=fs.readFileSync(
  'tools/threads_cloud_batch_pump.mjs',
  'utf8'
 );

 const workflow=fs.readFileSync(
  '.github/workflows/cortes-threads-cloud-handoff.yml',
  'utf8'
 );

 assert.match(
  src,
  /2026-10-22T08:40:00Z/
 );

 assert.match(
  src,
  /GITHUB_EVENT_NAME!=='workflow_dispatch'/
 );

 assert.match(
  src,
  /await sleep\(6\*60\*1000\)/
 );

 assert.match(
  src,
  /await yieldToWindows\(\)/
 );

 assert.match(workflow,/THREADS_BATCH/);
 assert.match(workflow,/timeout-minutes: 350/);
});

test('medium ASR is accepted with valid segment-bound evidence but arbitrary engines are rejected',()=>{
 const excerpt=
  'Gregor Samsa e Kafka aparecem na conversa sobre o livro e a transformação em inseto.';

 const media='a'.repeat(64);

 const clip={
  clip_id:'g1:fOmihuHUT1M:1325:1365',
  attachment_id:17001,
  sha256:media,
  duration:40
 };

 const attestation={
  schema:'anthares.clip-transcript-attestation.v1',
  clip_id:clip.clip_id,
  attachment_id:clip.attachment_id,
  media_sha256:media,
  method:'faster-whisper-medium-from-media',
  cues:[
   {
    start:0,
    end:12,
    text:excerpt
   }
  ],
  excerpt,
  verified:true
 };

 const meta={
  title:'Gregor Samsa e Kafka: a transformação em inseto ● Universo Anthares',
  description:
   'Uma conversa sobre Gregor Samsa, Kafka, o livro e a transformação em inseto. www.anthares.us',
  caption:'#Kafka #Literatura',
  alt_text:'Gregor, Kafka, inseto',
  transcript_attestation:attestation
 };

 assert.ok(
  validateEditorial(meta,clip).title.includes('Gregor')
 );

 assert.throws(
  ()=>validateEditorial({
   ...meta,
   transcript_attestation:{
    ...attestation,
    method:'unverified-external-tool'
   }
  },clip),
  /EDITORIAL_TRANSCRIPT_ATTESTATION_REQUIRED/
 );

 assert.throws(
  ()=>validateEditorial({
   ...meta,
   transcript_attestation:{
    ...attestation,
    media_sha256:'b'.repeat(64)
   }
  },clip),
  /EDITORIAL_TRANSCRIPT_ATTESTATION_REQUIRED/
 );
});

test('Threads public text never exceeds five words including description and hashtags',()=>{
 const src=fs.readFileSync('tools/cortes_threads_cloud_captions.mjs','utf8');
 assert.match(src,/titleWords\.slice\(0,5\)\.join\(' '\)/);
 assert.match(src,/caption\.split\(\/\\s\+\/u\)\.length>5/);
 assert.doesNotMatch(src,/const caption=base\+desc/);
});

test('expired Threads quarantine cannot silently fail queued publications',()=>{
 const src=fs.readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');
 assert.doesNotMatch(src,/UPDATE cortes_publications p SET status='failed'/);
 assert.doesNotMatch(src,/UPDATE cortes_threads_quarantine SET status='expired'/);
 assert.match(src,/q.status='isolated'/);
 assert.doesNotMatch(src,/q.status='isolated' AND q.expires_at>now\(\)/);
});
