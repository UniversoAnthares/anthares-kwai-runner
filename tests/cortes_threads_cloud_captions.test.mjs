import test from 'node:test';
import assert from 'node:assert/strict';
import {cleanTitle,captionForClip,addCloudCaptions} from '../tools/cortes_threads_cloud_captions.mjs';
test('Unicode safe YouTube title',()=>assert.equal(cleanTitle('A Metamorfose [Kafka] - AN\u00C1LISE (LIVE)'),'A Metamorfose [Kafka] - AN\u00C1LISE'));
test('reject replacement characters',()=>assert.throws(()=>cleanTitle('AN\uFFFDLISE')));
test('caption has title, timestamp and tags',()=>{const c=captionForClip('A Metamorfose [Kafka] - AN\u00C1LISE',{clip_id:'g1:fOmihuHUT1M:9434:9515'});assert.match(c.title,/Trecho 157:14/);assert.ok(c.caption.includes('#Kafka'));assert.ok(c.caption.includes('www.anthares.us'))});
test('one metadata request for multiple clips of one live',async()=>{
 let calls=0;const manifest={items:[{source:'fOmihuHUT1M',clip_id:'g1:fOmihuHUT1M:1:20'},{source:'fOmihuHUT1M',clip_id:'g1:fOmihuHUT1M:20:60'}]};
 const result=await addCloudCaptions(manifest,async()=>{calls++;return{ok:true,json:async()=>({title:'A Metamorfose'})}});
 assert.equal(calls,1);assert.equal(result.items.length,2);assert.equal(result.ai_tokens_per_publication,0);
});