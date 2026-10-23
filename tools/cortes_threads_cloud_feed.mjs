import fs from 'node:fs/promises';
import path from 'node:path';
const API='https://anthares.us/wp-json/wp/v2/media';
const EVIDENCE_FILE=new URL('../config/threads-verified-transcripts.json',import.meta.url);
async function evidenceRegistry(){
 const doc=JSON.parse(await fs.readFile(EVIDENCE_FILE,'utf8'));
 if(doc.schema!=='anthares.threads.clip-evidence-registry.v1'||!doc.items||typeof doc.items!=='object')
  throw Error('TRANSCRIPT_REGISTRY_INVALID');
 return doc.items;
}
const FILE=/^https:\/\/anthares\.us\/wp-content\/uploads\/anthares-clips\/\d{4}\/\d{2}\/short_([A-Za-z0-9_-]{11})_g(\d+)_(\d+)_(\d+)\.mp4$/;
export const localDay=(d=new Date())=>new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Campo_Grande',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);
export function clipFromMedia(m,day){
 if(!m||m.mime_type!=='video/mp4'||String(m.date||'').slice(0,10)!==day)return null;
 const url=String(m.source_url||''),z=FILE.exec(url);if(!z)return null;
 const [,source,round,a,b]=z,start=Number(a),end=Number(b);
 if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||end-start<5||end-start>180)return null;
 const clip_id='g'+round+':'+source+':'+start+':'+end;
 return{id:source+'|'+clip_id,clip_id,source,date:day,attachment_id:m.id,duration:end-start,url,stored_at:m.date_gmt||m.date,
  editorial:{title:m.title?.rendered||'',description:m.description?.rendered||'',caption:m.caption?.rendered||'',alt_text:m.alt_text||''}};
}
export async function fetchCloudManifest({fetcher=fetch,day=localDay(),maxPages=12}={}){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(day))throw Error('INVALID_DATE');
 let totalPages=1,pageCount=0;const unique=new Map();
 for(let page=1;page<=Math.min(totalPages,maxPages);page++){
  const u=new URL(API);for(const [k,v] of Object.entries({search:'short_',per_page:100,page,orderby:'date',order:'desc'}))u.searchParams.set(k,String(v));
  const res=await fetcher(u,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(20000)});
  if(!res.ok)throw Error('WORDPRESS_HTTP_'+res.status);
  const rows=await res.json();if(!Array.isArray(rows))throw Error('WORDPRESS_NOT_ARRAY');
  const n=Number(res.headers.get('X-WP-TotalPages')||1);totalPages=Number.isInteger(n)&&n>0?n:1;
  pageCount++;for(const item of rows){const c=clipFromMedia(item,day);if(c)unique.set(c.id,c);}
  if(rows.length<100)break;
 }
 const approved=await evidenceRegistry();
 const items=[...unique.values()].map(c=>{
  const e=approved[c.id];
  if(!e)return c; // Fail closed: captionForClip rejects absent proof.
  return {...c,editorial:{...c.editorial,
   title:e.title,description:e.description,
   caption:e.hashtags.join(' '),alt_text:e.keywords.join(', '),
   transcript_attestation:e.transcript_attestation}};
 }).sort((a,b)=>a.stored_at.localeCompare(b.stored_at)||a.id.localeCompare(b.id));
 return{day,source:'wp-rest-media',total:items.length,pages:pageCount,items};
}
if(process.argv[1]?.replaceAll('\\','/').endsWith('/cortes_threads_cloud_feed.mjs')){
 try{const data=await fetchCloudManifest({day:process.env.CORTES_DAY||localDay()}),dest=process.argv[2];
 if(dest){await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,JSON.stringify(data,null,2)+'\n','utf8');}
 console.log(JSON.stringify({ok:true,day:data.day,total:data.total,pages:data.pages,pc_independent:true}));}
 catch(e){const detail=[e.message,e.cause?.code,e.cause?.message].filter(Boolean).join(' | ').slice(0,250);console.error('::error title=Threads Cloud Feed::'+detail);process.exitCode=1;}
}