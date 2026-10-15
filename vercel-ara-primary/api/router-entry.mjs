if (!process.env.ARA_PUBLIC_ORIGIN) {
  process.env.ARA_PUBLIC_ORIGIN = 'https://anthares-remote-primary-v2.vercel.app';
}

const mod = await import('./router.mjs');
const app = mod.default;

export default async function handler(req, res) {
  const route = String(req.query?.route || '').replace(/^\/+|\/+$/g, '');

  // Legacy gateway-control routes depended on a Cloudflare-hosted ephemeral
  // signing key. Direct ChatGPT MCP and device queue routes do not need them.
  // Retire these paths explicitly so no live request can fall back to Cloudflare.
  if (route === 'v1/mcp/status' || route === 'v1/mcp/execute' || route === 'v1/mcp/oauth/consume') {
    res.statusCode = 410;
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Cache-Control', 'no-store');
    res.end(JSON.stringify({
      error: 'legacy_control_route_retired',
      replacement: '/mcp',
      backend: 'vercel-neon',
      cloudflare_dependency: false
    }));
    return;
  }

  return app(req, res);
}
