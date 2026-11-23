import test from 'node:test';
import assert from 'node:assert/strict';

process.env.COMMENT_ACCOUNT='universo.anthares';
const {default:service}=await import('../infra/neon-tiktok-comment-recovery/index.mjs');
const root='https://example.invalid/';

test('new recovery ledger is comment-only and rejects unauthenticated reads',async()=>{
  const response=await service.fetch(new Request(root+'?action=comment-pending'));
  assert.equal(response.status,401);
  assert.equal((await response.json()).error,'OIDC_REQUIRED');
});
test('rejects unauthenticated reservations before touching DB',async()=>{
  const response=await service.fetch(new Request(root+'?action=comment-reserve',{
    method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({source_video_id:'7711115854510853383',
      target_video_id:'7708902479219543297',comment_text:'Teste legítimo.'})
  }));
  assert.equal(response.status,401);
});
test('rejects any video publication route',async()=>{
  const response=await service.fetch(new Request(root+'?action=publish'));
  assert.equal(response.status,401);
});
test('unconfigured DB produces a safe 503, no fabricated ledger success',async()=>{
  const response=await service.fetch(new Request(root+'?action=health'));
  assert.equal(response.status,503);
  const body=await response.json();
  assert.equal(body.ok,false);
  assert.equal(body.error,'LEDGER_UNAVAILABLE');
});
