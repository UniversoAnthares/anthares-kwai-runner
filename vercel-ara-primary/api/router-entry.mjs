import crypto from 'node:crypto';

if (!process.env.ARA_PUBLIC_ORIGIN) {
  process.env.ARA_PUBLIC_ORIGIN = 'https://anthares-ara-vercel-reserve.vercel.app';
}
if (!process.env.ARA_OAUTH_TOKEN_SECRET && process.env.DATABASE_URL) {
  process.env.ARA_OAUTH_TOKEN_SECRET = crypto
    .createHash('sha256')
    .update(`${process.env.DATABASE_URL}:anthares-remote-oauth-v1`)
    .digest('base64url');
}
if (!process.env.ARA_OWNER_APPROVAL_HASH) {
  process.env.ARA_OWNER_APPROVAL_HASH = 'a0a20fa0c73cc242b53aeb2dd582b4a342fc4a108ec9cd483cf6dddba8d3d52b';
}

const mod = await import('./router.mjs');
export default mod.default;
