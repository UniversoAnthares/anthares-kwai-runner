import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const core = readFileSync('infra/neon-cortes-queue/index.mjs', 'utf8');
const edge = readFileSync('infra/cloudflare-cortes-queue-ha/src/index.js', 'utf8');
const standby = readFileSync('cloudflare-cortes-queue-ha/src/index.mjs', 'utf8');

test('all three production modules pass node syntax checks', () => {
  for (const file of [
    'infra/neon-cortes-queue/index.mjs',
    'infra/cloudflare-cortes-queue-ha/src/index.js',
    'cloudflare-cortes-queue-ha/src/index.mjs',
  ]) {
    const r = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
    assert.equal(r.status, 0, file + ': ' + r.stderr.slice(0, 500));
  }
});

test('Kwai publication remains off by default even with an OIDC issuer', () => {
  assert.ok(core.includes("process.env.CORTES_KWAI_CLOUD_PUBLISH_ENABLED!=='1'"));
  assert.ok(core.includes("actor.workflow!=='cortes-kwai-cloud-publisher.yml'"));
  assert.ok(core.includes("actor.workflow!=='cortes-kwai-dispatch-refill.yml'"));
  assert.ok(core.includes("u.status='uncertain'"));
  assert.ok(core.includes('KWAI_UNCERTAIN_HOLD_OR_CONCURRENT_WRITE'));
});

test('account, fingerprint, remote readback and fencing guards remain present', () => {
  assert.ok(core.includes("const KWAI_TARGET='kwai:lucasrosalem'"));
  assert.ok(core.includes("b.media_sha256!==sha(source+'|'+segment+'|'+media)"));
  assert.ok(core.includes("proof.kind!=='kwai_account_media_readback_verified'"));
  assert.ok(core.includes("p.split('/').filter(Boolean).pop()!==remote"));
  assert.ok(core.includes("lease_generation=$4"));
  assert.ok(core.includes("cortes_daily_publication_budget.reserved<100"));
});

test('both Workers only relay Kwai actions after bearer validation', () => {
  for (const src of [edge, standby]) {
    for (const action of ['kwai-uncertain-read','kwai-enqueue','kwai-lease','kwai-start','kwai-confirm','kwai-fail']) {
      assert.ok(src.includes(action), 'missing '+action);
    }
    assert.ok(src.includes('Bearer '));
  }
});

test('unsigned write is rejected by Neon function before querying database', async () => {
  const mod = await import('../infra/neon-cortes-queue/index.mjs');
  for (const action of ['kwai-uncertain-read','kwai-enqueue','kwai-lease','kwai-start','kwai-confirm','kwai-fail']) {
    const request = new Request('https://neon.invalid/?action='+action, {
      method:'POST',headers:{'content-type':'application/json'},body:'{}'
    });
    const response = await mod.default.fetch(request);
    assert.equal(response.status,401,action);
  }
});
