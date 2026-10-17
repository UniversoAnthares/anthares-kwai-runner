export interface Env {
  DEVICE_STATE: DurableObjectNamespace;
  DEVICE_TOKEN: string;
  CONTROL_TOKEN: string;
  ANTHARES_REMOTE_CONTROL_MODE?: string;
}

type Job = {
  id: string;
  type: string;
  args?: Record<string, string>;
  timeout_seconds?: number;
  created_at: string;
  status: 'queued' | 'leased' | 'done' | 'failed';
  result?: unknown;
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

function bearer(req: Request) {
  const h = req.headers.get('authorization') || '';
  return h.startsWith('Bearer ') ? h.slice(7) : '';
}

function deviceId(req: Request) {
  return (req.headers.get('x-anthares-device') || '').trim();
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === '/health') return json({ ok: true, service: 'anthares-remote-control', version: '0.2.0-write-quota', mode: String(env.ANTHARES_REMOTE_CONTROL_MODE || 'standby').toLowerCase() });

    if (url.pathname.startsWith('/v1/device/')) {
      if (!env.DEVICE_TOKEN || bearer(req) !== env.DEVICE_TOKEN) return json({ error: 'unauthorized' }, 401);
      const id = deviceId(req);
      if (!id) return json({ error: 'missing device id' }, 400);
      const stub = env.DEVICE_STATE.get(env.DEVICE_STATE.idFromName(id));
      const headers = new Headers(req.headers);
      headers.set('x-anthares-control-mode', String(env.ANTHARES_REMOTE_CONTROL_MODE || 'standby').toLowerCase());
      const next = new Request('https://do.local' + url.pathname, { method: req.method, headers, body: req.method === 'GET' || req.method === 'HEAD' ? undefined : req.body });
      return stub.fetch(next);
    }

    if (url.pathname.startsWith('/v1/control/')) {
      if (!env.CONTROL_TOKEN || bearer(req) !== env.CONTROL_TOKEN) return json({ error: 'unauthorized' }, 401);
      const body = req.method === 'GET' ? null : await req.clone().json().catch(() => null) as any;
      const id = body?.device_id || url.searchParams.get('device_id');
      if (!id) return json({ error: 'missing device_id' }, 400);
      const stub = env.DEVICE_STATE.get(env.DEVICE_STATE.idFromName(id));
      const headers = new Headers(req.headers);
      headers.set('x-anthares-device', id);
      headers.set('x-anthares-control-mode', String(env.ANTHARES_REMOTE_CONTROL_MODE || 'standby').toLowerCase());
      const fwd = new Request('https://do.local' + url.pathname + url.search, { method: req.method, headers, body: req.method === 'GET' ? undefined : JSON.stringify(body) });
      return stub.fetch(fwd);
    }

    return json({ error: 'not found' }, 404);
  },
};

export class DeviceState implements DurableObject {
  constructor(private state: DurableObjectState) {}

  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === '/v1/device/heartbeat' && req.method === 'POST') {
      const mode = (req.headers.get('x-anthares-control-mode') || 'standby').toLowerCase();
      if (mode !== 'active') return json({ ok: true, standby: true, persisted: false });
      const body = await req.json().catch(() => ({}));
      const now = Date.now();
      const previous = await this.state.storage.get<any>('heartbeat');
      const previousAt = previous?.seen_at ? Date.parse(previous.seen_at) : 0;
      const semanticOld = previous ? { ...previous } : null;
      if (semanticOld) delete semanticOld.seen_at;
      const semanticNew = { ...(body as object) };
      if (!previous || JSON.stringify(semanticOld) !== JSON.stringify(semanticNew) || now - previousAt >= 60000) {
        await this.state.storage.put('heartbeat', { ...semanticNew, seen_at: new Date(now).toISOString() });
        return json({ ok: true, standby: false, persisted: true });
      }
      return json({ ok: true, standby: false, persisted: false });
    }

    if (url.pathname === '/v1/device/jobs/next' && req.method === 'GET') {
      const jobs = await this.state.storage.list<Job>({ prefix: 'job:' });
      const queued = [...jobs.values()].filter(job => job && job.status === 'queued').sort((a,b) => Date.parse(a.created_at) - Date.parse(b.created_at));
      const job = queued[0];
      if (!job) return new Response(null, { status: 204 });
      job.status = 'leased';
      await this.state.storage.put('job:' + job.id, job);
      return json({ job });
    }

    const resultMatch = url.pathname.match(/^\/v1\/device\/jobs\/([^/]+)\/result$/);
    if (resultMatch && req.method === 'POST') {
      const id = resultMatch[1];
      const body = await req.json().catch(() => null);
      const job = await this.state.storage.get<Job>('job:' + id);
      if (!job) return json({ error: 'unknown job' }, 404);
      job.status = (body as any)?.ok ? 'done' : 'failed';
      job.result = body;
      await this.state.storage.put('job:' + id, job);
      return json({ ok: true });
    }

    if (url.pathname === '/v1/control/jobs' && req.method === 'POST') {
      const body = await req.json().catch(() => null) as any;
      if (!body?.type || typeof body.type !== 'string') return json({ error: 'missing type' }, 400);
      const id = crypto.randomUUID();
      const job: Job = {
        id,
        type: body.type,
        args: body.args || {},
        timeout_seconds: Math.max(1, Math.min(Number(body.timeout_seconds || 30), 120)),
        created_at: new Date().toISOString(),
        status: 'queued',
      };
      await this.state.storage.put('job:' + id, job);
      return json({ ok: true, job }, 201);
    }

    const jobMatch = url.pathname.match(/^\/v1\/control\/jobs\/([^/]+)$/);
    if (jobMatch && req.method === 'GET') {
      const job = await this.state.storage.get<Job>('job:' + jobMatch[1]);
      if (!job) return json({ error: 'not found' }, 404);
      return json({ job });
    }

    if (url.pathname === '/v1/control/status' && req.method === 'GET') {
      const heartbeat = await this.state.storage.get('heartbeat');
      const jobs = await this.state.storage.list<Job>({ prefix: 'job:' });
      const queued = [...jobs.values()].filter(job => job && job.status === 'queued').length;
      return json({ heartbeat: heartbeat || null, queued });
    }

    return json({ error: 'not found' }, 404);
  }
}
