import test from 'node:test';
import assert from 'node:assert/strict';
import {captionForClip,validateEditorial,addCloudCaptions} from '../tools/cortes_threads_cloud_captions.mjs';
import {clipFromMedia} from '../tools/cortes_threads_cloud_feed.mjs';
const title='Como Kafka apresenta a rejeição de Gregor Samsa ● Universo Anthares';
const meta={title,title: {rendered:title}, description:'<p>Em A metamorfose, Kafka mostra como a família rejeita Gregor Samsa. Essa leitura discute a transformação e a identidade.</p><p>www.anthares.us</p>',caption:'#Kafka #Metamorfose #GregorSamsa',alt_text:'Kafka, A metamorfose, Gregor Samsa, rejeição da família'};
const clip={id:'-CSeY1OpvwA|g1:-CSeY1OpvwA:1234:1275',url:'https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_-CSeY1OpvwA_g1_1234_1275.mp4',clip_id:'g1:-CSeY1OpvwA:1234:1275'};
test('strategic title and precise subject tags reach Threads, without live timestamp',()=>{
 const v=captionForClip({...meta,title},clip);
 assert.equal(v.title,title);
 assert.ok(v.caption.includes('Kafka'));
 assert.ok(v.caption.includes('#Metamorfose'));
 assert.ok(v.caption.includes('www.anthares.us'));
 assert.ok(v.caption.length<=500);
 assert.ok(!v.caption.includes('Trecho 20:34'));
 assert.equal(v.editorial_policy,'anthares_editorial_transcript_v2');
});
test('generic live headline cannot reach publisher',()=>{
 assert.throws(()=>captionForClip({title:'LITERATURA E ESCRITA | Trecho 05:33',description:meta.description,caption:meta.caption,alt_text:meta.alt_text},clip),/EDITORIAL_TITLE_MISSING_OR_GENERIC/);
});
test('missing transcript-specific keywords blocks publication',()=>{
 assert.throws(()=>validateEditorial({title,description:meta.description,caption:meta.caption,alt_text:''}),/EDITORIAL_TERMS_MISSING/);
});
test('WordPress manifest preserves exact attachment editorial metadata',()=>{
 const m={mime_type:'video/mp4',source_url:clip.url,date:'2026-10-22T06:15:00',id:387,title:{rendered:title},caption:{rendered:meta.caption},description:{rendered:meta.description},alt_text:meta.alt_text};
 const row=clipFromMedia(m,'2026-10-22');assert.ok(row);
 assert.equal(row.editorial.title,title);assert.equal(row.editorial.alt_text,meta.alt_text);
});
test('batch caption generation rejects one ungrounded item rather than inventing a headline',async()=>{
 await assert.rejects(addCloudCaptions({items:[{...clip,editorial:{title,description:meta.description,caption:meta.caption,alt_text:''}}]}),/EDITORIAL_TERMS_MISSING/);
});
