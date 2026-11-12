import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
const start=source.indexOf('async function instagramDeadlinePacing(');
const stop=source.indexOf('\nasync function instagramAuthenticatedProfileSave(',start);
assert.ok(start>0&&stop>start,'exact Instagram pacing function must exist');
const fn=source.slice(start,stop)+'\nthis.instagramPacing=instagramDeadlinePacing;';

function build(now, row){
  const sql=[];
  class Clock extends Date{
    constructor(...args){super(...(args.length?args:[Date.parse(now)]));}
    static now(){return Date.parse(now);}
  }
  const context={Date:Clock,Number,Math,Error,
    query:async (text,params)=>{sql.push({text,params});return [row];}};
  vm.runInNewContext(fn,context,{timeout:2500});
  return {run:(remaining)=>context.instagramPacing('instagram:universoanthares',100,remaining),sql};
}
function row(now,values={}){
  return {pending:266,started_today:22,
    first_started:'2026-11-12T04:01:47.962Z',
    last_started:'2026-11-12T18:22:20.358Z',
    server_now:now,deadline_at:'2026-11-13T03:00:00.000Z',...values};
}
test('exact 23:00 local cutoff and 100 daily starts with provider quota',async()=>{
 const now='2026-11-12T18:26:14.921Z';
 const mock=build(now,row(now));
 const p=await mock.run(56);
 assert.equal(p.status,'WAIT');
 assert.equal(p.pending,266);
 assert.equal(p.started_today,22);
 assert.equal(p.remaining_today,56);
 assert.equal(p.carryover,210);
 assert.equal(p.deadline_at,'2026-11-13T03:00:00.000Z');
 assert.ok(p.interval_seconds>540&&p.interval_seconds<560);
 assert.ok(Date.parse(p.next_due_at)>Date.parse(now));
 assert.ok(mock.sql[0].text.includes('publication_started_at>='));
 assert.ok(!mock.sql[0].text.includes('updated_at'));
 assert.ok(mock.sql[0].text.includes("status IN ('started','uncertain','confirmed')"));
});
test('initial post is immediately due when day has no starts',async()=>{
 const now='2026-11-12T10:00:00.000Z';
 const p=await build(now,row(now,{started_today:0,last_started:null,first_started:null})).run(55);
 assert.equal(p.status,'DUE');
 assert.equal(p.next_due_at,now);
});
test('after first post remaining slots are evenly divided to 23:00',async()=>{
 const last='2026-11-12T10:00:00.000Z';
 const now='2026-11-12T10:01:00.000Z';
 const p=await build(now,row(now,{started_today:1,last_started:last,first_started:last,pending:5})).run(100);
 const expected=(Date.parse('2026-11-13T03:00:00Z')-Date.parse(last))/5;
 assert.equal(p.interval_seconds,expected/1000);
 assert.equal(Date.parse(p.next_due_at),Date.parse(last)+expected);
 assert.equal(p.status,'WAIT');
});
test('no catch-up burst after missed schedule: last real start is the anchor',async()=>{
 const now='2026-11-12T18:33:00Z';
 const p=await build(now,row(now,{last_started:'2026-11-12T18:22:20.358Z'})).run(56);
 assert.equal(p.status,'DUE');
 const nextNow='2026-11-12T18:34:00.000Z';
 const q=await build(nextNow,row(nextNow,{last_started:'2026-11-12T18:33:00.000Z',
   started_today:23})).run(55);
 assert.equal(q.status,'WAIT');
 assert.ok(q.interval_seconds>500);
});
test('rolling provider quota blocks even when daily limit has room',async()=>{
 const now='2026-11-12T18:26:14.921Z';
 const p=await build(now,row(now)).run(0);
 assert.equal(p.status,'LIMIT_REACHED');
 assert.equal(p.remaining_today,0);
});
test('strict 100 starts in same local day; cancellations are not counted',async()=>{
 const now='2026-11-12T18:26:14.921Z';
 const p=await build(now,row(now,{started_today:100})).run(60);
 assert.equal(p.status,'LIMIT_REACHED');
 assert.equal(p.started_today,100);
});
test('after 23:00 local no new submission may start',async()=>{
 const now='2026-11-13T03:00:00.000Z';
 const p=await build(now,row(now)).run(56);
 assert.equal(p.status,'WINDOW_CLOSED');
});
test('scope and quota must be verified before a single lease',async()=>{
 const now='2026-11-12T18:26:14.921Z',x=build(now,row(now));
 await assert.rejects(x.run(101),/SCOPE_INVALID/);
 await assert.rejects(x.run(-1),/SCOPE_INVALID/);
 await assert.rejects(x.run(NaN),/SCOPE_INVALID/);
});
test('missing timestamp on existing starts fails closed',async()=>{
 const now='2026-11-12T18:26:14.921Z';
 await assert.rejects(build(now,row(now,{last_started:null,first_started:null})).run(56),
                      /FIRST_START_INCONSISTENT/);
});
