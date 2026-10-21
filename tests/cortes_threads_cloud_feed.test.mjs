import test from 'node:test';
import assert from 'node:assert/strict';
import {clipFromMedia,localDay,fetchCloudManifest} from '../tools/cortes_threads_cloud_feed.mjs';
const m=(date='2026-10-21T09:21:43',file='short_fOmihuHUT1M_g1_1727_1763.mp4')=>({date,mime_type:'video/mp4',id:12,source_url:'https://anthares.us/wp-content/uploads/anthares-clips/2026/10/'+file});
test('stable identity',()=>assert.equal(clipFromMedia(m(),'2026-10-21').id,'fOmihuHUT1M|g1:fOmihuHUT1M:1727:1763'));
test('no stale clips',()=>assert.equal(clipFromMedia(m('2026-10-20T00:01:00'),'2026-10-21'),null));
test('bad duration',()=>assert.equal(clipFromMedia(m(undefined,'short_fOmihuHUT1M_g1_1_2000.mp4'),'2026-10-21'),null));
test('deduplication',async()=>{const r={ok:true,headers:{get:()=> '1'},json:async()=>[m(),m()]};assert.equal((await fetchCloudManifest({day:'2026-10-21',fetcher:async()=>r})).total,1)});
test('Campo Grande timezone',()=>assert.equal(localDay(new Date('2026-10-21T02:00:00Z')),'2026-10-20'));