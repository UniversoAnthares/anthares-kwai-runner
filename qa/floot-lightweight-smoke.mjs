// Anthares lightweight QA: standalone Node 22, no paid CI runner.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const BASE = 'https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/';
const paths = ['ci/shared/provider-smoke.sh', '.circleci/config.yml'];
const results = [];
for (const path of paths) {
  const response = await fetch(BASE + path, { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, 'HTTP '+response.status+' '+path);
  const source = await response.text();
  assert.ok(source.length > 20, 'Empty file: '+path);
  results.push({ path, bytes: source.length, sha256: createHash('sha256').update(source).digest('hex') });
}
assert.match((await (await fetch(BASE+'.circleci/config.yml')).text()), /provider_smoke/);
console.log(JSON.stringify({ok:true, executor:'node22', checks:results},null,2));
