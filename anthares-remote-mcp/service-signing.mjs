import { generateKeyPairSync, sign } from 'node:crypto';

const pair = generateKeyPairSync('ed25519');
const publicPem = pair.publicKey.export({ type: 'spki', format: 'pem' });

export function servicePublicKey() {
  return String(publicPem);
}

export function signControlRequest(method, path, body = '') {
  const timestamp = String(Date.now());
  const payload = `${timestamp}\n${method.toUpperCase()}\n${path}\n${body}`;
  const signature = sign(null, Buffer.from(payload), pair.privateKey).toString('base64url');
  return { timestamp, signature };
}
