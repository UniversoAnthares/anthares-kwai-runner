import fs from 'node:fs/promises';
const BRAND=' ● Universo Anthares',WEBSITE='www.anthares.us';
const decode=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&#x27;/g,"'").replace(/&nbsp;/g,' ').replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n))).normalize('NFC').replace(/\s+/g,' ').trim();
export function cleanTitle(x){return decode(x)}
export function validateEditorial(meta){
 const title=decode(meta?.title),description=decode(meta?.description);
 const hashtags=decode(meta?.caption).match(/#[A-Za-zÀ-ÖØ-öø-ÿ0-9_]{3,45}/g)||[];
 const keywords=decode(meta?.alt_text).split(',').map(x=>x.trim()).filter(Boolean);
 if(!title.endsWith(BRAND)||title.length<40||title.length>180||
  /^(Trecho|Corte|Live|Vídeo)\b/i.test(title)||/\b\d\d:\d\d\b/.test(title))
  throw Error('EDITORIAL_TITLE_MISSING_OR_GENERIC');
 if(description.length<70||!description.includes(WEBSITE))throw Error('EDITORIAL_DESCRIPTION_MISSING');
 if(keywords.length<3||hashtags.length<2)throw Error('EDITORIAL_TERMS_MISSING');
 return {title,description,hashtags:[...new Set(hashtags)],keywords};
}
export function captionForClip(meta,clip){
 const validated=validateEditorial(meta);
 if(!clip?.id||!clip?.url)throw Error('EDITORIAL_CLIP_IDENTITY_MISSING');
 const tags=[...new Set([...validated.hashtags,'#UniversoAnthares'])].slice(0,6).join(' ');
 const base=validated.title+'\n\n';
 const end='\n\n'+WEBSITE+'\n'+tags;
 const remaining=500-base.length-end.length;
 if(remaining<70)throw Error('EDITORIAL_THREADS_CAPTION_OVER_LIMIT');
 const desc=validated.description.replace(WEBSITE,'').trim();
 const caption=base+desc.slice(0,remaining).trimEnd()+end;
 if(caption.length>500||caption.includes('\uFFFD'))throw Error('EDITORIAL_THREADS_CAPTION_INVALID');
 return {...clip,title:validated.title,caption,
  description:validated.description,keywords:validated.keywords,hashtags:validated.hashtags,
  editorial_policy:'anthares_editorial_transcript_v2'};
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
