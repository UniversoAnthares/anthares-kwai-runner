import { signControlRequest } from './service-signing.mjs';

const PRIMARY_CONTROL = 'https://anthares-ara-control.onrender.com';
const SECONDARY_CONTROL = 'https://anthares-ara-infra-canary-v2.onrender.com';
const ALLOWED_CONTROLS = new Set([PRIMARY_CONTROL, SECONDARY_CONTROL]);
const FAILOVER_STATUSES = new Set([404, 500, 502, 503, 504]);

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

function controlOrigins(preferred) {
  const first = safeControlOrigin(preferred);
  return [first, ...[PRIMARY_CONTROL, SECONDARY_CONTROL].filter(origin => origin !== first)];
}

async function signedFetchOnce(origin, path, method, payload, timeoutMs) {
  const target = new URL(path, origin + '/');
  const canonical = `${target.pathname}${target.search}`;
  const signed = signControlRequest(method, canonical, payload);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(target, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'AntharesRemoteMCP/0.7',
        'X-ARA-Timestamp': signed.timestamp,
        'X-ARA-Signature': signed.signature,
        'X-ARA-Signer': 'anthares-remote-mcp',
      },
      body: payload === '' ? undefined : payload,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const payload = body === undefined ? '' : JSON.stringify(body);
  let lastResponse = null;
  let lastError = null;
  for (const origin of controlOrigins(controlOrigin)) {
    try {
      const response = await signedFetchOnce(origin, path, method, payload, timeoutMs);
      lastResponse = response;
      if (!FAILOVER_STATUSES.has(response.status)) return response;
    } catch (error) {
      lastError = error;
    }
  }
  if (lastResponse) return lastResponse;
  throw lastError || new Error('all ARA control origins unavailable');
}

export const controlFailoverOrigins = Object.freeze([PRIMARY_CONTROL, SECONDARY_CONTROL]);
