import test from 'node:test';
import assert from 'node:assert/strict';
import {captionForClip} from './cortes_threads_cloud_captions.mjs';

const clip={id:'fOmihuHUT1M|g1:fOmihuHUT1M:92:132',clip_id:'g1:fOmihuHUT1M:92:132',attachment_id:16939,sha256:'a'.repeat(64),duration:40,url:'https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_fOmihuHUT1M_g1_92_132.mp4'};
const meta={title:'Metamorfose de Kafka na literatura austríaca ● Universo Anthares',description:'O falante menciona a obra Metamorfose de Kafka, destacando sua importância na literatura austríaca. www.anthares.us',caption:'#Kafka #Metamorfose',alt_text:'Kafka, metamorfose, literatura'};
test('reject actual mismatched WordPress metadata without bound transcript',()=>{
 assert.throws(()=>captionForClip(meta,clip),/EDITORIAL_TRANSCRIPT_ATTESTATION_REQUIRED/);
});
test('reject literal escape contamination before posting',()=>{
 assert.throws(()=>captionForClip({...meta,description:meta.description+'\\n\\n'},clip),/EDITORIAL_UNSAFE_ESCAPES_OR_SOURCE_METADATA/);
});
test('reject synthetic attestation referring to different clip',()=>{
 const transcript_attestation={schema:'anthares.clip-transcript-attestation.v1',clip_id:'other',attachment_id:16939,verified:true,excerpt:'Metamorfose Kafka literatura austríaca obra importância autor leitura filosofia e outros argumentos extensos'};
 assert.throws(()=>captionForClip({...meta,transcript_attestation},clip),/EDITORIAL_TRANSCRIPT_ATTESTATION_REQUIRED/);
});
test('reject unrelated title despite bound attestation',()=>{
 const transcript_attestation={schema:'anthares.clip-transcript-attestation.v1',clip_id:clip.clip_id,attachment_id:clip.attachment_id,verified:true,media_sha256:'a'.repeat(64),method:'faster-whisper-small-from-media',cues:[{start:0,end:20,text:'Falamos sobre leitura de poesia em sala de aula e consideramos os ritmos diferentes da escrita moderna e o impacto dos professores.'}],excerpt:'Falamos sobre leitura de poesia em sala de aula e consideramos os ritmos diferentes da escrita moderna e o impacto dos professores.'};
 assert.throws(()=>captionForClip({...meta,transcript_attestation},clip),/EDITORIAL_TITLE_NOT_SUPPORTED_BY_TRANSCRIPT/);
});
