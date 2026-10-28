'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {Pool}=require('pg');
const pool=new Pool({connectionString:process.env.ARA_ITEM8_TEST_DATABASE_URL,max:3});
const mcp=fs.readFileSync(__dirname+'/mcp.js','utf8');
const router=fs.readFileSync(__dirname+'/router.js','utf8');
function between(src,begin,end){
  const a=src.indexOf(begin),b=src.indexOf(end,a+begin.length);
  assert.ok(a>=0&&b>a,'source function anchor missing: '+begin);
  return src.slice(a,b);
}
const queries=[];
const measuredPool={query:async(...args)=>{
  queries.push(String(args[0]));
  return pool.query(...args);
}};
const status=new Function('pool',
  between(mcp,'async function status(d){','async function create(')+';return status')(measuredPool);
const heartbeat=new Function(
  between(router,'async function heartbeat(c,d,p){','async function status(')+';return heartbeat')();
const device='DESKTOP-FTDK0HP';
async function setup(){
 await pool.query('DROP TABLE IF EXISTS ara_reserve_jobs');
 await pool.query('DROP TABLE IF EXISTS ara_reserve_devices');
 await pool.query(`CREATE TABLE ara_reserve_devices(
   device_id text PRIMARY KEY,heartbeat jsonb NOT NULL DEFAULT '{}'::jsonb,
   seen_at timestamptz NOT NULL DEFAULT now())`);
 await pool.query(`CREATE TABLE ara_reserve_jobs(
   id text PRIMARY KEY,device_id text NOT NULL,status text NOT NULL)`);
 queries.length=0;
}
test('ARA_ITEM8_FIRST_HEARTBEAT_ENROLLMENT_PASS',async()=>{
 await setup();
 const hb={hostname:'DESKTOP-FTDK0HP',time:'2026-10-28T22:00:00Z',version:'0.3.1'};
 await heartbeat(measuredPool,device,hb);
 assert.equal(queries.length,2,'first enrollment requires UPDATE miss + one UPSERT');
 assert.match(queries[0],/^UPDATE ara_reserve_devices/);
 assert.match(queries[1],/INSERT INTO ara_reserve_devices/);
 const q=await pool.query('SELECT heartbeat,seen_at FROM ara_reserve_devices WHERE device_id=$1',[device]);
 assert.equal(q.rowCount,1);assert.deepEqual(q.rows[0].heartbeat,hb);assert.ok(q.rows[0].seen_at instanceof Date);
 console.log('ARA_ITEM8_FIRST_HEARTBEAT_ENROLLMENT_PASS');
});
test('ARA_ITEM8_ESTABLISHED_HEARTBEAT_ONE_UPDATE_PASS',async()=>{
 const hb={hostname:'DESKTOP-FTDK0HP',time:'2026-10-28T22:01:00Z',version:'0.3.1'};
 const before=await pool.query('SELECT seen_at FROM ara_reserve_devices WHERE device_id=$1',[device]);
 queries.length=0;
 await heartbeat(measuredPool,device,hb);
 assert.equal(queries.length,1,'existing heartbeat must issue one UPDATE only');
 assert.match(queries[0],/^UPDATE ara_reserve_devices/);
 const q=await pool.query('SELECT heartbeat,seen_at FROM ara_reserve_devices WHERE device_id=$1',[device]);
 assert.deepEqual(q.rows[0].heartbeat,hb);
 assert.ok(q.rows[0].seen_at>=before.rows[0].seen_at);
 console.log('ARA_ITEM8_ESTABLISHED_HEARTBEAT_ONE_UPDATE_PASS');
});
test('ARA_ITEM8_SIGNED_PRESENCE_SINGLE_SELECT_PASS',async()=>{
 await pool.query(`INSERT INTO ara_reserve_jobs(id,device_id,status) VALUES
 ('queued1',$1,'queued'),('queued2',$1,'queued'),
 ('leased1',$1,'leased'),('uncertain1',$1,'uncertain'),
 ('done1',$1,'done'),('other','OTHER-DEVICE','queued')`,[device]);
 queries.length=0;
 const r=await status(device);
 assert.equal(queries.length,1,'signed MCP status must use exactly one SQL statement');
 assert.match(queries[0],/LEFT JOIN LATERAL/);
 assert.ok(!/UPDATE|DELETE|INSERT/.test(queries[0]),'status cannot mutate the queue');
 assert.equal(r.connected,true);assert.equal(r.queued,2);assert.equal(r.leased,1);assert.equal(r.uncertain,1);
 assert.equal(r.backend,'vercel-neon');assert.equal(r.heartbeat.hostname,device);
 assert.ok(typeof r.seen_at==='string'&&r.seen_at.endsWith('Z'));
 console.log('ARA_ITEM8_SIGNED_PRESENCE_SINGLE_SELECT_PASS');
});
test('ARA_ITEM8_MISSING_DEVICE_AND_STALE_TTL_PASS',async()=>{
 queries.length=0;
 const missing=await status('OTHER-DEVICE');
 assert.equal(queries.length,1);assert.equal(missing.connected,false);
 assert.equal(missing.heartbeat,null);assert.equal(missing.seen_at,null);
 assert.equal(missing.queued,1);assert.equal(missing.leased,0);
 await pool.query("UPDATE ara_reserve_devices SET seen_at=now()-interval '95 seconds' WHERE device_id=$1",[device]);
 queries.length=0;const stale=await status(device);
 assert.equal(queries.length,1);assert.equal(stale.connected,false);
 assert.equal(stale.queued,2);assert.equal(stale.uncertain,1);
 await pool.query("UPDATE ara_reserve_devices SET seen_at=now()-interval '70 seconds' WHERE device_id=$1",[device]);
 queries.length=0;const recent=await status(device);
 assert.equal(queries.length,1);assert.equal(recent.connected,true);
 console.log('ARA_ITEM8_MISSING_DEVICE_AND_STALE_TTL_PASS');
});
test.after(async()=>{await pool.end();});
