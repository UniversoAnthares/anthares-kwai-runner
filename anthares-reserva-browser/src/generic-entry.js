import puppeteer from "@cloudflare/puppeteer";
import app, { BrowserState } from "./entry.js";

export { BrowserState };

const ALLOWED_HOSTS = new Set([
  "app.circleci.com",
  "circleci.com",
  "github.com",
]);

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
  },
});

function sameSecret(a, b) {
  a = String(a || "");
  b = String(b || "");
  if (!a || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function authorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}

function genericStub(env) {
  return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("generic-browser"));
}

async function readSessionId(env) {
  const r = await genericStub(env).fetch("https://state/session");
  return String((await r.json()).session_id || "");
}

async function writeSessionId(env, id) {
  await genericStub(env).fetch("https://state/session", {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify({session_id: id || ""}),
  });
}

async function connectOrLaunch(env) {
  const existing = await readSessionId(env);
  if (existing) {
    try {
      return {browser: await puppeteer.connect(env.BROWSER, existing), reused: true};
    } catch {
      await writeSessionId(env, "");
    }
  }
  const browser = await puppeteer.launch(env.BROWSER, {keep_alive: 600000});
  await writeSessionId(env, browser.sessionId());
  return {browser, reused: false};
}

async function liveView(page) {
  const cdp = await page.createCDPSession();
  try {
    const result = await cdp.send("Cloudflare.getLiveView", {mode: "full", expiresInMs: 600000});
    return String(result.devtoolsFrontendUrl || "");
  } finally {
    await cdp.detach().catch(() => {});
  }
}

async function navigate(env, target) {
  let parsed;
  try { parsed = new URL(target); } catch { return {ok:false, error:"invalid_url"}; }
  if (parsed.protocol !== "https:" || !ALLOWED_HOSTS.has(parsed.hostname.toLowerCase())) {
    return {ok:false, error:"host_not_allowed"};
  }
  const opened = await connectOrLaunch(env);
  const browser = opened.browser;
  try {
    const pages = await browser.pages();
    const page = pages[0] || await browser.newPage();
    await page.goto(parsed.toString(), {waitUntil:"domcontentloaded", timeout:20000});
    const title = await page.title().catch(() => "");
    const live_view_url = await liveView(page);
    await browser.disconnect();
    return {ok:true, reused:opened.reused, url:page.url(), title, live_view_url};
  } catch (err) {
    await browser.disconnect().catch(() => {});
    return {ok:false, error:"navigation_failed", detail:String(err?.message || err).slice(0,180)};
  }
}

async function closeGeneric(env) {
  const id = await readSessionId(env);
  if (!id) return {ok:true, active:false};
  try {
    const browser = await puppeteer.connect(env.BROWSER, id);
    await browser.close();
  } catch {}
  await writeSessionId(env, "");
  return {ok:true, active:false};
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/browser/navigate" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      let body;
      try { body = await request.json(); } catch { return json({error:"invalid_json"}, 400); }
      const result = await navigate(env, String(body?.url || ""));
      return json(result, result.ok ? 200 : 400);
    }
    if (url.pathname === "/browser/close" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      return json(await closeGeneric(env));
    }
    if (url.pathname === "/health" && request.method === "GET") {
      const response = await app.fetch(request, env, ctx);
      if (!response.ok) return response;
      const body = await response.json();
      body.generic_browser = true;
      body.generic_browser_allowed_hosts = [...ALLOWED_HOSTS];
      return json(body);
    }
    return app.fetch(request, env, ctx);
  },
};
