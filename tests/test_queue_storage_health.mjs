import test from 'node:test';
import assert from 'node:assert/strict';
import {migrateLegacyTargetAccounts, storageQuotaResponse} from '../cloudflare-worker/src/queue_storage_health.js';

test('cold starts never rewrite unchanged default-account history',()=>{
 const writes=[];
 const sql={exec:(query,...args)=>{
  if(query.startsWith('SELECT'))return {toArray:()=>[
   {id:'old',account_id:'default',payload:'{}'},
   {id:'bad',account_id:'default',payload:'{bad'},
   {id:'done',account_id:'lucasrosalem',payload:'{}'}]};
  writes.push(args);
 }};
 for(let i=0;i<100;i++)migrateLegacyTargetAccounts(sql);
 assert.deepEqual(writes,[]);
});
test('real legacy-account migration occurs once and preserves job payload',()=>{
 const row={id:'old',account_id:'default',payload:'{"account_id":"@LucasRosalem"}'};let writes=0;
 const sql={exec:(query,account)=>{
  if(query.startsWith('SELECT'))return {toArray:()=>[row]};
  writes++;row.account_id=account;
 }};
 migrateLegacyTargetAccounts(sql);migrateLegacyTargetAccounts(sql);
 assert.equal(writes,1);assert.equal(row.account_id,'lucasrosalem');
 assert.equal(row.payload,'{"account_id":"@LucasRosalem"}');
});
test('quota is explicit retryable503 and never authorizes publication',async()=>{
 const r=storageQuotaResponse(new Error('Exceeded allowed rows written in Durable Objects free tier.'));
 assert.equal(r.status,503);assert.equal(r.headers.get('Retry-After'),'900');
 assert.equal((await r.json()).publication_allowed,false);
 assert.equal(storageQuotaResponse(new Error('unrelated code bug')),null);
});
