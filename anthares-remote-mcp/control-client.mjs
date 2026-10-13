import { randomUUID } from 'node:crypto';
import { signControlRequest } from './service-signing.mjs';

const RETRYABLE_STATUS = new Set([502, 503, 504]);
const RETRY_DELAYS_MS = [150, 400];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const target = new URL(path, controlOrigin.replace(/\/$/, '') + '/');
  const upperMethod = String(method || 'GET').toUpperCase();

  // The control plane deduplicates /v1/mcp/execute by this key. Inject it here
  // so a transient Render 502/503/504 can be retried without executing a
  // destructive device operation twice.
  let requestBody = body;
  if (
    upperMethod === 'POST' &&
    target.pathname === '/v1/mcp/execute' &&
    requestBody &&
    typeof requestBody === 'object' &&
    !Array.isArray(requestBody) &&
    !requestBody.idempotency_key
  ) {
    requestBody = { ...requestBody, idempotency_key: randomUUID() };
  }

  const payload = requestBody === undefined ? '' : JSON.stringify(requestBody);
  const canonical = `${target.pathname}${target.search}`;
  const idempotent = upperMethod === 'GET' || upperMethod === 'HEAD' || Boolean(requestBody?.idempotency_key);
  const attempts = idempotent ? 3 : 1;
  const deadline = Date.now() + Math.max(1000, timeoutMs);
  let lastError;

  for (let attempt = 0; attempt < attempts; attempt++) {
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;

    const signed = signControlRequest(upperMethod, canonical, payload);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), remaining);

    try {
      const response = await fetch(target, {
        method: upperMethod,
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

      if (!RETRYABLE_STATUS.has(response.status) || attempt === attempts - 1) {
        return response;
      }

      // Drain before retrying so the connection can be reused cleanly.
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
