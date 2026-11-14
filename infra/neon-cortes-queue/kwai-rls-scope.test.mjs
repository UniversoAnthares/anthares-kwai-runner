import assert from 'node:assert/strict';
import test from 'node:test';
import fn,{kwaiSqlScope} from './index.mjs';

const url='https://example.neon.tech/?action=health';
const audit='postgresql://audit:test@example.us-east-1.aws.neon.tech/neondb';
const oldAudit=process.env.CORTES_AUDIT_DATABASE_URL;

test('Kwai SQL scope is exact per account and rejects unknown account',()=>{
 assert.equal(kwaiSqlScope('kwai:lucasrosalem'),'kwai_primary');
 assert.equal(kwaiSqlScope('kwai:universoanthares'),'kwai_secondary');
 for(const x of ['',null,'kwai:another','kwai:lucasrosalem ','instagram:universoanthares',{}])
  assert.equal(kwaiSqlScope(x),null);
 console.log('NEON_KWAI_ACCOUNT_RLS_SCOPE_GUARD_PASS');
});

test('health uses the dedicated non-owner audit connection',async()=>{
 const fetchBefore=globalThis.fetch;
 process.env.CORTES_AUDIT_DATABASE_URL=audit;
 globalThis.fetch=async (_endpoint,options)=>{
  assert.equal(options.headers['Neon-Connection-String'],audit);
  assert.equal(options.method,'POST');
  return Response.json({rows:[{target_key:'kwai:lucasrosalem',status:'queued',n:0}]});
 };
 try{
  const r=await fn.fetch(new Request(url));
  assert.equal(r.status,200);
  assert.equal((await r.json()).database_ok,true);
  console.log('NEON_HEALTH_RESTRICTED_AUDIT_ROLE_PASS');
 }finally{
  globalThis.fetch=fetchBefore;
  if(oldAudit===undefined)delete process.env.CORTES_AUDIT_DATABASE_URL;
  else process.env.CORTES_AUDIT_DATABASE_URL=oldAudit;
 }
});

test('health fails closed if dedicated audit connection missing',async()=>{
 const before=process.env.CORTES_AUDIT_DATABASE_URL;
 const fetchBefore=globalThis.fetch;
 delete process.env.CORTES_AUDIT_DATABASE_URL;
 globalThis.fetch=async()=>{throw new Error('SCOPED DATABASE REQUEST MUST NEVER RUN');};
 try{
  const r=await fn.fetch(new Request(url));
  assert.equal(r.status,503);
  assert.equal((await r.json()).database_ok,false);
  console.log('NEON_RLS_ROLE_MISSING_FAIL_CLOSED_PASS');
 }finally{
  globalThis.fetch=fetchBefore;
  if(before===undefined)delete process.env.CORTES_AUDIT_DATABASE_URL;
  else process.env.CORTES_AUDIT_DATABASE_URL=before;
 }
});

test('unsigned Kwai route refuses call before any SQL scope is queried',async()=>{
 const fetchBefore=globalThis.fetch;
 globalThis.fetch=async()=>{throw new Error('MUST NOT TOUCH DATABASE');};
 try{
  for(const target_key of ['kwai:lucasrosalem','kwai:universoanthares']){
   const r=await fn.fetch(new Request('https://example.neon.tech/?action=kwai-lease',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({target_key,expected_account:target_key.split(':')[1]})
   }));
   assert.equal(r.status,401);
  }
 }finally{globalThis.fetch=fetchBefore;}
 console.log('NEON_KWAI_UNAUTH_NO_SQL_CALL_PASS');
});
