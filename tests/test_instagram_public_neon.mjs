import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
const a=source.indexOf('async function instagramDirectAction(');
const b=source.indexOf('\nexport function validatePinterestTerminalErrorProof(',a);
assert.ok(a>=0&&b>a);
const snippet=source.slice(a,b)+'\nthis.direct=instagramDirectAction;';
const FUTURE_NOW=Date.parse('2026-11-16T14:00:00Z');
class TestDate extends Date {
  constructor(...args){super(...(args.length?args:[FUTURE_NOW]));}
  static now(){return FUTURE_NOW;}
}

function mock(evidence={}, started=new Date(FUTURE_NOW-48*3600e3).toISOString()){
  const statements=[];
  const context={URL,Date:TestDate,JSON,String,Number,Object,Set,Math,
    sha:s=>crypto.createHash('sha256').update(String(s)).digest('hex'),
    query:async (sql,p=[])=>{
      statements.push({sql,params:p});
      if(sql.includes('SELECT id,publication_started_at,confirmation_evidence')){
        return [{id:p[0],publication_started_at:started,confirmation_evidence:evidence}];
      }
      if(sql.includes('UPDATE cortes_publications')){
        return [{id:p[0],status:sql.includes("status='failed'")?'failed':'confirmed',
                 remote_id:p[2]||null}];
      }
      return [];
    }};
  vm.runInNewContext(snippet,context,{timeout:4000});
  return {call:context.direct,statements};
}
function proof(id,start){
 const tag='#antharescorte'+crypto.createHash('sha256').update(id).digest('hex').slice(0,12);
 const when=new Date(start).getTime();
 return {username:'universoanthares',origin:'instagram_public_profile',
  profile_url:'https://www.instagram.com/universoanthares/reels/',
  complete:true,graph_complete:true,scanned_count:75,graph_scanned_count:92,
  tag,observed_at:new Date(FUTURE_NOW).toISOString(),newest_at:new Date(when+3*3600e3).toISOString(),
  oldest_at:new Date(when-3*3600e3).toISOString(),
  graph_oldest_at:new Date(when-3*3600e3).toISOString(),
  matching_caption_tag:false,graph_matching_tag:false};
}
const id='cortes-fanout-instagram-'+'a'.repeat(32);
test('reject incomplete public timeline without database changes',async()=>{
  const h=mock();
  const p=proof(id,new Date(FUTURE_NOW-48*3600e3));p.complete=false;
  const r=await h.call('reconcile',{id,decision:'absent',proof:p});
  assert.equal(r.error,'DIRECT_PUBLIC_PROOF_INCOMPLETE');
  assert.equal(h.statements.length,0);
});
test('bounded per-account pending action',async()=>{
  const h=mock();
  assert.equal((await h.call('pending',{limit:51})).ok,false);
  const r=await h.call('pending',{limit:20});
  assert.equal(r.ok,true);
  assert.equal(h.statements.length,1);
  assert.equal(h.statements[0].params[0],'instagram:universoanthares');
  assert.match(h.statements[0].sql,/status='uncertain'/);
});
test('first complete absence adds audit without changing failed state',async()=>{
  const h=mock();
  const r=await h.call('reconcile',{id,decision:'absent',proof:proof(id,new Date(FUTURE_NOW-48*3600e3))});
  assert.equal(r.ok,true);
  assert.equal(r.first_scan_complete,true);
  assert.match(h.statements[1].sql,/confirmation_evidence=/);
  assert.doesNotMatch(h.statements[1].sql,/status='failed'/);
});
test('second complete scan after one hour marks failed, never queued',async()=>{
  const old=new Date(FUTURE_NOW-2*3600e3).toISOString();
  const h=mock({kind:'instagram_public_absence_first_pass',first_scan_at:old});
  const r=await h.call('reconcile',{id,decision:'absent',proof:proof(id,new Date(FUTURE_NOW-48*3600e3))});
  assert.equal(r.ok,true);
  assert.match(h.statements[1].sql,/status='failed'/);
  assert.doesNotMatch(h.statements[1].sql,/status='queued'/);
});
test('reject absent without separate Graph absence',async()=>{
 const h=mock();const p=proof(id,new Date(FUTURE_NOW-48*3600e3));
 p.graph_matching_tag=true;
 const r=await h.call('reconcile',{id,decision:'absent',proof:p});
 assert.equal(r.error,'DIRECT_PUBLIC_ABSENCE_UNPROVEN');
});
test('exact public and Graph permalink can confirm with remote media id',async()=>{
 const h=mock();const p=proof(id,new Date(FUTURE_NOW-48*3600e3));
 const permalink='https://www.instagram.com/reel/XyzQ987/';
 p.matching_caption_tag=true;p.graph_matching_tag=true;
 p.matched_permalink=permalink;p.graph_permalink=permalink;p.graph_media_id='18123456789012345';
 const r=await h.call('reconcile',{id,decision:'visible',permalink,media_id:p.graph_media_id,proof:p});
 assert.equal(r.ok,true);
 assert.match(h.statements[1].sql,/status='confirmed'/);
});
test('old untagged jobs cannot be reported failed',async()=>{
 const h=mock({},'2026-10-29T05:00:00.000Z');
 const p=proof(id,new Date('2026-10-29T05:00:00.000Z'));
 const r=await h.call('reconcile',{id,decision:'absent',proof:p});
 assert.equal(r.error,'DIRECT_PUBLIC_ABSENCE_TOO_EARLY_OR_LEGACY');
});
