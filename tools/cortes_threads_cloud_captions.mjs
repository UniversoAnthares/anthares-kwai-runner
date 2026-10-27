import fs from 'node:fs/promises';
const BRAND=' ● Universo Anthares',WEBSITE='www.anthares.us';
const decode=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&#x27;/g,"'").replace(/&nbsp;/g,' ').replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n))).normalize('NFC').replace(/\s+/g,' ').trim();
export function cleanTitle(x){return decode(x)}
// Fail closed: a WordPress media attachment title alone cannot certify the
// words spoken in a given clip. Only a segment-bound, independently verified
// excerpt may authorize its publication.
const norm=s=>decode(s).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const words=s=>norm(s).match(/[a-z0-9]{4,}/g)||[];
const unsafe=s=>/\\[nr]/.test(String(s||''))||/\uFFFD/.test(String(s||''))||
  /https?:\/\/|<video\b|wp-video|short_[A-Za-z0-9_-]+_g[0-9]+/i.test(String(s||''));
export function validateEditorial(meta,clip){
 const title=decode(meta?.title),description=decode(meta?.description);
 const hashtags=decode(meta?.caption).match(/#[A-Za-zÀ-ÖØ-öø-ÿ0-9_]{3,45}/g)||[];
 const keywords=decode(meta?.alt_text).split(',').map(x=>x.trim()).filter(Boolean);
 if([meta?.title,meta?.description,meta?.caption,meta?.alt_text].some(unsafe))
  throw Error('EDITORIAL_UNSAFE_ESCAPES_OR_SOURCE_METADATA');
 if(!title.endsWith(BRAND)||title.length<40||title.length>180||
   /^(Trecho|Corte|Live|Vídeo)\b/i.test(title)||/\b\d\d:\d\d\b/.test(title))
  throw Error('EDITORIAL_TITLE_MISSING_OR_GENERIC');
 if(description.length<70||!description.includes(WEBSITE))throw Error('EDITORIAL_DESCRIPTION_MISSING');
 if(keywords.length<3||hashtags.length<2)throw Error('EDITORIAL_TERMS_MISSING');
 const attested=meta?.transcript_attestation;
 if(!attested||attested.schema!=='anthares.clip-transcript-attestation.v1'||
    attested.clip_id!==clip?.clip_id||
    attested.attachment_id!==clip?.attachment_id||
    attested.media_sha256!==clip?.sha256||
    !/^[a-f0-9]{64}$/.test(attested.media_sha256||'')||
    !['faster-whisper-small-from-media','faster-whisper-medium-from-media'].includes(attested.method)||
    !Array.isArray(attested.cues)||attested.cues.length===0||
    attested.cues.some(c=>typeof c.text!=='string'||typeof c.start!=='number'||
      typeof c.end!=='number'||c.start<0||c.end>clip.duration+5||c.end<=c.start)||
    attested.cues.map(c=>c.text).join(' ')!==attested.excerpt||
    attested.verified!==true||
    typeof attested.excerpt!=='string'||attested.excerpt.length<60)
  throw Error('EDITORIAL_TRANSCRIPT_ATTESTATION_REQUIRED');
 const source=new Set(words(attested.excerpt));
 const distinct=[...new Set(words(title.replace(BRAND,'')))].filter(w=>w!=='universo'&&w!=='anthares');
 if(distinct.length<3||distinct.filter(w=>source.has(w)).length<2)
  throw Error('EDITORIAL_TITLE_NOT_SUPPORTED_BY_TRANSCRIPT');
 const bodyWords=[...new Set(words(description.replace(WEBSITE,'')))];
 if(bodyWords.filter(w=>source.has(w)).length<3)
  throw Error('EDITORIAL_DESCRIPTION_NOT_SUPPORTED_BY_TRANSCRIPT');
 return {title,description,hashtags:[...new Set(hashtags)],keywords};
}
export function captionForClip(meta,clip){
 if(!clip?.id||!clip?.url)throw Error('EDITORIAL_CLIP_IDENTITY_MISSING');
 const validated=validateEditorial(meta,clip);
 const tags=[...new Set([...validated.hashtags,'#UniversoAnthares'])].slice(0,6).join(' ');
 const base=validated.title+'\n\n';
 const end='\n\n'+WEBSITE+'\n'+tags;
 const remaining=500-base.length-end.length;
 if(remaining<70)throw Error('EDITORIAL_THREADS_CAPTION_OVER_LIMIT');
 const desc=validated.description.replace(WEBSITE,'').trim();
 const caption=base+desc.slice(0,remaining).trimEnd()+end;
 if(caption.length>500||caption.includes('\uFFFD')||unsafe(caption))
  throw Error('EDITORIAL_THREADS_CAPTION_INVALID');
 return {...clip,title:validated.title,caption,
  description:validated.description,keywords:validated.keywords,hashtags:validated.hashtags,
  editorial_policy:'anthares_editorial_transcript_attested_v3'};
}
export async function addCloudCaptions(manifest){
 const items=(manifest.items||[]).map(clip=>captionForClip(clip.editorial,clip));
 return {...manifest,items,caption_source:'wp_verified_segment_metadata',ai_tokens_per_publication:0};
}
if(process.argv[1]?.replaceAll('\\','/').endsWith('/cortes_threads_cloud_captions.mjs')){
 try{
  const file=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
  const output=await addCloudCaptions(file);
  await fs.writeFile(process.argv[3],JSON.stringify(output,null,2)+'\n','utf8');
  console.log(JSON.stringify({ok:true,total:output.items.length,caption_source:output.caption_source}));
 }catch(e){console.error('THREADS_EDITORIAL_REQUIRED='+String(e.message).slice(0,100));process.exitCode=1}
}
