import { createPrivateKey, createPublicKey, generateKeyPairSync, sign } from 'node:crypto';

function loadPair() {
  const encoded = process.env.ARA_CONTROL_PRIVATE_KEY_B64 || '';
  if (encoded) {
    const privateKey = createPrivateKey({ key: Buffer.from(encoded, 'base64'), format: 'der', type: 'pkcs8' });
    return { privateKey, publicKey: createPublicKey(privateKey) };
  }
  return generateKeyPairSync('ed25519');
}

const pair = loadPair();
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
