import core, { AraState } from './index.js';

export { AraState };

const HEARTBEAT_COALESCE_SECONDS = 60;
const EMPTY_POLL_COALESCE_SECONDS = 15;

async function tokenKey(request, kind) {
  const auth = request.headers.get('Authorization') || '';
  const device = (request.headers.get('X-Anthares-Device') || '').trim();
  if (!auth.startsWith('Bearer ') || !device) return null;
  const raw = new TextEncoder().encode(`${kind}\n${device}\n${auth}`);
  const digest = await crypto.subtle.digest('SHA-256', raw);
  const hex = [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
  return new Request(`https://ara-quota-guard.invalid/${kind}/${hex}`, { method: 'GET' });
}

async function cacheHit(key) {
  if (!key) return false;
  try { return !!(await caches.default.match(key)); } catch { return false; }
}

async function remember(key, seconds) {
  if (!key) return;
  try {
    await caches.default.put(key, new Response('1', {
      status: 200,
      headers: { 'Cache-Control': `public, max-age=${seconds}` },
    }));
  } catch {}
}

function coalescedHeartbeat() {
  return Response.json({ ok: true, coalesced: true, quota_guard: true }, {
    status: 200,
    headers: {
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
      'x-ara-quota-guard': 'heartbeat-coalesced',
    },
  });
}

function coalescedEmptyPoll() {
  return new Response(null, {
    status: 204,
    headers: {
      'cache-control': 'no-store',
      'retry-after': String(EMPTY_POLL_COALESCE_SECONDS),
      'x-ara-quota-guard': 'empty-poll-coalesced',
    },
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/v1/device/heartbeat' && request.method === 'POST') {
      const key = await tokenKey(request, 'heartbeat');
      if (await cacheHit(key)) return coalescedHeartbeat();
      const response = await core.fetch(request, env, ctx);
      if (response.ok) ctx.waitUntil(remember(key, HEARTBEAT_COALESCE_SECONDS));
      return response;
    }

    if (url.pathname === '/v1/device/jobs/next' && request.method === 'GET') {
      const key = await tokenKey(request, 'empty-poll');
      if (await cacheHit(key)) return coalescedEmptyPoll();
      const response = await core.fetch(request, env, ctx);
      if (response.status === 204) {
        ctx.waitUntil(remember(key, EMPTY_POLL_COALESCE_SECONDS));
        const headers = new Headers(response.headers);
        headers.set('retry-after', String(EMPTY_POLL_COALESCE_SECONDS));
        headers.set('x-ara-quota-guard', 'empty-poll-origin');
        return new Response(null, { status: 204, headers });
      }
      return response;
    }

    return core.fetch(request, env, ctx);
  },
};
