import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const {Miniflare,convertV4MiniflareOptions}=await import(process.env.MINIFLARE_MODULE||'miniflare');
const helper=(await readFile(new URL('./src/secure-fetch.mjs',import.meta.url),'utf8')).replace('export async function','async function');
async function run(script,handler) {
 const options={modules:true,compatibilityDate:'2026-10-01',script,outboundService:handler};
 const mf=new Miniflare(convertV4MiniflareOptions?convertV4MiniflareOptions(options):options);
 try{return await(await mf.dispatchFetch('https://test.invalid/')).json()}finally{await mf.dispose()}
}
test('actual workerd rejects redirect:error before sending a provider request',async()=>{
 let requests=0;
 const r=await run(`export default{async fetch(){try{await fetch('https://provider.invalid/',{redirect:'error'});return Response.json({ok:true})}catch(e){return Response.json({name:e.name,message:e.message})}}}`,()=>{requests++;return new Response('ok')});
 assert.equal(r.name,'TypeError');assert.match(r.message,/Invalid redirect value/);assert.equal(requests,0);
});
test('production helper performs a manual-mode provider request in actual workerd',async()=>{
 let requests=0;
 const r=await run(helper+`\nexport default{async fetch(){const r=await fetchWithoutRedirects('https://provider.invalid/',{headers:{authorization:'Bearer fake-test-only'}});return Response.json({status:r.status,ok:(await r.json()).ok})}}`,req=>{
  requests++;assert.equal(req.url,'https://provider.invalid/');return Response.json({ok:true});
 });
 assert.equal(r.status,200);assert.equal(r.ok,true);assert.equal(requests,1);
});
test('actual workerd helper rejects redirects without forwarding credentials',async()=>{
 let requests=0;
 const r=await run(helper+`\nexport default{async fetch(){try{await fetchWithoutRedirects('https://provider.invalid/',{headers:{authorization:'Bearer fake-test-only'}});return Response.json({ok:true})}catch(e){return Response.json({error:e.message})}}}`,req=>{
  requests++;assert.equal(new URL(req.url).hostname,'provider.invalid');return new Response(null,{status:302,headers:{location:'https://untrusted.invalid/'}});
 });
 assert.equal(r.error,'upstream_redirect_rejected');assert.equal(requests,1);
});
