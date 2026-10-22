import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const queue=readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
const workflow=readFileSync(new URL('../.github/workflows/cortes-buffer-linkedin-cloud.yml',import.meta.url),'utf8');
test('secondary wakeup is pinned to main branch and trusted upstream workflow',()=>{
  for(const expected of [
    'workflow_run:',
    'workflows: ["CORTES 3 independent networks - all shorts cloud fanout", "CORTES Pinterest - automatic Buffer cloud publisher"]',
    'types: [completed]',
    'branches: [main]'
    "github.event.workflow_run.conclusion == 'success'",
  ]) assert.ok(workflow.includes(expected),expected);
});

test('Neon OIDC allows workflow_run but retains main, audience, repo and signature checks',()=>{
  assert.match(queue,/\['schedule','workflow_dispatch','push','workflow_run'\]\.includes\(claims\.event_name\)/);
  assert.match(queue,/claims\.ref!=='refs\/heads\/main'/);
  assert.match(queue,/claims\.aud/);
  assert.match(queue,/claims\.repository/);
  assert.match(queue,/crypto\.verify\('RSA-SHA256'/);
});
