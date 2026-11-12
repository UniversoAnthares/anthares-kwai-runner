import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const backend = readFileSync(new URL('../infra/neon-cortes-queue/index.mjs', import.meta.url),'utf8');
const lead = "SELECT MIN(origin.created_at) FROM cortes_publications origin WHERE origin.target_key=";
test('Instagram Graph and LinkedIn personal direct queues select newest source before old queue records',()=>{
  const instagram = backend.slice(backend.indexOf('async function instagramDirectAction'));
  const personal = backend.slice(backend.indexOf('async function personalAction'));
  assert(instagram.includes(lead));
  assert(personal.includes(lead));
  assert(instagram.includes('FOR UPDATE OF q SKIP LOCKED LIMIT 1'));
  assert(personal.includes('FOR UPDATE OF q SKIP LOCKED LIMIT 1'));
  assert(instagram.includes("status='queued'"));
  assert(personal.includes("status='queued'"));
});
test('Pinterest browser/direct queue prioritizes newest source and preserves fencing',()=>{
  const a = backend.slice(backend.indexOf('async function pinterestBrowserAction'));
  assert(a.includes(lead));
  assert(a.includes('FOR UPDATE OF p SKIP LOCKED LIMIT 1'));
  assert(a.includes('lease_generation'));
  assert(a.includes("status='queued'"));
});
test('Buffer publishers disabled for every destination and Windows fallback',()=>{
  for(const name of ['cortes-buffer-instagram-cloud.yml','cortes-buffer-linkedin-cloud.yml','cortes-buffer-pinterest-cloud.yml','cortes-buffer-instagram-windows-fallback.yml']){
    const src=readFileSync(new URL('../.github/workflows/'+name,import.meta.url),'utf8');
    assert.match(src,/^    if: \$\{\{ false \}\}$/m,name);
  }
});
