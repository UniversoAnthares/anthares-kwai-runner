import { readFile, writeFile, chmod } from 'node:fs/promises';
import { randomBytes } from 'node:crypto';

const secretFile = process.env.ARA_OAUTH_SECRET_FILE || '/tmp/anthares-remote-oauth-secret';
if (!process.env.ARA_OAUTH_TOKEN_SECRET || process.env.ARA_OAUTH_TOKEN_SECRET.length < 32) {
  let secret = '';
  try { secret = (await readFile(secretFile, 'utf8')).trim(); } catch {}
  if (secret.length < 32) {
    secret = randomBytes(48).toString('base64url');
    await writeFile(secretFile, secret, { mode: 0o600 });
    await chmod(secretFile, 0o600).catch(() => {});
  }
  process.env.ARA_OAUTH_TOKEN_SECRET = secret;
}
await import('./gateway-v2.mjs');
