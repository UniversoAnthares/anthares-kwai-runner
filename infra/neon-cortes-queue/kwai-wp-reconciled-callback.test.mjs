import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
const start=src.indexOf('async function kwaiSyncReconciledWordpress(');
const end=src.indexOf('async function kwaiUnprovenAction(',start);
const fn=src.slice(start,end);
test('only reconciled confirmed Kwai publication may call WordPress',()=>{
 assert.ok(start>0&&end>start);
 assert.match(fn,/p.status='confirmed'/);
 assert.match(fn,/kwai_authenticated_source_frames_reconciled_v1/);
 assert.match(fn,/remote_id=\$3/);
});
test('target URL and confidential callback token are bound server-side',()=>{
 for(const part of ["endpoint.protocol!=='https:'","['anthares.us','www.anthares.us']",
  "'/cortes/clip-network-callback'","token.length<16","!endpoint.pathname.includes",
  "'https://www.kwai.com/@'+account+'/'"])
  assert.ok(fn.includes(part),part);
 assert.match(fn,/media\?\.cortes_callback_token/);
 assert.doesNotMatch(fn,/console\.log\(token/);
 assert.doesNotMatch(fn,/return\s*\{[^}]*token/);
});
test('WordPress reply is checked and successful callbacks are durable',()=>{
 assert.match(fn,/response\.ok/);
 assert.match(fn,/answer\.ok===true/);
 assert.match(fn,/wp_callback_state','completed'/);
 assert.match(fn,/AbortSignal\.timeout\(18000\)/);
 assert.match(fn,/pending:results\.filter\(x=>!x\.ok\)/);
});
test('same signed action supports callback retry and the confirm path attempts origin sync',()=>{
 assert.match(src,/if\(mode==='wp-sync'\)return kwaiSyncReconciledWordpress/);
 assert.match(src,/const wp=await kwaiSyncReconciledWordpress\(target,id\)/);
 assert.match(src,/kwaiUnprovenAction\(b,actor,KWAI_TARGET\)/);
 assert.match(src,/actor\.role!=='kwai-physical'/);
});
