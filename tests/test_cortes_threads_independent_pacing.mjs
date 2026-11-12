import test from 'node:test';
import assert from 'node:assert/strict';
import {threadsProportionalDue} from '../infra/neon-cortes-threads-execution/index.mjs';

const original=globalThis.fetch;
const old=process.env.DATABASE_URL;
process.env.DATABASE_URL='postgresql://fake:fake@ep-fake.us-east-1.aws.neon.tech/neondb';
const base={eligible:3,cloud_leased:0,started:1,
  first_confirmed:'2026-11-12T12:00:00Z',
  last_confirmed:'2026-11-12T12:00:00Z',
  server_now:'2026-11-12T16:00:00Z',
  deadline_at:'2026-11-13T03:00:00Z'};
const stub=row=>{
  globalThis.fetch=async (_url,options)=>{
    const body=JSON.parse(options.body);
    assert.ok(body.query.includes("p.target_key=$1"));
    assert.equal(body.params[0],'threads:universoanthares');
    assert.ok(body.query.includes("interval '23 hours'"));
    assert.ok(body.query.includes("status='isolated'"));
    return new Response(JSON.stringify({rows:[row],rowCount:1}),{status:200,
      headers:{'Content-Type':'application/json'}});
  };
};
await test('independent Threads cloud honors WordPress 23h interval and second guard',async()=>{
  stub(base);
  let p=await threadsProportionalDue(false);
  assert.equal(p.status,'WAIT');
  assert.equal(p.next_due_at,'2026-11-12T17:00:00.000Z');
  stub({...base,server_now:'2026-11-12T18:00:00Z'});
  p=await threadsProportionalDue(false);
  assert.equal(p.status,'DUE');
  // Same leased media remains eligible at STARTED boundary.
  stub({...base,eligible:2,cloud_leased:1,server_now:'2026-11-12T18:00:00Z'});
  p=await threadsProportionalDue(true);
  assert.equal(p.status,'DUE');
  assert.equal(p.remaining_today,3);
  // A verified new post always changes the due time.
  stub({...base,eligible:2,started:2,server_now:'2026-11-12T18:00:00Z',
    last_confirmed:'2026-11-12T18:00:00Z'});
  p=await threadsProportionalDue(false);
  assert.equal(p.status,'WAIT');
  assert.equal(p.next_due_at,'2026-11-12T22:30:00.000Z');
  stub({...base,server_now:'2026-11-13T03:00:01Z'});
  assert.equal((await threadsProportionalDue(false)).status,'BLOCKED_SAME_DAY_CAPACITY');
  stub({...base,started:100});
  assert.equal((await threadsProportionalDue(false)).status,'BLOCKED_PLATFORM_LIMIT');
  stub({...base,first_confirmed:null,last_confirmed:null,started:0});
  assert.equal((await threadsProportionalDue(false)).status,'DUE');
  stub({...base,first_confirmed:'2026-11-12T19:00:00Z',
    last_confirmed:'2026-11-12T18:00:00Z'});
  await assert.rejects(()=>threadsProportionalDue(false),/THREADS_PACING_RECEIPT_INVALID/);
});
globalThis.fetch=original;
if(old===undefined)delete process.env.DATABASE_URL;else process.env.DATABASE_URL=old;
