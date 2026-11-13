// Persistent Android (ReDroid) queue identity. Deliberately disabled until
// the real host, dual-account logins, and independent publication are proven.
// Never use phone/MEmu tokens or GitHub OIDC outside their original runtimes.
import crypto from 'node:crypto';

const ALLOWED = new Set(['kwai-lease','kwai-renew','kwai-start',
                         'kwai-confirm','kwai-fail']);
const CLOUD_ROLE = Object.freeze({
  role:'kwai-persistent-cloud',
  workflow:'cloud:android:redroid',
  platform:'kwai',
});
export function persistentCloudEnabled(env=process.env) {
  return env.KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED === '1';
}
export function kwaiPersistentCloudIdentity(request,action,env=process.env) {
  if (!persistentCloudEnabled(env) || request.method !== 'POST' ||
      !ALLOWED.has(action)) return null;
  const expectedHex = String(env.KWAI_PERSISTENT_CLOUD_TOKEN_SHA256 || '');
  if (!/^[0-9a-f]{64}$/.test(expectedHex)) return null;
  const header = String(request.headers?.get('authorization') || '');
  const match = /^Bearer ([A-Za-z0-9_-]{43})$/.exec(header);
  if (!match) return null;
  const expected = Buffer.from(expectedHex,'hex');
  const actual = crypto.createHash('sha256').update(match[1],'utf8').digest();
  if (expected.length !== 32 || !crypto.timingSafeEqual(actual,expected))
    return null;
  return CLOUD_ROLE;
}
// When cloud production is explicitly armed in Neon, fresh local leases and
// STARTED transitions stop. Existing local started jobs can still be renewed
// and independently confirmed to avoid discarding an already uploaded post.
export function localBlockedByCloudCutover(actor,action,env=process.env) {
  return persistentCloudEnabled(env) &&
    (action === 'kwai-lease' || action === 'kwai-start') &&
    ['kwai-physical','kwai-mobile-primary','kwai-mobile'].includes(
      actor?.role);
}
