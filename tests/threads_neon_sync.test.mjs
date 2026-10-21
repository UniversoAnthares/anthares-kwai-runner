import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import service from '../infra/neon-cortes-threads-sync/index.mjs';
const secret='unit-test-threads-device-key';
const expected=crypto.createHash('sha256').update(secret).digest('hex');
const oldFetch=globalThis.fetch,oldDb=process.env.DATABASE_URL;
process.env.DATABASE_URL='postgres://demo:demo@demo.neon.tech/neondb';
globalThis.fetch=async (url,options)=> {
 if(String(url).includes('raw.githubusercontent.com'))return new Response(expected,{status:200});
 if(String(url).includes('api.neon.tech'))return Response.json({rows:[{status:'queued',count:1}]});
 throw Error('UNEXPECTED_FETCH '+url);
};
const target='https://example.invalid/?action=';
const auth={'Authorization':'Bearer '+secret,'X-Anthares-Device':'DESKTOP-FTDK0HP','Content-Type':'application/json'};
test('rejects requests without device credentials',async()=>{
 const r=await service.fetch(new Request(target+'stats',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"target_key":"threads:universoanthares"}'}));
 assert.equal(r.status,401);
});
test('rejects cross-network stats even with valid device credential',async()=>{
 const r=await service.fetch(new Request(target+'stats',{method:'POST',headers:auth,body:'{"target_key":"kwai:lucasrosalem"}'}));
 assert.equal(r.status,403);
});
test('rejects fabricated confirmation URL before database mutation',async()=>{
 const clip='fOmihuHUT1M|g1:fOmihuHUT1M:9600:9690';
 const r=await service.fetch(new Request(target+'threads-ledger-sync',{method:'POST',headers:auth,body:JSON.stringify({entries:[{id:'threads:'+clip,status:'confirmed',post_url:'https://www.threads.com/@anotheruser/post/ABC123'}]})}));
 assert.equal(r.status,400);
});
test('rejects wrong media identity for new queue row',async()=>{
 const r=await service.fetch(new Request(target+'enqueue',{method:'POST',headers:auth,body:JSON.stringify({id:'threads:unknown',target_key:'threads:universoanthares'})}));
 assert.equal((await r.json()).error,'THREADS_ENQUEUE_INVALID');
});
test('service is intentionally incapable of publishing media',async()=>{
 const r=await service.fetch(new Request(target+'publish',{method:'POST',headers:auth,body:'{}'}));
 assert.equal(r.status,404);
});
test.after(()=>{globalThis.fetch=oldFetch;if(oldDb===undefined)delete process.env.DATABASE_URL;else process.env.DATABASE_URL=oldDb});