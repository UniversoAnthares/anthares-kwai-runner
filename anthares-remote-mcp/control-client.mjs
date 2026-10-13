import { signControlRequest } from './service-signing.mjs';

const PRIMARY_CONTROL = 'https://anthares-ara-control.onrender.com';
const ALLOWED_CONTROLS = new Set([
  PRIMARY_CONTROL,
  'https://anthares-ara-infra-canary-v2.onrender.com',
]);

function safeControlOrigin(value) {
  try {
    const parsed = new URL(String(value || PRIMARY_CONTROL));
    const origin = parsed.origin.replace(/\/$/, '');
    if (parsed.protocol === 'https:' && parsed.pathname === '/' && !parsed.search && !parsed.hash && ALLOWED_CONTROLS.has(origin)) {
      return origin;
    }
  } catch {}
  return PRIMARY_CONTROL;
}

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const target = new URL(path, safeControlOrigin(controlOrigin) + '/');
  const payload = body === undefined ? '' : JSON.stringify(body);
  const canonical = `${target.pathname}${target.search}`;
  const signed = signControlRequest(method, canonical, payload);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(target, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'AntharesRemoteMCP/0.6',
        'X-ARA-Timestamp': signed.timestamp,
        'X-ARA-Signature': signed.signature,
        'X-ARA-Signer': 'anthares-remote-mcp',
      },
      body: body === undefined ? undefined : payload,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}
