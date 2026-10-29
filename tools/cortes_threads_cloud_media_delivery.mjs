import fs from 'node:fs/promises';

const MANIFEST=new URL('../config/threads-media-delivery-mirrors.json',import.meta.url);
const BLOB_HOST='izu4hsz4kmpqtwkl.public.blob.vercel-storage.com';
const SHA=/^[0-9a-f]{64}$/;
const KEY=/^([A-Za-z0-9_-]{11})\|g([0-9]+):([A-Za-z0-9_-]{11}):([0-9]+):([0-9]+)$/;

// This is a delivery-only override. It never changes the canonical
// WordPress URL or Neon reservation identity and cannot release quarantine.
export async function deliveryUrlForClip(clip){
 const canonical=String(clip?.url||'');
 const id=String(clip?.id||'');
 const doc=JSON.parse(await fs.readFile(MANIFEST,'utf8'));
 if(doc.schema!=='anthares.threads.media-delivery-mirrors.v1'||
    !doc.items||Array.isArray(doc.items)||typeof doc.items!=='object'){
  throw Error('THREADS_MIRROR_MANIFEST_INVALID');
 }
 const record=doc.items[id];
 if(!record)return canonical;
 const match=KEY.exec(id);
 const att=clip?.editorial?.transcript_attestation;
 if(!match||match[1]!==match[3]||!att||att.verified!==true||
    att.schema!=='anthares.clip-transcript-attestation.v1'||
    att.clip_id!=='g'+match[2]+':'+match[1]+':'+match[4]+':'+match[5]||
    att.source_video_id!==match[1]||
    Number(att.source_start_s)!==Number(match[4])||
    Number(att.source_end_s)!==Number(match[5])||
    !SHA.test(String(att.media_sha256||''))||
    att.media_sha256!==record.media_sha256||
    !Number.isSafeInteger(record.bytes)||record.bytes<100000||
    record.canonical_url!==canonical){
  throw Error('THREADS_MIRROR_EVIDENCE_MISMATCH');
 }
 const expected='/threads/'+match[1]+'/g'+match[2]+'-'+match[4]+'-'+match[5]+
    '-'+record.media_sha256.slice(0,12)+'.mp4';
 let uri;
 try{uri=new URL(record.delivery_url)}catch{throw Error('THREADS_MIRROR_INVALID_URL')}
 if(uri.protocol!=='https:'||uri.host!==BLOB_HOST||uri.pathname!==expected||
    uri.search||uri.hash||uri.username||uri.password){
  throw Error('THREADS_MIRROR_UNTRUSTED_URL');
 }
 return uri.href;
}
