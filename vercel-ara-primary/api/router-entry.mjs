import { Pool } from 'pg';

if (!process.env.ARA_PUBLIC_ORIGIN) {
  process.env.ARA_PUBLIC_ORIGIN = 'https://anthares-remote-primary.vercel.app';
}

const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 1, ssl: { rejectUnauthorized: false } });
let compatibilityReady = false;

async function ensureCompatibility() {
  if (compatibilityReady) return;
  await pool.query(`
    ALTER TABLE IF EXISTS ara_reserve_jobs
      DROP CONSTRAINT IF EXISTS ara_reserve_jobs_status_check;
    ALTER TABLE IF EXISTS ara_reserve_jobs
      ADD CONSTRAINT ara_reserve_jobs_status_check
      CHECK (status IN ('queued','leased','done','failed','uncertain','expired'));
  `);
  compatibilityReady = true;
}

const mod = await import('./router.mjs');
const app = mod.default;

export default async function handler(req, res) {
  await ensureCompatibility();
  const route = String(req.query?.route || '').replace(/^\/+|\/+$/g, '');

  // The TikTok queue retains separate OIDC roles, Neon storage and leases.
  // The existing entrypoint makes the handler reachable even when Vercel
  // omits its new standalone function during an incremental Git build.
  if (route === 'cortes-tiktok') {
    const { default: tiktokHandler } = await import('./cortes-tiktok.mjs');
    return tiktokHandler(req, res);
  }

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
