import puppeteer from "@cloudflare/puppeteer";

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
const sameSecret = (a, b) => {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
};
const AUTHORIZED_HOSTS = new Set(["www.kwai.com", "studio.kwai.com"]);

async function runProbe(env, handle) {
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
    await page.goto("https://www.kwai.com/@" + encodeURIComponent(handle), { waitUntil: "domcontentloaded", timeout: 12000 });
    const result = await page.evaluate(() => ({
      host: location.hostname,
      path: location.pathname,
      owner_edit: !!document.querySelector('[data-testid*="edit-profile" i],[href*="/profile/edit" i]'),
      login_gate: !!document.querySelector('input[type="password"]')
    }));
    return { ok: true, mode: "isolated_ephemeral", profile: result,
      identity_verified: false, upload_verified: false,
      reason: "ephemeral_browser_has_no_production_login" };
  } catch (err) {
    return { ok: false, error: "browser_probe_failed", detail: String(err?.message || err).slice(0, 120) };
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET")
      return json({ ok: true, service: "anthares-reserva-browser", mode: "on-demand", authenticated_session: "not_verified" });

    // Safe public liveness proof. Fixed owned profile, no credentials, cookies,
    // DOM text or session data are returned, and no state-changing action occurs.
    if (url.pathname === "/_selftest" && request.method === "GET") {
      const result = await runProbe(env, "lucasrosalem");
      return json({ ok: result.ok, browser_started: result.ok, host_ok: result.profile?.host === "www.kwai.com", mode: result.mode || "isolated_ephemeral" }, result.ok ? 200 : 503);
    }

    if (url.pathname !== "/probe" || request.method !== "POST") return json({ error: "not_found" }, 404);
    const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
    if (!sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN)) return json({ error: "unauthorized" }, 401);
    let body;
    try { body = await request.json(); } catch { return json({ error: "invalid_json" }, 400); }
    const handle = String(body?.handle || "").replace(/^@/, "");
    if (!/^[a-zA-Z0-9._-]{1,40}$/.test(handle)) return json({ error: "invalid_handle" }, 400);
    const result = await runProbe(env, handle);
    return json(result, result.ok ? 200 : 503);
  }
};
