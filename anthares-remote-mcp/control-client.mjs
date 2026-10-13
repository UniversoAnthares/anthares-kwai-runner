import { signControlRequest } from './service-signing.mjs';

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const target = new URL(path, controlOrigin.replace(/\/$/, '') + '/');
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
        'User-Agent': 'AntharesRemoteMCP/0.5',
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
