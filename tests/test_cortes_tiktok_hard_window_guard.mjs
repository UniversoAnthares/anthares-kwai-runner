import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const migration=readFileSync('db/migrations/20261112_tiktok_hard_window_proportional_guard.sql','utf8');
const vercel=readFileSync('vercel-ara-primary/api/cortes-tiktok.mjs','utf8');
const primary=readFileSync('infra/neon-cortes-tiktok/index.mjs','utf8');
const secondary=readFileSync('infra/neon-cortes-lucasrosalem4/index.mjs','utf8');
const common=readFileSync('infra/neon-cortes-queue/index.mjs','utf8');
const threads=readFileSync('infra/neon-cortes-threads-execution/index.mjs','utf8');

await test('PostgreSQL trigger rejects early or late starts on both TikTok accounts',()=>{
 for(const x of ['cortes_tiktok_hard_window_06_23_v1',
                 'cortes_tiktok4_hard_window_06_23_v1',
                 "time '06:00:00'","time '23:00:00'","time '22:59:00'",
                 'pg_advisory_xact_lock','v_last_confirmed','v_last_started',
                 'v_due := v_anchor+(v_last_slot-v_anchor)/v_remaining',
                 'CORTES_TIKTOK_HARD_WINDOW_06_23',
                 'CORTES_TIKTOK_PROPORTIONAL_EARLY_START'])
  assert.ok(migration.includes(x),x);
 for(const x of ['DROP TABLE','TRUNCATE TABLE','DELETE FROM cortes_tiktok'])
  assert.ok(!migration.includes(x),'migration must be additive: '+x);
});
await test('both TikTok primary and fallback ingress calculate 06h to 23h',()=>{
 for(const c of [vercel,primary,secondary]){
  assert.ok(c.includes("time '06:00:00'"),'06h start');
  assert.ok(c.includes("time '22:59:00'"),'last due');
  assert.ok(c.includes("time '23:00:00'"),'hard cutoff');
  assert.ok(c.includes("last_started"),'protect unconfirmed start');
  assert.ok(c.includes("mode:'before_window'"),'before-window safe stop');
  assert.ok(c.includes('proportionalDue(true)'),'start double gate');
  assert.ok(!c.includes("Math.max(180,Math.min(240"),'no arbitrary interval');
  assert.ok(!c.includes("time '23:45:00'"),'no late-night window');
 }
});
await test('other Neon destinations also share 06h start and 23h hard stop',()=>{
 for(const c of [common,threads]){
  assert.ok(c.includes("interval '6 hours'"),'06h start');
  assert.ok(c.includes("interval '22 hours 59 minutes'"),'last slot');
  assert.ok(c.includes("interval '23 hours'"),'hard end');
  assert.ok(c.includes('last_started'),'unconfirmed start anchor');
  assert.ok(c.includes('WAIT_DAY_START'),'no overnight first post');
 }
});
