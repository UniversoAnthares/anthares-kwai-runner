export interface Env {
  DEVICE_STATE: DurableObjectNamespace;
  DEVICE_TOKEN: string;
  CONTROL_TOKEN: string;
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
    if (url.pathname === '/health') return json({ ok: true, service: 'anthares-remote-control', version: '0.1.0' });

    if (url.pathname.startsWith('/v1/device/')) {
      if (!env.DEVICE_TOKEN || bearer(req) !== env.DEVICE_TOKEN) return json({ error: 'unauthorized' }, 401);
      const id = deviceId(req);
      if (!id) return json({ error: 'missing device id' }, 400);
      const stub = env.DEVICE_STATE.get(env.DEVICE_STATE.idFromName(id));
      const next = new Request('https://do.local' + url.pathname, req);
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
      const body = await req.json().catch(() => ({}));
      await this.state.storage.put('heartbeat', { ...body as object, seen_at: new Date().toISOString() });
      return json({ ok: true });
    }

    if (url.pathname === '/v1/device/jobs/next' && req.method === 'GET') {
      const queue = (await this.state.storage.get<string[]>('queue')) || [];
      while (queue.length) {
        const id = queue.shift()!;
        const job = await this.state.storage.get<Job>('job:' + id);
        if (!job || job.status !== 'queued') continue;
        job.status = 'leased';
        await this.state.storage.put('job:' + id, job);
        await this.state.storage.put('queue', queue);
        return json({ job });
      }
      await this.state.storage.put('queue', queue);
      return new Response(null, { status: 204 });
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
      const queue = (await this.state.storage.get<string[]>('queue')) || [];
      queue.push(id);
      await this.state.storage.put('job:' + id, job);
      await this.state.storage.put('queue', queue);
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
      const queue = (await this.state.storage.get<string[]>('queue')) || [];
      return json({ heartbeat: heartbeat || null, queued: queue.length });
    }

    return json({ error: 'not found' }, 404);
  }
}
