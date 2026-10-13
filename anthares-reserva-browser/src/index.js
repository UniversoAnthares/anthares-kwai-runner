import puppeteer from "@cloudflare/puppeteer";

const VERSION = "2026-10-13-reserva-browser-v3";
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
  },
});
const sameSecret = (a, b) => {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
};
const AUTHORIZED_HOSTS = new Set(["www.kwai.com", "studio.kwai.com"]);

function authorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      return json({
        ok: true,
        service: "anthares-reserva-browser",
        version: VERSION,
        provider: "cloudflare",
        mode: "on-demand",
        browser_binding: !!env.BROWSER,
        authenticated_session: "not_verified",
        persistent_profile: false,
        render_required: false,
        purpose: "emergency browser continuity",
      });
    }
    if (url.pathname === "/status" && request.method === "GET") {
      if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);
      return json({
        ok: !!env.BROWSER,
        service: "anthares-reserva-browser",
        version: VERSION,
        provider: "cloudflare",
        browser_binding: !!env.BROWSER,
        continuous_runtime: false,
        persistent_profile: false,
        production_login: "not_verified",
        render_required: false,
      });
    }
    if (url.pathname !== "/probe" || request.method !== "POST") return json({ error: "not_found" }, 404);
    if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);

    let body;
    try { body = await request.json(); } catch { return json({ error: "invalid_json" }, 400); }
    const handle = String(body?.handle || "").replace(/^@/, "");
    if (!/^[a-zA-Z0-9._-]{1,40}$/.test(handle)) return json({ error: "invalid_handle" }, 400);

    let browser;
    try {
      browser = await puppeteer.launch(env.BROWSER);
      const page = await browser.newPage();
      await page.setRequestInterception(true);
      page.on("request", req => {
        let dest;
        try { dest = new URL(req.url()); } catch { return req.abort(); }
        if (dest.protocol !== "https:" || !AUTHORIZED_HOSTS.has(dest.hostname)) return req.abort();
        if (["image", "media", "font"].includes(req.resourceType())) return req.abort();
        return req.continue();
      });
      await page.goto("https://www.kwai.com/@" + encodeURIComponent(handle), {
        waitUntil: "domcontentloaded",
        timeout: 12000,
      });
      const result = await page.evaluate(() => ({
        host: location.hostname,
        path: location.pathname,
        owner_edit: !!document.querySelector('[data-testid*="edit-profile" i],[href*="/profile/edit" i]'),
        login_gate: !!document.querySelector('input[type="password"]'),
      }));
      return json({
        ok: true,
        mode: "isolated_ephemeral",
        profile: result,
        identity_verified: false,
        upload_verified: false,
        reason: "fallback browser has no production login yet",
      });
    } catch (err) {
      return json({
        ok: false,
        error: "browser_probe_failed",
        detail: String(err?.message || err).slice(0, 120),
      }, 503);
    } finally {
      if (browser) await browser.close().catch(() => {});
    }
  },
};
