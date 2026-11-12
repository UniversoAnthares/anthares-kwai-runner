import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const backend=readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
const workflow=readFileSync(new URL('../.github/workflows/cortes-linkedin-company-direct-cloud.yml',import.meta.url),'utf8');
test('LinkedIn company has distinct official OIDC authorization and queue fence',()=>{
  assert(backend.includes("wf==='cortes-linkedin-company-direct-cloud.yml'"));
  assert(backend.includes("role='linkedin-company'"));
  assert(backend.includes('async function companyAction('));
  assert(backend.includes("action.startsWith('company-')"));
  assert(backend.includes('lease_generation'));
  assert(backend.includes("status='queued'"));
  assert(backend.includes("FOR UPDATE OF q SKIP LOCKED LIMIT 1"));
});
test('Company uses only official REST organization token; Buffer absent',()=>{
  assert(workflow.includes('LINKEDIN_ACCESS_TOKEN:'));
  assert(workflow.includes('urn:li:organization:145345334'));
  assert(!workflow.includes('BUFFER_API_KEY'));
  assert(workflow.includes('id-token: write'));
  assert(workflow.includes('workflow_dispatch:'));
});

test('HTTP queue adapter explicitly permits the eight fenced company actions',()=>{
 const q=readFileSync(new URL('../tools/cortes_queue_ha.py',import.meta.url),'utf8');
 for(const action of ['lease','start','fail','accepted','confirmed','media-missing','pending','reconcile-public'])
  assert(q.includes('"company-'+action+'"'));
});
