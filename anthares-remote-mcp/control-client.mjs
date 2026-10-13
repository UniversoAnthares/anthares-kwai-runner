import { randomUUID } from 'node:crypto';
import { signControlRequest } from './service-signing.mjs';
import { executeViaIssueQueue, issueQueueConfigured, IssueQueueUncertainError } from './github-issue-queue-client.mjs';

const PRIMARY_CONTROL = 'https://anthares-ara-control.onrender.com';
const SECONDARY_CONTROL = 'https://anthares-ara-infra-canary-v2.onrender.com';
const TERTIARY_CONTROL = 'https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run';
const QUATERNARY_CONTROL = 'https://anthares-ara-backup.anthares1.workers.dev';
const ALL_CONTROLS = Object.freeze([PRIMARY_CONTROL, SECONDARY_CONTROL, TERTIARY_CONTROL, QUATERNARY_CONTROL]);
const ALLOWED_CONTROLS = new Set(ALL_CONTROLS);
const FAILOVER_STATUSES = new Set([404, 500, 502, 503, 504]);
const RETRYABLE_STATUS = new Set([502, 503, 504]);
const RETRY_DELAYS_MS = [150, 400];
const EXECUTION_TRANSPORT = String(process.env.ARA_EXECUTION_TRANSPORT || 'github-primary').trim().toLowerCase();

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function safeControlOrigin(value) {
  try {
    const parsed = new URL(String(value || PRIMARY_CONTROL));
    const origin = parsed.origin.replace(/\/$/, '');
    if (parsed.protocol === 'https:' && parsed.pathname === '/' && !parsed.search && !parsed.hash && ALLOWED_CONTROLS.has(origin)) return origin;
  } catch {}
  return PRIMARY_CONTROL;
}

function controlOrigins(preferred) {
  const first = safeControlOrigin(preferred);
  return [first, ...ALL_CONTROLS.filter(origin => origin !== first)];
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
}

function seenAtMs(data) {
  const raw = data?.seen_at || data?.heartbeat?.seen_at || data?.heartbeat?.time || '';
  const ms = Date.parse(String(raw));
  return Number.isFinite(ms) ? ms : 0;
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
          'User-Agent': 'AntharesRemoteMCP/0.11',
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
    } finally { clearTimeout(timer); }
    const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)];
    if (Date.now() + delay >= deadline) break;
    await sleep(delay);
  }
  if (lastError) throw lastError;
  throw new Error('control request deadline exceeded');
}

async function probeStatus(origin, deviceId, deadline) {
  const remaining = deadline - Date.now();
  if (remaining <= 0) return null;
  const probeDeadline = Date.now() + Math.min(8000, remaining);
  try {
    const response = await signedFetchWithRetry(origin, `/v1/mcp/status?device_id=${encodeURIComponent(deviceId)}`, 'GET', undefined, probeDeadline);
    const raw = await response.text();
    let data = {};
    try { data = raw ? JSON.parse(raw) : {}; } catch { data = { raw }; }
    return { origin, status: response.status, ok: response.ok, data };
  } catch (error) { return { origin, status: 0, ok: false, data: {}, error }; }
}

async function chooseActiveControl(preferred, deviceId, deadline) {
  const origins = controlOrigins(preferred);
  const probes = (await Promise.all(origins.map(origin => probeStatus(origin, deviceId, deadline)))).filter(Boolean);
  const healthy = probes.filter(p => p.ok);
  const connected = healthy.filter(p => p.data?.connected === true);
  const candidates = connected.length ? connected : healthy;
  candidates.sort((a, b) => {
    const connectedDelta = Number(b.data?.connected === true) - Number(a.data?.connected === true);
    if (connectedDelta) return connectedDelta;
    const seenDelta = seenAtMs(b.data) - seenAtMs(a.data);
    if (seenDelta) return seenDelta;
    return origins.indexOf(a.origin) - origins.indexOf(b.origin);
  });
  return { selected: candidates[0] || null, probes };
}

async function aggregateStatus(preferred, path, deadline) {
  const target = new URL(path, PRIMARY_CONTROL + '/');
  const deviceId = target.searchParams.get('device_id') || '';
  if (!deviceId) return jsonResponse({ error: 'missing_device_id' }, 400);
  const { selected, probes } = await chooseActiveControl(preferred, deviceId, deadline);
  if (selected) {
    return jsonResponse({
      ...selected.data,
      control_origin: selected.origin,
      control_failover: selected.origin !== safeControlOrigin(preferred),
      execution_transport: issueQueueConfigured() && EXECUTION_TRANSPORT !== 'control-only' ? 'github-issues-primary' : 'control-primary',
      github_queue_configured: issueQueueConfigured(),
      control_candidates: probes.filter(p => p.ok).map(p => ({ origin: p.origin, connected: p.data?.connected === true, seen_at: p.data?.seen_at || null })),
    }, selected.status || 200);
  }
  return jsonResponse({ error: 'all ARA control origins unavailable', execution_transport: issueQueueConfigured() ? 'github-issues-primary' : 'control-primary', github_queue_configured: issueQueueConfigured() }, 503);
}

async function consumeOauthCentrally(path, requestBody, deadline) {
  let lastError = null;
  for (const origin of [PRIMARY_CONTROL, SECONDARY_CONTROL]) {
    try {
      const response = await signedFetchWithRetry(origin, path, 'POST', requestBody, deadline);
      if (!FAILOVER_STATUSES.has(response.status) || origin === SECONDARY_CONTROL) return response;
      await response.arrayBuffer().catch(() => {});
    } catch (error) { lastError = error; }
  }
  throw lastError || new Error('durable OAuth control unavailable');
}

async function executeViaPreferredTransport(controlOrigin, path, requestBody, deadline) {
  const useGithub = EXECUTION_TRANSPORT !== 'control-only' && issueQueueConfigured();
  if (useGithub) {
    try {
      const result = await executeViaIssueQueue({
        deviceId: String(requestBody?.device_id || '').trim(),
        type: String(requestBody?.type || '').trim(),
        args: requestBody?.args && typeof requestBody.args === 'object' ? requestBody.args : {},
        timeoutSeconds: Number(requestBody?.timeout_seconds || 30),
      });
      return jsonResponse(result, 200);
    } catch (error) {
      if (error instanceof IssueQueueUncertainError || error?.issueQueueSubmitted !== false) {
        return jsonResponse({ error: 'github_queue_execution_uncertain', message: error.message, details: error.details || {}, fallback_suppressed: true }, 504);
      }
      if (EXECUTION_TRANSPORT === 'github-only') {
        return jsonResponse({ error: 'github_queue_unavailable', message: error.message }, 503);
      }
      // Safe fallback: submission failed before GitHub accepted the job, so duplicate execution is impossible.
    }
  } else if (EXECUTION_TRANSPORT === 'github-only') {
    return jsonResponse({ error: 'github_queue_not_configured' }, 503);
  }

  const deviceId = String(requestBody?.device_id || '').trim();
  if (!deviceId) return jsonResponse({ error: 'missing_device_id' }, 400);
  const { selected } = await chooseActiveControl(controlOrigin, deviceId, deadline);
  if (!selected || selected.data?.connected !== true) return jsonResponse({ error: 'no connected ARA control for device' }, 503);
  return signedFetchWithRetry(selected.origin, path, 'POST', requestBody, deadline);
}

export async function signedControlFetch(controlOrigin, path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const upperMethod = String(method || 'GET').toUpperCase();
  const pathname = new URL(path, PRIMARY_CONTROL + '/').pathname;
  let requestBody = body;
  if (upperMethod === 'POST' && pathname === '/v1/mcp/execute' && requestBody && typeof requestBody === 'object' && !Array.isArray(requestBody) && !requestBody.idempotency_key) {
    requestBody = { ...requestBody, idempotency_key: randomUUID() };
  }
  const deadline = Date.now() + Math.max(1000, timeoutMs);
  if (upperMethod === 'GET' && pathname === '/v1/mcp/status') return aggregateStatus(controlOrigin, path, deadline);
  if (upperMethod === 'POST' && pathname === '/v1/mcp/oauth/consume') return consumeOauthCentrally(path, requestBody, deadline);
  if (upperMethod === 'POST' && pathname === '/v1/mcp/execute') return executeViaPreferredTransport(controlOrigin, path, requestBody, deadline);

  const origins = controlOrigins(controlOrigin);
  let lastError = null;
  for (let index = 0; index < origins.length; index++) {
    const origin = origins[index];
    if (deadline - Date.now() <= 0) break;
    try {
      const response = await signedFetchWithRetry(origin, path, upperMethod, requestBody, deadline);
      const canFailOver = index < origins.length - 1;
      if (!FAILOVER_STATUSES.has(response.status) || !canFailOver) return response;
      await response.arrayBuffer().catch(() => {});
    } catch (error) { lastError = error; }
  }
  throw lastError || new Error('all ARA control origins unavailable');
}

export const controlFailoverOrigins = ALL_CONTROLS;
export const executionTransport = Object.freeze({ mode: EXECUTION_TRANSPORT, githubConfigured: issueQueueConfigured() });
