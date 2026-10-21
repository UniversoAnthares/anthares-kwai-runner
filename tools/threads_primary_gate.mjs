// Deterministic local standby gate for the Anthares Browser cloud publisher.
// No API credentials, browser use, or content publication in this module.
// Exit 0 = local fallback may run; exit 20 = standby/hold.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const WORKFLOW = 'cortes-threads-cloud-publish.yml';
const URL = 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/actions/workflows/' + WORKFLOW + '/runs?per_page=20';
const root = process.env.CORTES_THREADS_LOCAL_ROOT || 'D:\\AntharsWork\\cortes-social-browser-20261020';
const cacheFile = path.join(root, 'threads-cloud-gate-cache.json');
const now = Date.now();

export function decide(result, nowMs = Date.now()) {
  if (result?.http === 404) return { allow: true, reason: 'CLOUD_PUBLISHER_NOT_DEPLOYED' };
  if (result?.http !== 200 || !Array.isArray(result.workflow_runs))
    return { allow: false, reason: 'CLOUD_STATUS_UNAVAILABLE' };
  const runs = result.workflow_runs.filter(r => r && r.head_branch === 'main' && r.event !== 'pull_request');
  if (runs.length === 0) return { allow: true, reason: 'CLOUD_PUBLISHER_NOT_STARTED' };
  const recent = runs.some(r => ['queued','waiting','in_progress','requested','pending'].includes(r.status)
       && nowMs - Date.parse(r.created_at) < 90 * 60_000);
  if (recent) return { allow: false, reason: 'CLOUD_PRIMARY_ACTIVE' };
  if (runs.some(r => r.conclusion === 'success' && nowMs - Date.parse(r.created_at) < 60 * 60_000))
    return { allow: false, reason: 'CLOUD_PRIMARY_HEALTHY' };
  // A failed/expired publishing run may have clicked Post. A shared lease and
  // remote reconciliation must precede any local failover after the first run.
  return { allow: false, reason: 'CLOUD_OUTCOME_REQUIRES_SHARED_LEASE_RECONCILIATION' };
}

function readCache() {
  try {
    const value = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    if (Number.isFinite(value.checked_at) && now - value.checked_at < 5 * 60_000
        && value.status && Number.isInteger(value.status.http)) return value.status;
  } catch {}
  return null;
}

async function fetchStatus() {
  const cached = readCache();
  if (cached) return cached;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 6_000);
  try {
    const r = await fetch(URL, {
      headers: {'Accept':'application/vnd.github+json','User-Agent':'AntharesCortesThreadsStandby/1.0'},
      signal: controller.signal
    });
    if (r.status !== 200 && r.status !== 404) return {http:r.status};
    const body = r.status === 200 ? await r.json() : null;
    const status = {http:r.status,workflow_runs:(body?.workflow_runs || []).map(({head_branch,event,status,conclusion,created_at}) =>
      ({head_branch,event,status,conclusion,created_at}))};
    const temporary = cacheFile + '.tmp-' + process.pid;
    fs.writeFileSync(temporary, JSON.stringify({checked_at:now,status}), 'utf8');
    fs.renameSync(temporary, cacheFile);
    return status;
  } finally {
    clearTimeout(timeout);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const status = await fetchStatus();
    const decision = decide(status, now);
    console.log('THREADS_EXECUTOR_ROLE=LOCAL_STANDBY ' + decision.reason);
    process.exitCode = decision.allow ? 0 : 20;
  } catch (err) {
    console.log('THREADS_EXECUTOR_ROLE=LOCAL_STANDBY CLOUD_STATUS_CHECK_FAILED ' + err?.name);
    process.exitCode = 20;
  }
}
