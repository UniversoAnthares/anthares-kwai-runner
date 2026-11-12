import test from 'node:test';
import assert from 'node:assert/strict';
import {deriveKwaiPacing,KWAI_PACING_VERSION} from './kwai-pacing-policy.mjs';
const end='2026-11-12T03:00:00.000Z'; // 23:00 on Nov 11 in America/Campo_Grande
const clock='2026-11-12T00:00:00.000Z'; // Nov 11 at 20:00
const defaultInput=(v={})=>({
 target_key:'kwai:lucasrosalem',now:clock,deadline:end,
 pending:5,used:1,confirmed_today:1,
 first_confirmed_at:'2026-11-11T23:00:00.000Z',
 last_confirmed_at:'2026-11-11T23:00:00.000Z',daily_limit:100,...v});
test('first post is due immediately; timing starts only after first confirmation',()=>{
 const p=deriveKwaiPacing(defaultInput({used:0,confirmed_today:0,first_confirmed_at:null,last_confirmed_at:null}));
 assert.equal(p.status,'DUE');assert.equal(p.next_due_at,clock);
});
test('proportional future slots use actual last post, all prior to 23h',()=>{
 const p=deriveKwaiPacing(defaultInput());
 assert.equal(p.pacing_version,KWAI_PACING_VERSION);
 assert.equal(p.remaining_today,5);
 assert.equal(p.interval_seconds,40*60); // (23:00 - 19:00) / (5 + safety slot)
 assert.equal(p.next_due_at,'2026-11-11T23:40:00.000Z');
 const first=Date.parse(p.last_confirmed_at),gap=p.interval_seconds*1000;
 assert.equal(first+gap*(p.remaining_today+1),Date.parse(end));
 assert.ok(first+gap*p.remaining_today<Date.parse(end));
});
test('two accounts obey identical independent timetable rules',()=>{
 const one=deriveKwaiPacing(defaultInput());
 const two=deriveKwaiPacing(defaultInput({target_key:'kwai:universoanthares'}));
 assert.equal(one.next_due_at,two.next_due_at);
 assert.equal(two.remaining_today,5);
});
test('next due stays constant if no confirmed post or queue change',()=>{
 const a=deriveKwaiPacing(defaultInput());
 const b=deriveKwaiPacing(defaultInput({now:'2026-11-12T00:05:00.000Z'}));
 assert.equal(a.next_due_at,b.next_due_at);
});
test('refill and reduced queue recalculate exact intervals, never fixed delays',()=>{
 const base=deriveKwaiPacing(defaultInput());
 const refill=deriveKwaiPacing(defaultInput({pending:10}));
 const reduce=deriveKwaiPacing(defaultInput({pending:1}));
 assert.ok(refill.interval_seconds<base.interval_seconds);
 assert.ok(reduce.interval_seconds>base.interval_seconds);
});
test('new confirmed post changes anchor and reduces remaining slots',()=>{
 const old=deriveKwaiPacing(defaultInput());
 const next=deriveKwaiPacing(defaultInput({used:2,confirmed_today:2,
  last_confirmed_at:'2026-11-12T00:20:00.000Z',pending:4,
  now:'2026-11-12T00:25:00.000Z'}));
 assert.ok(Date.parse(next.next_due_at)>Date.parse(old.next_due_at));
 assert.equal(next.remaining_today,4);
});
test('database reconciliations cannot rewrite the actual publication anchor',()=>{
 const p=deriveKwaiPacing(defaultInput());
 assert.equal(p.last_confirmed_at,'2026-11-11T23:00:00.000Z');
 assert.equal(p.next_due_at,'2026-11-11T23:40:00.000Z');
});
test('daily cap and in-progress attempts are never exceeded',()=>{
 assert.equal(deriveKwaiPacing(defaultInput({pending:40,used:100,confirmed_today:99})).status,'BLOCKED_PLATFORM_LIMIT');
 assert.equal(deriveKwaiPacing(defaultInput({pending:40,used:98,confirmed_today:95})).remaining_today,2);
});
test('no post can start at or after 23h',()=>{
 for (const t of [end,'2026-11-12T03:01:00.000Z']){
  const p=deriveKwaiPacing(defaultInput({now:t}));
  assert.equal(p.status,'BLOCKED_SAME_DAY_CAPACITY');
 }
});
test('invalid or missing confirmed-post clock blocks, rather than guessing',()=>{
 const p=deriveKwaiPacing(defaultInput({confirmed_today:1,first_confirmed_at:null,last_confirmed_at:null}));
 assert.equal(p.status,'BLOCKED_UNVERIFIED_POST_CLOCK');
 assert.throws(()=>deriveKwaiPacing(defaultInput({target_key:'kwai:other'})),/INVALID_COUNTERS/);
 assert.throws(()=>deriveKwaiPacing(defaultInput({pending:-1})),/INVALID_COUNTERS/);
});
test('overdue schedule permits one next lease, not a same-tick burst',()=>{
 const p=deriveKwaiPacing(defaultInput({now:'2026-11-12T01:00:00.000Z'}));
 assert.equal(p.status,'DUE');
 assert.equal(p.next_due_at,'2026-11-11T23:40:00.000Z');
});
