import crypto from 'node:crypto';

const ISSUER = 'https://anthares.us/forgejo/api/actions';
const KEYS = ISSUER + '/.well-known/keys';
const AUDIENCE = 'urn:anthares:forgejo:identity-proof:v1';
const TRUSTED_WORKFLOWS = new Map([
  ['anthares-admin/anthares-ci-sandbox', 'forgejo-identity-proof.yml'],
  ['anthares-admin/anthares-tiktok-forgejo', 'item6-hostinger-readonly-standby.yml'],
]);

function send(res, status, result) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(result));
}

export default async function handler(req, res) {
  if (req.method !== 'GET') return send(res, 405, {ok: false});
  const match = /^Bearer\s+([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/i.exec(String(req.headers.authorization || ''));
  const jwt = match?.[1] || '';
  if (jwt.length < 200 || jwt.length > 16000) return send(res, 401, {ok: false});
  try {
    const segments = jwt.split('.');
    const header = JSON.parse(Buffer.from(segments[0], 'base64url').toString('utf8'));
    const claims = JSON.parse(Buffer.from(segments[1], 'base64url').toString('utf8'));
    const now = Math.floor(Date.now() / 1000);
    const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
    const workflowName = TRUSTED_WORKFLOWS.get(claims.repository);
    const expectedWorkflow = claims.repository + '/.forgejo/workflows/' + workflowName + '@refs/heads/main';
    if (header.alg !== 'RS256' || !/^[A-Za-z0-9_.-]{1,200}$/.test(header.kid || '') ||
        !workflowName || claims.iss !== ISSUER || !aud.includes(AUDIENCE) ||
        claims.repository_owner !== 'anthares-admin' ||
        claims.sub !== 'repo:' + claims.repository + ':ref:refs/heads/main' ||
        claims.ref !== 'refs/heads/main' || claims.workflow_ref !== expectedWorkflow ||
        claims.event_name !== 'workflow_dispatch' ||
        !Number.isInteger(claims.iat) || !Number.isInteger(claims.exp) ||
        claims.iat > now + 60 || claims.exp <= now || claims.exp > now + 3600 ||
        claims.exp - claims.iat > 3600 ||
        (claims.nbf !== undefined && Number(claims.nbf) > now + 60)) {
      return send(res, 401, {ok: false});
    }
    const response = await fetch(KEYS, {signal: AbortSignal.timeout(8000)});
    if (!response.ok) return send(res, 503, {ok: false, code: 'keys_unavailable'});
    const keys = (await response.json()).keys || [];
    const candidates = keys.filter(k => k.kid === header.kid && k.kty === 'RSA' && (!k.alg || k.alg === 'RS256'));
    if (candidates.length !== 1) return send(res, 401, {ok: false});
    const publicKey = crypto.createPublicKey({key: candidates[0], format: 'jwk'});
    const verified = crypto.verify('RSA-SHA256', Buffer.from(segments[0] + '.' + segments[1]), publicKey, Buffer.from(segments[2], 'base64url'));
    return send(res, verified ? 200 : 401, {ok: verified, provider: 'forgejo', role: verified ? 'identity-proof' : null});
  } catch {
    return send(res, 401, {ok: false});
  }
}
