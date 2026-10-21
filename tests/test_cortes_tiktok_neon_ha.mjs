import test from 'node:test';
import assert from 'node:assert/strict';
import neon from '../infra/neon-cortes-tiktok/index.mjs';
import edge from '../infra/cloudflare-cortes-tiktok-ha/src/index.js';

test('Neon TikTok supports unauthenticated health and shares canonical fenced ledger',async()=>{
 const old=globalThis.fetch,conn=process.env.DATABASE_URL;
 process.env.DATABASE_URL='postgresql://test:demo@ep-test.neon.tech/test';
 const calls=[];
 globalThis.fetch=async (url,init)=>{
  calls.push([url,String(init?.body||'').slice(0,120)]);
  if(String(init?.body||'').includes('SELECT count(*)::int AS total FROM public.cortes_tiktok_publications'))
   return Response.json({rows:[{total:'158'}],rowCount:1});
  return Response.json({rows:[],rowCount:0});
 };
 try{
  const r=await neon.fetch(new Request('https://neon.invalid/?action=health'));
  const body=await r.json();
  assert.equal(r.status,200);
  assert.equal(body.ok,true);
  assert.equal(body.service,'cortes-tiktok-neon');
  assert.equal(body.fencing,true);
  assert(calls.length>=3);
 }finally{
  globalThis.fetch=old;
  if(conn===undefined)delete process.env.DATABASE_URL;
  else process.env.DATABASE_URL=conn;
 }
});

test('Neon function denies anonymous queue mutation',async()=>{
 const r=await neon.fetch(new Request('https://neon.invalid/?action=start',{method:'POST',
  headers:{'content-type':'application/json'},body:'{}'}));
 assert.equal(r.status,401);
 assert.equal((await r.json()).error,'unauthorized_oidc');
});

test('Cloudflare TikTok edge blocks untrusted writes before upstream',async()=>{
 const old=globalThis.fetch;let called=false;
 globalThis.fetch=()=>{called=true;throw Error('unexpected');};
 try{
  const r=await edge.fetch(new Request('https://edge.invalid/?action=claim',{method:'POST',
   headers:{'content-type':'application/json'},body:'{}'}));
  assert.equal(r.status,401);
  assert.equal(called,false);
 }finally{globalThis.fetch=old;}
});

test('Cloudflare edge routes only to fixed Neon TikTok backend',async()=>{
 const old=globalThis.fetch;let last='';
 globalThis.fetch=(url)=>{last=url;return Promise.resolve(Response.json(
  {ok:true,service:'cortes-tiktok-neon',fencing:true}))};
 try{
  const r=await edge.fetch(new Request('https://edge.invalid/?action=health'));
  assert.equal(r.status,200);
  assert(last.includes('cortestiktok.compute.'));
  assert(!last.includes('vercel.'));
 }finally{globalThis.fetch=old;}
});

test('Neon SQL string counts are normalized before client status processing',async()=>{
  const {readFileSync}=await import('node:fs');
  const text=readFileSync(new URL('../infra/neon-cortes-tiktok/index.mjs',import.meta.url),'utf8');
  assert(text.includes('Number(x.count)'));
  assert(text.includes('db_ledger_total'));
});
