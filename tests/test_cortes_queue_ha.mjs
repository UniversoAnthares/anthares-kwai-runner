import assert from 'node:assert/strict';
import test from 'node:test';
import neon from '../infra/neon-cortes-queue/index.mjs';
import edge from '../infra/cloudflare-cortes-queue-ha/src/index.js';

const neonURL='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/';
const originalFetch=globalThis.fetch;
const oldEnv=process.env.DATABASE_URL;
const db='postgresql://user:example@c-14.us-east-1.aws.neon.tech/anthares';

test('Neon queue exposes only read-only health without authentication', async()=>{
 process.env.DATABASE_URL=db;
 globalThis.fetch=async url=>{
  assert.match(String(url),/^https:\/\/api\.us-east-1\.aws\.neon\.tech\/sql/);
  return Response.json({rows:[{target_key:'linkedin:primary',status:'queued',n:2}]});
 };
 try{
  const r=await neon.fetch(new Request(neonURL+'?action=health'));
  const b=await r.json();
  assert.equal(r.status,200);
  assert.equal(b.ok,true);
  assert.equal(b.network_isolation,true);
  assert.equal(b.counts[0].target_key,'linkedin:primary');
 }finally{globalThis.fetch=originalFetch;process.env.DATABASE_URL=oldEnv;}
});

test('Neon queue refuses unsigned job enqueues and independent worker mutations', async()=>{
 for(const action of ['enqueue','buffer-lease','probe']){
  const r=await neon.fetch(new Request(neonURL+'?action='+action,{
   method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({platform:'linkedin',target_key:'linkedin:primary'})
  }));
  assert.equal(r.status,401,action);
 }
});

test('Neon queue refuses unknown methods and endpoints', async()=>{
 const r=await neon.fetch(new Request(neonURL+'?action=run-publisher'));
 assert.equal(r.status,404);
});

test('Cloudflare edge forwards only fixed Neon health checks', async()=>{
 globalThis.fetch=async (url,opts)=>{
  assert.equal(String(url),neonURL+'?action=health');
  assert.equal(opts.method,'GET');
  return Response.json({ok:true,backend:'neon-functions-cortes',database_ok:true,
                        network_isolation:true,counts:[]});
 };
 try{
  const r=await edge.fetch(new Request('https://example.workers.dev/healthz'));
  assert.equal(r.status,200);
  assert.equal((await r.json()).database_ok,true);
 }finally{globalThis.fetch=originalFetch;}
});

test('Cloudflare edge rejects unsigned writes before upstream', async()=>{
 globalThis.fetch=async()=>{throw Error('UPSTREAM MUST NOT BE CALLED')};
 try{
  const r=await edge.fetch(new Request('https://example.workers.dev/?action=buffer-lease',{
   method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}));
  assert.equal(r.status,401);
 }finally{globalThis.fetch=originalFetch;}
});

test('Cloudflare edge preserves OIDC unchanged, without routing to user supplied URL', async()=>{
 const secret='x'.repeat(90);
 globalThis.fetch=async (url,opts)=>{
  assert.equal(String(url),neonURL+'?action=probe');
  assert.equal(opts.headers.Authorization,'Bearer '+secret);
  assert.equal(opts.method,'POST');
  assert.equal(opts.body,'{"nonce":"safe-probe"}');
  return Response.json({ok:true,probe:'SIGNED_OIDC_NEON_WRITE_READ_DELETE'});
 };
 try{
  const r=await edge.fetch(new Request('https://example.workers.dev/?action=probe',{
   method:'POST',headers:{Authorization:'Bearer '+secret,'Content-Type':'application/json'},
   body:'{"nonce":"safe-probe"}'}));
  assert.equal(r.status,200);
 }finally{globalThis.fetch=originalFetch;}
});
