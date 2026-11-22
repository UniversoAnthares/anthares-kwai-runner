import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const accounts=[
 ['infra/neon-cortes-tiktok/index.mjs','cortes_tiktok_outbound_comments','cortes_tiktok_publications','universo.anthares'],
 ['infra/neon-cortes-lucasrosalem4/index.mjs','cortes_tiktok_lucas4_outbound_comments','cortes_tiktok_lucasrosalem4_publications','lucasrosalem4']
];
for(const [file,table,posts,account] of accounts){
 test(account+' uses an account-isolated persistent comment receipt',()=>{
  const s=fs.readFileSync(file,'utf8');
  assert.ok(s.includes('CREATE TABLE IF NOT EXISTS '+table));
  assert.ok(s.includes('source_video_id text PRIMARY KEY'));
  assert.ok(s.includes("WHERE remote_id=$1 AND status='confirmed'"));
  assert.ok(s.includes("ON CONFLICT(source_video_id) DO NOTHING"));
  assert.ok(s.includes('ORDER BY created_at DESC, source_video_id DESC LIMIT 30'));
  assert.ok(s.includes("FROM "+posts+" "));
  assert.ok(s.includes("WHERE lower(recent.comment_text)=lower($3) OR recent.target_video_id=$2"));
  assert.ok(s.includes("role==='consumer'&&req.method==='POST'&&action==='comment-reserve'"));
  assert.ok(s.includes("role==='consumer'&&req.method==='POST'&&action==='comment-complete'"));
  assert.ok(s.includes("role==='consumer'&&req.method==='GET'&&action==='comment-recent'"));
  assert.ok(s.includes("role==='consumer'&&req.method==='GET'&&action==='comment-pending'"));
  assert.ok(s.includes("AND NOT EXISTS(SELECT 1 FROM "+table));
 });
}
for(const route of ['infra/cloudflare-cortes-tiktok-ha/src/index.js',
                      'infra/cloudflare-cortes-tiktok-lucas4-ha/src/index.js']){
 test(route+' retains OIDC and forwards receipt actions',()=>{
  const s=fs.readFileSync(route,'utf8');
  for(const name of ['comment-pending','comment-recent','comment-reserve','comment-complete'])
   assert.ok(s.includes("'"+name+"'"),name);
  assert.ok(s.includes("oidc_required"));
 });
}
for(const path of ['tools/cortes_tiktok_hosted_publish.py',
                    'tools/cortes_tiktok_lucasrosalem4_cloud_publish.py']){
 test(path+' defers comments to five independent daily windows',()=>{
  const s=fs.readFileSync(path,'utf8');
  assert.ok(s.includes('COMMENT_DEFERRED_TO_SCHEDULE=1'));
  assert.ok(!s.includes('from cortes_tiktok_after_publish_comment import after_confirmed'));
 });
}
test('five daily windows and independent per-account Neon flow',()=>{
 const s=fs.readFileSync('.github/workflows/cortes-tiktok-deferred-comments.yml','utf8');
 for (const clock of ['7 12 * * *','13 15 * * *','19 18 * * *','25 21 * * *','31 1 * * *']) assert.ok(s.includes(clock),clock);
 assert.ok(s.includes('TIKTOK_DEFERRED_ACCOUNT: universo.anthares'));
 assert.ok(s.includes('TIKTOK_DEFERRED_ACCOUNT: lucasrosalem4'));
 assert.ok(s.includes('tools/cortes_tiktok_deferred_comments.py'));
});

test('secondary comment actions use direct Neon despite disabled edge deploy',()=>{
 const s=fs.readFileSync('tools/cortes_tiktok_lucasrosalem4_cloud_publish.py','utf8');
 assert.ok(s.includes('route=QUEUE'));
 assert.ok(s.includes('if action in ("comment-pending","comment-recent","comment-reserve","comment-complete"):'));
 assert.ok(s.includes('route="https://br-crimson-unit-b89nau08-cortestiktok4.compute.c-14.us-east-1.aws.neon.tech/"'));
 assert.ok(s.includes('url=route+"?"'));
 assert.ok(s.includes('if action in ("mirror","claim"):'), 'publication failover preserved');
});
