// CF-06: authenticated, on-demand commands over the existing private GitHub
// issue queue. The PC agent polls GitHub/GitLab independently; this module
// emits zero Cloudflare requests when there is no ChatGPT command.
const ACCOUNT = 'UniversoAnthares';
const REPO = ACCOUNT + '/anthares-ara-queue';
const API = 'https://api.github.com/repos/' + REPO;
const DEFAULT_DEVICE = 'DESKTOP-FTDK0HP';
const MAX_BODY = 60000;
const POLL_MS = 1300;
const RESULT_PREFIX = 'ARA_RESULT_B64 part=';
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function requireToken(env) {
  const token = String(env.ANTHARES_GITHUB_TOKEN || '').trim();
  if (!token) throw new Error('cf06_github_queue_credential_unavailable');
  return token;
}

async function github(env, method, path, body) {
  const token = requireToken(env);
  const response = await fetch(API + path, {
    method,
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': 'Bearer ' + token,
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'Anthares-ARA-Private-Queue/CF06',
      ...(body === undefined ? {} : {'Content-Type':'application/json'})
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    redirect: 'error'
  });
  if (!response.ok) {
    // Do not echo provider response bodies, bearer tokens or URL fragments.
    throw new Error('cf06_github_queue_http_' + response.status);
  }
  return response.status === 204 ? null : response.json();
}

function decodeParts(comments, jobId) {
  const batches = new Map();
  for (const entry of comments) {
    if (!entry || typeof entry.body !== 'string' || entry.user?.login !== ACCOUNT) continue;
    const m = entry.body.match(/^ARA_RESULT_B64 part=(\d+)\/(\d+)\n([A-Za-z0-9+/=\r\n]+)\s*$/);
    if (!m) continue;
    const index = Number(m[1]), total = Number(m[2]);
    if (index < 1 || total < 1 || total > 50 || index > total) continue;
    if (!batches.has(total)) batches.set(total, new Map());
    batches.get(total).set(index, m[3].replace(/\s/g,''));
  }
  for (const [total, parts] of batches.entries()) {
    if (parts.size !== total) continue;
    const joined = Array.from({length:total}, (_,i)=>parts.get(i+1)).join('');
    if (!joined) continue;
    try {
      const decoded = Uint8Array.from(atob(joined), ch=>ch.charCodeAt(0));
      const value = JSON.parse(new TextDecoder().decode(decoded));
      if (value.id === jobId && typeof value.ok === 'boolean') return value;
    } catch { /* Ignore unrelated or incomplete comments. */ }
  }
  return null;
}

async function assertPrivateQueue(env) {
  const meta = await github(env, 'GET', '');
  if (meta?.full_name !== REPO || meta.private !== true || meta.owner?.login !== ACCOUNT) {
    throw new Error('cf06_private_queue_identity_or_visibility_invalid');
  }
}

function normalizedArgs(args) {
  if (!args || typeof args !== 'object' || Array.isArray(args)) return {};
  const result = {};
  for (const [key, value] of Object.entries(args)) {
    if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(key) || key.length > 80) {
      throw new Error('cf06_invalid_argument_key');
    }
    result[key] = typeof value === 'string' ? value : JSON.stringify(value);
  }
  return result;
}

export async function queueExecute(env, type, args = {}, timeout = 30, device = DEFAULT_DEVICE) {
  const deviceId = String(device || DEFAULT_DEVICE);
  if (deviceId !== DEFAULT_DEVICE) throw new Error('cf06_unknown_device');
  if (!/^[a-z][a-z0-9_]{1,50}$/.test(type)) throw new Error('cf06_invalid_command_type');
  const timeoutSeconds = Math.min(120, Math.max(1, Math.ceil(Number(timeout) || 30)));
  await assertPrivateQueue(env);

  const jobId = 'cf06-' + crypto.randomUUID();
  const envelope = {
    job_id: jobId,
    device_id: deviceId,
    type,
    args: normalizedArgs(args),
    timeout_seconds: timeoutSeconds
  };
  const serialized = JSON.stringify(envelope);
  if (serialized.length > MAX_BODY) throw new Error('cf06_queue_payload_too_large');

  // A POST with an unknown outcome is never retried: otherwise an action
  // could be submitted twice with different job identifiers.
  const issue = await github(env, 'POST', '/issues', {
    title: 'ARA CF06 private transport ' + jobId,
    body: serialized,
    labels: ['ara-queued']
  });
  const number = Number(issue?.number || 0);
  if (!Number.isInteger(number) || number <= 0) {
    throw new Error('cf06_queue_created_result_uncertain');
  }

  const deadline = Date.now() + (timeoutSeconds + 45) * 1000;
  let receipt = null;
  let lastReadError = null;
  while (Date.now() < deadline) {
    try {
      const comments = await github(env, 'GET', '/issues/' + number + '/comments?per_page=100');
      receipt = decodeParts(comments || [], jobId);
      if (receipt) break;
      lastReadError = null;
    } catch (error) {
      lastReadError = error;
    }
    await sleep(POLL_MS);
  }

  if (!receipt) return {
    ok: false,
    status: 'uncertain',
    job_id: jobId,
    issue_number: number,
    error: lastReadError ? 'cf06_result_retrieval_uncertain' : 'cf06_queue_result_unconfirmed',
    retry_safe: false
  };

  // Close only a job that has already produced an authenticated matching
  // receipt. This cleanup is best-effort and cannot trigger a second job.
  try { await github(env, 'PATCH', '/issues/' + number, {state:'closed'}); } catch {}

  return {
    ok: receipt.ok === true,
    status: receipt.ok ? 'done' : 'failed',
    job_id: jobId,
    issue_number: number,
    output: receipt.output ?? null,
    error: receipt.error ?? null,
    started_at: receipt.started_at ?? null,
    ended_at: receipt.ended_at ?? null
  };
}

export async function queueStatus(env, device = DEFAULT_DEVICE) {
  const result = await queueExecute(env, 'agent_health', {}, 15, device);
  if (!result.ok) throw new Error(result.error || 'cf06_private_queue_agent_health_failed');
  let health;
  try { health = JSON.parse(result.output); } catch { throw new Error('cf06_private_queue_agent_health_invalid'); }
  if (!health.ok || health.device_id !== DEFAULT_DEVICE || !health.queue_configured ||
      !Array.isArray(health.queue_providers) || !health.queue_providers.includes('github')) {
    throw new Error('cf06_private_queue_agent_health_mismatch');
  }
  return {
    heartbeat: health,
    seen_at: health.checked_at,
    connected: true,
    queued: 0,
    leased: 0,
    uncertain: 0,
    backend: 'github-private-issue-queue',
    queue_providers: health.queue_providers,
    http_control: health.http_control
  };
}
