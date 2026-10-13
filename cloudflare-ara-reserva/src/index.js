const INTERNAL_ORIGIN = 'https://anthares-ara-backup.internal';

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, INTERNAL_ORIGIN);
    const upstream = await env.ARA_CONTROL.fetch(new Request(target.toString(), request));
    const headers = new Headers(upstream.headers);
    headers.set('x-anthares-ara-route', 'reserve-proxy');
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers,
    });
  },
};
