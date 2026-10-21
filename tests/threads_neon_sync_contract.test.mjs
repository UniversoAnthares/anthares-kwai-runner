import assert from 'node:assert/strict';
import test from 'node:test';
import crypto from 'node:crypto';
import neon from '../infra/neon-threads-sync/index.mjs';
const endpoint='https://example.com/?action=threads-ledger-sync';
const headers={'Authorization':'Bearer '+('x'.repeat(48)),'X-Anthares-Device':'DESKTOP-FTDK0HP'};
test('public health never sends a post',async()=>{const r=await neon.fetch(new Request('https://example.com/health'));assert.equal(r.status,200);assert.equal((await r.json()).posts_sent,0)});
test('anonymous request is rejected before database activity',async()=>{const r=await neon.fetch(new Request(endpoint,{method:'POST',body:'{"entries":[]}'}));assert.equal(r.status,401)});
test('authentication, account URL and uncertain guards',async()=>{
 const original=globalThis.fetch;
 const saved=process.env.DATABASE_URL;
 try{
  process.env.DATABASE_URL='postgresql://fixture:fixture@ep-fixture.neon.tech/neondb';
  globalThis.fetch=async url=>{
   if(String(url).includes('raw.githubusercontent.com'))return new Response(crypto.createHash('sha256').update('x'.repeat(48)).digest('hex'));
   throw Error('database must not be accessed for invalid inputs');
  };
  const bad=[{id:'threads:fOmihuHUT1M|g1:fOmihuHUT1M:9600:9690',status:'confirmed',post_url:'https://www.threads.com/@wrongaccount/post/abc'}];
  let r=await neon.fetch(new Request(endpoint,{method:'POST',headers,body:JSON.stringify({entries:bad})}));
  assert.equal(r.status,409);
  assert.equal((await r.json()).error,'INVALID_ACCOUNT_OR_POST_URL');
  r=await neon.fetch(new Request(endpoint,{method:'POST',headers,body:JSON.stringify({entries:[{...bad[0],status:'uncertain'}]})}));
  assert.equal(r.status,409);
  assert.equal((await r.json()).error,'UNCERTAIN_CANNOT_CLAIM_PUBLIC_URL');
 }finally{globalThis.fetch=original;if(saved===undefined)delete process.env.DATABASE_URL;else process.env.DATABASE_URL=saved}
});
