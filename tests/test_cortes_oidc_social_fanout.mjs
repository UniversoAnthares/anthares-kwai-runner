import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync('vercel-ara-primary/api/cortes-queue.mjs','utf8');
const start=source.indexOf('function validOidcProducerPayload(body){');
const end=source.indexOf('\nasync function ensureSchema()',start);
assert(start>=0&&end>start,'OIDC validator must exist');
const script=source.slice(start,end)+'\nvalidOidcProducerPayload';
const sha256hex=x=>crypto.createHash('sha256').update(String(x)).digest('hex');
const validate=vm.runInNewContext(script,{URL,sha256hex,Number,String,Object});
const accounts={instagram:'universoanthares',pinterest:'lucasyahn',linkedin:'primary'};
for(const [platform,account] of Object.entries(accounts)){
 const source_id='video_ABC',segment_id='segment_27',target_key=platform+':'+account;
 const media_url='https://anthares.us/wp-content/uploads/2026/10/example.mp4';
 const id='cortes-fanout-'+platform+'-'+sha256hex(source_id+'|'+segment_id+'|'+target_key).slice(0,32);
 const row={id,dedupe_key:id,executor:'social_video',platform,target_key,account_id:account,
  master_id:source_id,source_id,segment_id,duration_class:'short',duration_seconds:45,
  source_start:1000,source_end:46000,media_sha256:sha256hex(source_id+'|'+segment_id+'|'+media_url),
  media_url,video_url:media_url,title:'Vídeo Anthares',cortes_attachment_id:32};
 assert.equal(validate(row),true,platform+' allowed');
 const bad=[
  {...row,target_key:'kwai:lucasrosalem'}, {...row,executor:'other'},
  {...row,account_id:'other'}, {...row,media_url:'https://evil.example/video.mp4',video_url:'https://evil.example/video.mp4'},
  {...row,media_url:'https://anthares.us.evil.org/video.mp4',video_url:'https://anthares.us.evil.org/video.mp4'},
  {...row,title:''},{...row,source_id:'forged'},{...row,id:'forged'},
  {...row,media_sha256:'a'.repeat(64)},{...row,duration_seconds:200},
  {...row,cortes_attachment_id:0},{...row,source_end:500},
 ];
 bad.forEach((x,i)=>assert.equal(validate(x),false,platform+' forged case '+i));
}
const kwai={platform:'kwai',executor:'github',target_key:'kwai:lucasrosalem',expected_account:'lucasrosalem',
 video_url:'https://anthares.us/video.mp4',cortes_callback_url:'https://anthares.us/wp-json/anthares/v1/cortes/clip-network-callback',cortes_callback_token:'nonempty'};
assert.equal(validate(kwai),true,'existing Kwai OIDC payload remains supported');
assert.equal(validate({...kwai,cortes_callback_token:''}),false,'Kwai callback must be signed');
console.log('CORTES_OIDC_THREE_SOCIAL_TARGETS=PASS');
