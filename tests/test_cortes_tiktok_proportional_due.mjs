import test from 'node:test';
import assert from 'node:assert/strict';

import {proportionalDue as primary} from '../infra/neon-cortes-tiktok/index.mjs';
import {proportionalDue as secondary} from '../infra/neon-cortes-lucasrosalem4/index.mjs';

const oldFetch=globalThis.fetch;
const oldUrl=process.env.DATABASE_URL;
process.env.DATABASE_URL='postgresql://test:test@ep-fake.us-east-1.aws.neon.tech/neondb';
const base={
  daily:1,eligible:3,leased:0,
  first_confirmed:'2026-11-12T12:00:00Z',
  last_confirmed:'2026-11-12T12:00:00Z',
  last_started:null,
  start_utc:'2026-11-12T10:00:00Z',
  final_due_utc:'2026-11-13T02:59:00Z',
  server_now:'2026-11-12T16:00:00Z',
  deadline_utc:'2026-11-13T03:00:00Z'
};

function stub(rows,table){
  globalThis.fetch=async (_url,opts)=>{
    const sql=JSON.parse(opts.body).query;
    assert.ok(sql.includes('FROM '+table),'must use independent account table');
    assert.ok(sql.includes("time '06:00:00'"),'start 06:00 local');
    assert.ok(sql.includes("time '22:59:00'"),'final due before 23h');
    assert.ok(sql.includes("time '23:00:00'"),'hard stop at 23h');
    assert.ok(sql.includes('confirmed_at'),'actual verified post date');
    return new Response(JSON.stringify({rows:[rows],rowCount:1}),{status:200,
      headers:{'Content-Type':'application/json'}});
  };
}

await test('both independent accounts honor 23:00, confirmed-receipt interval and second gate',async t=>{
  for(const [name,pacing,table] of [
    ['universo.anthares',primary,'cortes_tiktok_publications'],
    ['lucasrosalem4',secondary,'cortes_tiktok_lucasrosalem4_publications']
  ]){
    await t.test(name,async()=>{
      stub({...base},table);
      let p=await pacing(false);
      assert.equal(p.mode,'paced');
      assert.equal(p.due_at,'2026-11-12T16:59:40.000Z');
      assert.equal(p.available,3);
      stub({...base,server_now:'2026-11-12T18:00:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'publish');
      assert.equal(p.due_at,'2026-11-12T16:59:40.000Z');

      // The confirmation changes next due; it cannot retain a fixed 180–240s.
      stub({...base,server_now:'2026-11-12T18:00:00Z',
       daily:2,eligible:2,first_confirmed:'2026-11-12T12:00:00Z',
       last_confirmed:'2026-11-12T18:00:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'paced');
      assert.equal(p.due_at,'2026-11-12T22:29:30.000Z');

      // STARTED guard accounts for one existing Neon lease.
      stub({...base,server_now:'2026-11-12T18:00:00Z',
       eligible:2,leased:1},table);
      p=await pacing(true);
      assert.equal(p.mode,'publish');
      assert.equal(p.available,3);

      stub({...base,server_now:'2026-11-13T03:00:01Z'},table);
      assert.equal((await pacing(false)).mode,'cap');
      stub({...base,daily:100},table);
      assert.equal((await pacing(false)).mode,'cap');

      // No publication may begin at 05:59; first eligible wake-up at 06:00
      // immediately authorizes a start when there is no prior confirmation.
      stub({...base,daily:0,first_confirmed:null,last_confirmed:null,
        last_started:null,server_now:'2026-11-12T09:59:59Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'before_window');
      assert.equal(p.due_at,'2026-11-12T10:00:00.000Z');
      stub({...base,daily:0,first_confirmed:null,last_confirmed:null,
        last_started:null,server_now:'2026-11-12T10:00:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'publish');
      // An unconfirmed STARTED remains a spacing anchor; no burst while
      // waiting for a remote provider receipt.
      stub({...base,first_confirmed:null,last_confirmed:null,
        last_started:'2026-11-12T12:00:00Z',server_now:'2026-11-12T12:01:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'paced');
      assert.equal(p.due_at,'2026-11-12T16:59:40.000Z');
      stub({...base,server_now:'2026-11-13T02:59:59Z',
        last_started:'2026-11-13T02:59:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'cap');
      stub({...base,daily:0,first_confirmed:null,last_confirmed:null},table);
      assert.equal((await pacing(false)).mode,'publish');

      stub({...base,first_confirmed:'2026-11-12T19:00:00Z',
        last_confirmed:'2026-11-12T18:00:00Z'},table);
      await assert.rejects(()=>pacing(false),/RECEIPT_INVALID/);
    });
  }
});
globalThis.fetch=oldFetch;
if(oldUrl===undefined)delete process.env.DATABASE_URL;else process.env.DATABASE_URL=oldUrl;
