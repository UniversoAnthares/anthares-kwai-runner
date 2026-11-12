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
  server_now:'2026-11-12T16:00:00Z',
  deadline_utc:'2026-11-13T03:00:00Z'
};

function stub(rows,table){
  globalThis.fetch=async (_url,opts)=>{
    const sql=JSON.parse(opts.body).query;
    assert.ok(sql.includes('FROM '+table),'must use independent account table');
    assert.ok(sql.includes("time '23:00:00'"),'23h exact deadline');
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
      assert.equal(p.due_at,'2026-11-12T17:00:00.000Z');
      assert.equal(p.available,3);
      stub({...base,server_now:'2026-11-12T18:00:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'publish');
      assert.equal(p.due_at,'2026-11-12T17:00:00.000Z');

      // The confirmation changes next due; it cannot retain a fixed 180–240s.
      stub({...base,server_now:'2026-11-12T18:00:00Z',
       daily:2,eligible:2,first_confirmed:'2026-11-12T12:00:00Z',
       last_confirmed:'2026-11-12T18:00:00Z'},table);
      p=await pacing(false);
      assert.equal(p.mode,'paced');
      assert.equal(p.due_at,'2026-11-12T22:30:00.000Z');

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
