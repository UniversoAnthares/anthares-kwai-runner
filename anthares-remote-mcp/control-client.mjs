import { randomUUID } from 'node:crypto';
import { signControlRequest } from './service-signing.mjs';

const PRIMARY_CONTROL = 'https://anthares-ara-control.onrender.com';
const SECONDARY_CONTROL = 'https://anthares-ara-infra-canary-v2.onrender.com';
const ALLOWED_CONTROLS = new Set([PRIMARY_CONTROL, SECONDARY_CONTROL]);
const FAILOVER_STATUSES = new Set([404, 500, 502, 503, 504]);
const RETRYABLE_STATUS = new Set([502, 503, 504]);
const RETRY_DELAYS_MS = [150, 400];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function safeControlOrigin(value) {
  try {
    const parsed = new URL(String(value || PRIMARY_CONTROL));
    const origin = parsed.origin.replace(/\/$/, '');
    if (
      parsed.protocol === 'https:' &&
      parsed.pathname === '/' &&
      !parsed.search &&
      !parsed.hash &&
      ALLOWED_CONTROLS.has(origin)
    ) return origin;
  } catch {}
  return PRIMARY_CONTROL;
}

function controlOrigins(preferred) {
  const first = safeControlOrigin(preferred);
  return [first, ...[PRIMARY_CONTROL, SECONDARY_CONTROL].filter(origin => origin !== first)];
}

async function signedFetchWithRetry(origin, path, method, requestBody, deadline) {
  const target = new URL(path, origin + '/');
  const canonical = `${target.pathname}${target.search}`;
  const payload = requestBody === undefined ? '' : JSON.stringify(requestBody);
  const idempotent = method === 'GET' || method === 'HEAD' || Boolean(requestBody?.idempotency_key);
  const attempts = idempotent ? 3 : 1;
  let lastError = null;

  for (let attempt = 0; attempt < attempts; attempt++) {
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;
    const signed = signControlRequest(method, canonical, payload);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), remaining);
    try {
      const response = await fetch(target, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'AntharesRemoteMCP/0.8',
          'X-ARA-Timestamp': signed.timestamp,
          'X-ARA-Signature': signed.signature,
          'X-ARA-Signer': 'anthares-remote-mcp',
        },
        body: requestBody === undefined ? undefined : payload,
        signal: controller.signal,
      });
      if (!RETRYABLE_STATUS.has(response.status) || attempt === attempts - 1) return response;
      await response.arrayBuffer().catch(() => {});
    } catch (error) {
      lastError = error;
      if (attempt === attempts - 1) throw error;
    } finally {
      clearTimeout(timer);
    }
    const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)];
    if (Date.now() + delay >= deadline) break;
    await sleep(delay);
  }

  if (lastError) throw lastError;
  throw new Error('control request deadline exceeded');
}

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const upperMethod = String(method || 'GET').toUpperCase();
  let requestBody = body;

  if (
    upperMethod === 'POST' &&
    new URL(path, PRIMARY_CONTROL + '/').pathname === '/v1/mcp/execute' &&
    requestBody &&
    typeof requestBody === 'object' &&
    !Array.isArray(requestBody) &&
    !requestBody.idempotency_key
  ) {
    requestBody = { ...requestBody, idempotency_key: randomUUID() };
  }

  const deadline = Date.now() + Math.max(1000, timeoutMs);
  const origins = controlOrigins(controlOrigin);
  let lastError = null;

  for (let index = 0; index < origins.length; index++) {
    const origin = origins[index];
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;
    try {
      const response = await signedFetchWithRetry(origin, path, upperMethod, requestBody, deadline);
      const canFailOver = index < origins.length - 1;
      if (!FAILOVER_STATUSES.has(response.status) || !canFailOver) return response;
      await response.arrayBuffer().catch(() => {});
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('all ARA control origins unavailable');
}

export const controlFailoverOrigins = Object.freeze([PRIMARY_CONTROL, SECONDARY_CONTROL]);
