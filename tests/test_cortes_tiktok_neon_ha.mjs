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

test('Cloudflare pacing-audit route requires OIDC before forwarding',async()=>{
 const old=globalThis.fetch;let called=false;
 globalThis.fetch=()=>{called=true;throw Error('unexpected');};
 try{
  const r=await edge.fetch(new Request('https://edge.invalid/?action=pacing-audit'));
  assert.equal(r.status,401);
  assert.equal((await r.json()).error,'oidc_required');
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

test('TikTok queue selects the newest source by original ingestion, not a late historic refill',async()=>{
  const {readFileSync}=await import('node:fs');
  const text=readFileSync(new URL('../infra/neon-cortes-tiktok/index.mjs',import.meta.url),'utf8');
  assert(text.includes('GROUP BY source_id'));
  assert(text.includes('HAVING COUNT(*) FILTER'));
  assert(text.includes('ORDER BY MIN(created_at) DESC,source_id DESC LIMIT 1'));
  assert(!text.includes('ORDER BY created_at DESC,id DESC LIMIT 1'));
});

test('Source-priority change retains queued-only, cooldown, 100/day and fenced single-claim protection',async()=>{
  const {readFileSync}=await import('node:fs');
  const text=readFileSync(new URL('../infra/neon-cortes-tiktok/index.mjs',import.meta.url),'utf8');
  assert(text.includes('pg_try_advisory_xact_lock(19283746501001::bigint)'));
  assert(text.includes('FOR UPDATE SKIP LOCKED LIMIT 1'));
  assert(text.includes('COUNT(*) FILTER'));
  assert(text.includes('retry_not_before IS NULL OR retry_not_before<=now()'));
  // The canonical scheduler now computes a proportional slot through 22:59,
  // fenced again immediately before STARTED, with 23:00 as an exclusive stop.
  assert(text.includes('if(now>=end||used>=100)'));
  assert(text.includes('const available=Math.min(queued+leased,Math.max(0,100-used))'));
  assert(text.includes('const due=anchor+(finalSlot-anchor)/available'));
  assert(text.includes("if(timing.mode!=='publish')"));
  assert(text.includes("time '06:00:00'"));
  assert(text.includes("time '23:00:00'"));
  assert(!text.includes("source_id='cOhqEaY3-08'"));
});

test('Neon and Vercel TikTok failover agree on original-source priority',async()=>{
 const {readFileSync}=await import('node:fs');
 const neon=readFileSync(new URL('../infra/neon-cortes-tiktok/index.mjs',import.meta.url),'utf8');
 const backup=readFileSync(new URL('../vercel-ara-primary/api/cortes-tiktok.mjs',import.meta.url),'utf8');
 const clause='ORDER BY MIN(created_at) DESC,source_id DESC LIMIT 1';
 assert(neon.includes(clause));
 assert(backup.includes(clause));
 assert(neon.includes('HAVING COUNT(*) FILTER'));
 assert(backup.includes('HAVING COUNT(*) FILTER'));
 assert(!backup.includes('ORDER BY created_at DESC,id DESC LIMIT 1'));
});
