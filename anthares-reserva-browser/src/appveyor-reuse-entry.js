import puppeteer from "@cloudflare/puppeteer";
import app, { BrowserState } from "./generic-entry.js";

export { BrowserState };

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {"content-type":"application/json; charset=utf-8","cache-control":"no-store"},
});

function sameSecret(a, b) {
  a = String(a || ""); b = String(b || "");
  if (!a || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function authorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_PROBE_TOKEN);
}

function genericStub(env) {
  return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("generic-browser"));
}
async function readSessionId(env) {
  const r = await genericStub(env).fetch("https://state/session");
  return String((await r.json()).session_id || "");
}

async function probeExisting(env) {
  const sessionId = await readSessionId(env);
  if (!sessionId) return {ok:false,error:"no_existing_browser_session"};
  let browser;
  try {
    browser = await puppeteer.connect(env.BROWSER, sessionId);
    const pages = await browser.pages();
    const page = pages[0] || await browser.newPage();
    await page.goto("https://ci.appveyor.com/login", {waitUntil:"domcontentloaded", timeout:20000});
    await new Promise(r => setTimeout(r, 1200));
    const result = await page.evaluate(() => ({
      url: location.href,
      title: document.title,
      text: (document.body?.innerText || "").replace(/\s+/g, " ").slice(0, 1600),
      actions: [...document.querySelectorAll('a,button,input[type="submit"],[role="button"]')]
        .map(e => ({text:((e.innerText||e.value||e.getAttribute("aria-label")||"").replace(/\s+/g," ").trim()).slice(0,120),href:e.href||""}))
        .filter(x => x.text || x.href)
        .slice(0,60),
    }));
    return {ok:true,reused:true,...result};
  } catch (err) {
    return {ok:false,error:"existing_browser_unavailable",detail:String(err?.message||err).slice(0,300)};
  } finally {
    if (browser) await browser.disconnect().catch(() => {});
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/browser/appveyor-reuse-probe" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      const result = await probeExisting(env);
      return json(result, result.ok ? 200 : 409);
    }
    return app.fetch(request, env, ctx);
  },
};
