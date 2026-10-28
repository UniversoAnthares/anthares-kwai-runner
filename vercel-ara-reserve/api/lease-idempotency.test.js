'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),crypto=require('node:crypto');
const {Pool}=require('pg');
const pool=new Pool({connectionString:process.env.ARA_ITEM9_TEST_DATABASE_URL,max:12});
let signals=0;
const notification=async()=>{signals++;return{ok:true,sequence:signals}};
const mcp=fs.readFileSync(__dirname+'/mcp.js','utf8');
const router=fs.readFileSync(__dirname+'/router.js','utf8');
function extract(source,begin,end){
 const a=source.indexOf(begin),b=source.indexOf(end,a+begin.length);
 assert.ok(a>=0&&b>a,'source anchor missing: '+begin);
 return source.slice(a,b);
}
const create=new Function('crypto','pool','notifyWakeAfterCommit','process',
 extract(mcp,'async function create(','async function execute(')+';return create'
)(crypto,pool,notification,{env:{ARA_WAKE_NOTIFY_ENABLED:'1'}});
assert.match(mcp,/execute\(String\(b\.device_id\|\|DEVICE\),String\(b\.type\),b\.args\|\|\{\},b\.timeout_seconds,b\.idempotency_key\)/);
assert.match(router,/FOR UPDATE SKIP LOCKED LIMIT 1/);
const safe=new Function(router.slice(router.indexOf('const SAFE=new Set('),router.indexOf(';',router.indexOf('const SAFE=new Set('))+1)+';return SAFE')();
assert.ok(safe.has('system_info')&&!safe.has('shell'));
const row=new Function(extract(router,'function row(','async function enqueue(')+';return row')();
const reap=new Function('SAFE',extract(router,'async function reap(','function row(')+';return reap')(safe);
const lease=new Function('reap','row',extract(router,'async function lease(','async function complete(')+';return lease')(reap,row);
const complete=new Function('row',extract(router,'async function complete(','async function waitJob(')+';return complete')(row);
async function setup(){
 await pool.query('DROP TABLE IF EXISTS ara_reserve_jobs');
 await pool.query(`CREATE TABLE ara_reserve_jobs(
 id text primary key,device_id text not null,type text not null,args jsonb not null,
 timeout_seconds integer not null,created_at timestamptz not null default now(),
 expires_at timestamptz not null,status text not null default 'queued',
 attempts integer not null default 0,lease_until timestamptz,
 idempotency_key text,result jsonb)`);
 await pool.query('CREATE UNIQUE INDEX ara_reserve_jobs_dedupe ON ara_reserve_jobs(device_id,idempotency_key) WHERE idempotency_key IS NOT NULL');
 signals=0;
}
test('ARA_ITEM9: same signed request via primary+standby returns one Neon job and one wake',async()=>{
 await setup();
 const key='cfmcp-00000000-1111-4111-8111-000000000000';
 const jobs=await Promise.all(Array.from({length:7},()=>create('DESKTOP-FTDK0HP','system_info',{a:1,b:'two'},25,key)));
 assert.equal(new Set(jobs.map(x=>x.id)).size,1);
 assert.equal(jobs.filter(x=>x.inserted).length,1);
 assert.equal(signals,1);
 const {rows}=await pool.query('SELECT count(*)::int n,count(DISTINCT id)::int ids FROM ara_reserve_jobs');
 assert.equal(rows[0].n,1);assert.equal(rows[0].ids,1);
 const retry=await create('DESKTOP-FTDK0HP','system_info',{b:'two',a:1},25,key);
 assert.equal(retry.id,jobs[0].id);assert.equal(retry.inserted,false);assert.equal(signals,1);
 console.log('ARA_ITEM9_DEDUPE_CONCURRENT_PASS');
});
test('ARA_ITEM9: key reused with changed payload or timeout fails closed',async()=>{
 await setup();
 const key='cfmcp-00000000-1111-4111-8111-000000000001';
 await create('DESKTOP-FTDK0HP','system_info',{x:1},25,key);
 await assert.rejects(create('DESKTOP-FTDK0HP','shell',{x:1},25,key),/idempotency_payload_mismatch/);
 await assert.rejects(create('DESKTOP-FTDK0HP','system_info',{x:2},25,key),/idempotency_payload_mismatch/);
 await assert.rejects(create('DESKTOP-FTDK0HP','system_info',{x:1},30,key),/idempotency_payload_mismatch/);
 await assert.rejects(create('DESKTOP-FTDK0HP','system_info',{x:1},25,'invalid'),/invalid_idempotency_key/);
 const {rows}=await pool.query('SELECT count(*)::int n FROM ara_reserve_jobs');
 assert.equal(rows[0].n,1);assert.equal(signals,1);
 console.log('ARA_ITEM9_CONFLICT_FAIL_CLOSED_PASS');
});
test('ARA_ITEM9: competing event/poll workers claim one lease only',async()=>{
 await setup();
 const key='cfmcp-00000000-1111-4111-8111-000000000002';
 const job=await create('DESKTOP-FTDK0HP','shell',{},30,key);
 const a=await pool.connect(),b=await pool.connect();
 try{
   await a.query('BEGIN');
   const claim1=await a.query("SELECT id FROM ara_reserve_jobs WHERE device_id=$1 AND status='queued' AND expires_at>now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1",['DESKTOP-FTDK0HP']);
   assert.equal(claim1.rows[0].id,job.id);
   await b.query('BEGIN');
   const claim2=await b.query("SELECT id FROM ara_reserve_jobs WHERE device_id=$1 AND status='queued' AND expires_at>now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1",['DESKTOP-FTDK0HP']);
   assert.equal(claim2.rowCount,0);
   await a.query("UPDATE ara_reserve_jobs SET status='leased',attempts=attempts+1,lease_until=now()+interval '45 seconds' WHERE id=$1",[job.id]);
   await a.query('COMMIT');await b.query('COMMIT');
 }finally{try{await a.query('ROLLBACK')}catch{}try{await b.query('ROLLBACK')}catch{}a.release();b.release();}
 const x=await pool.query('SELECT attempts,status FROM ara_reserve_jobs WHERE id=$1',[job.id]);
 assert.equal(x.rows[0].attempts,1);assert.equal(x.rows[0].status,'leased');
 const newClaim=await pool.connect();
 try{const again=await lease(newClaim,'DESKTOP-FTDK0HP');assert.equal(again,null);}
 finally{newClaim.release();}
 const finish=await pool.connect();
 try{
   const first=await complete(finish,'DESKTOP-FTDK0HP',job.id,{ok:true,output:'one'});
   assert.equal(first.status,'done');
   const second=await complete(finish,'DESKTOP-FTDK0HP',job.id,{ok:false,output:'two'});
   assert.equal(second.status,'done');
 }finally{finish.release();}
 const done=await pool.query('SELECT result,status,attempts FROM ara_reserve_jobs WHERE id=$1',[job.id]);
 assert.equal(done.rows[0].status,'done');assert.equal(done.rows[0].attempts,1);
 assert.equal(done.rows[0].result.output,'one');
 assert.equal(signals,1);
 console.log('ARA_ITEM9_SINGLE_LEASE_AND_TERMINAL_IMMUTABLE_PASS');
});
test('ARA_ITEM9: expired mutating lease becomes uncertain, never re-queued',async()=>{
 await setup();
 const shell=await create('DESKTOP-FTDK0HP','shell',{},10,'cfmcp-00000000-1111-4111-8111-000000000003');
 const info=await create('DESKTOP-FTDK0HP','system_info',{},10,'cfmcp-00000000-1111-4111-8111-000000000004');
 await pool.query("UPDATE ara_reserve_jobs SET status='leased',lease_until=now()-interval '1 second',attempts=1 WHERE id=ANY($1::text[])",[[shell.id,info.id]]);
 const c=await pool.connect();
 try{await reap(c,'DESKTOP-FTDK0HP');}finally{c.release();}
 const {rows}=await pool.query('SELECT id,status,attempts FROM ara_reserve_jobs WHERE id=ANY($1::text[])',[[shell.id,info.id]]);
 const byId=Object.fromEntries(rows.map(x=>[x.id,x]));
 assert.equal(byId[shell.id].status,'uncertain');
 assert.equal(byId[info.id].status,'queued');
 const worker=await pool.connect();
 try{
  const acquired=await lease(worker,'DESKTOP-FTDK0HP');
  assert.equal(acquired.id,info.id);
  const stale=await complete(worker,'DESKTOP-FTDK0HP',shell.id,{ok:true,output:'late'});
  assert.equal(stale.status,'uncertain');
 }finally{worker.release();}
 const after=await pool.query('SELECT status,result FROM ara_reserve_jobs WHERE id=$1',[shell.id]);
 assert.equal(after.rows[0].status,'uncertain');
 assert.equal(after.rows[0].result,null);
 console.log('ARA_ITEM9_UNCERTAIN_MUTATING_NEVER_RETRY_PASS');
});
test.after(async()=>{await pool.end();});
