export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      return Response.json({
        ok: true,
        service: 'anthares-ci-redundancy',
        provider: 'cloudflare-workers-builds'
      });
    }
    return new Response('Anthares CI redundancy', { status: 200 });
  }
};
