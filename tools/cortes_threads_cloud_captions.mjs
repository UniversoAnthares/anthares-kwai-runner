import fs from 'node:fs/promises';
export function cleanTitle(input){
 const s=String(input||'').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&#x27;/g,"'").normalize('NFC')
  .replace(/\s*[\[(]?\s*LIVE\s*[\])]?\s*$/i,'').trim();
 if(!s||s.includes('\uFFFD')||s.length>180)throw Error('UNSAFE_SOURCE_TITLE');
 return s;
}
export function captionForClip(sourceTitle,clip){
 const source=cleanTitle(sourceTitle),start=Number(clip?.clip_id?.split(':').at(-2));
 if(!Number.isSafeInteger(start)||start<0)throw Error('INVALID_CLIP_START');
 const mark=String(Math.floor(start/60)).padStart(2,'0')+':'+String(start%60).padStart(2,'0');
 const title=source+' | Trecho '+mark+' \u25CF Universo Anthares';
 let tags='#Literatura #Livros #Leitura #UniversoAnthares';
 if(/Kafka|Metamorfose/i.test(source))tags+=' #Kafka #AMetamorfose';
 else if(/Arist[oó]teles|Po[eé]tica/i.test(source))tags+=' #Aristoteles #Poetica';
 else if(/Tolst[oó]i|Ivan Ilitch/i.test(source))tags+=' #Tolstoi #IvanIlitch';
 const caption=title+'\n\nwww.anthares.us\n\n'+tags;
 if(title.includes('\uFFFD')||caption.includes('\uFFFD'))throw Error('INVALID_UNICODE');
 return{...clip,title,caption};
}
export async function addCloudCaptions(manifest,fetcher=fetch){
 const titles=new Map(),items=[];
 for(const clip of manifest.items||[]){
  if(!/^[A-Za-z0-9_-]{11}$/.test(String(clip.source)))throw Error('INVALID_SOURCE');
  if(!titles.has(clip.source)){
   const u=new URL('https://www.youtube.com/oembed');u.searchParams.set('url','https://www.youtube.com/watch?v='+clip.source);u.searchParams.set('format','json');
   const resp=await fetcher(u,{signal:AbortSignal.timeout(12000)});
   if(!resp.ok)throw Error('YOUTUBE_OEMBED_HTTP_'+resp.status);
   const info=await resp.json();titles.set(clip.source,cleanTitle(info.title));
  }
  items.push(captionForClip(titles.get(clip.source),clip));
 }
 return{...manifest,items,caption_source:'youtube_oembed',ai_tokens_per_publication:0};
}
if(process.argv[1]?.replaceAll('\\','/').endsWith('/cortes_threads_cloud_captions.mjs')){
 try{const src=JSON.parse(await fs.readFile(process.argv[2],'utf8'));const out=await addCloudCaptions(src);
 await fs.writeFile(process.argv[3],JSON.stringify(out,null,2)+'\n','utf8');
 console.log(JSON.stringify({ok:true,total:out.items.length,caption_source:out.caption_source,ai_tokens_per_publication:0}));}
 catch(e){console.error('::error title=Threads Cloud Caption::'+e.message);process.exitCode=1;}
}