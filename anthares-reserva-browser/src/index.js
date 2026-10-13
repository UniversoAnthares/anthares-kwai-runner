import { DurableObject } from "cloudflare:workers";
import puppeteer from "@cloudflare/puppeteer";

const VERSION = "2026-10-13-reserva-browser-v4";
const OWNER_APPROVAL_HASH = "6Z-3WlmAvh6o7m_W0eYEpEo23YKZtjn-DLJpyjtEfQ0";
const OWNER_COOKIE = "anthares_reserva_owner";
const START_URL = "https://www.kwai.com/";
const te = new TextEncoder();
const td = new TextDecoder();

const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    ...headers,
  },
});
const html = (body, status = 200, headers = {}) => new Response(body, {
  status,
  headers: {
    "content-type": "text/html; charset=utf-8",
    "cache-control": "no-store",
    "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    ...headers,
  },
});
const sameSecret = (a, b) => {
  a = String(a || ""); b = String(b || "");
  if (!a || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
};
const b64url = bytes => {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
};
const fromB64url = value => {
  let s = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const raw = atob(s);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
};
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

async function sha256b64(value) {
  return b64url(new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode(String(value)))));
}
async function hmac(env, value) {
  if (!env.ANTHARES_RESERVA_TOKEN) throw new Error("reserve token unavailable");
  const key = await crypto.subtle.importKey("raw", te.encode(env.ANTHARES_RESERVA_TOKEN), {name:"HMAC", hash:"SHA-256"}, false, ["sign"]);
  return b64url(new Uint8Array(await crypto.subtle.sign("HMAC", key, te.encode(value))));
}
async function stateKey(env) {
  if (!env.ANTHARES_RESERVA_TOKEN) throw new Error("reserve token unavailable");
  const raw = new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode("anthares-reserva-state-v1:" + env.ANTHARES_RESERVA_TOKEN)));
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}
async function encryptState(env, state) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cipher = new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM", iv, additionalData:te.encode("anthares-reserva-browser-state-v1")}, await stateKey(env), te.encode(JSON.stringify(state))));
  const out = new Uint8Array(iv.length + cipher.length); out.set(iv); out.set(cipher, iv.length);
  return b64url(out);
}
async function decryptState(env, value) {
  const blob = fromB64url(value);
  if (blob.length < 29) throw new Error("invalid state blob");
  const clear = await crypto.subtle.decrypt({name:"AES-GCM", iv:blob.slice(0,12), additionalData:te.encode("anthares-reserva-browser-state-v1")}, await stateKey(env), blob.slice(12));
  return JSON.parse(td.decode(clear));
}

export class BrowserState extends DurableObject {
  constructor(ctx, env) { super(ctx, env); this.ctx = ctx; }
  async fetch(request) {
    const u = new URL(request.url);
    if (u.pathname === "/state" && request.method === "GET") {
      const record = await this.ctx.storage.get("state");
      return json(record ? {ok:true, available:true, ...record} : {ok:true, available:false});
    }
    if (u.pathname === "/state" && request.method === "POST") {
      const body = await request.json();
      const record = {ciphertext:String(body.ciphertext || ""), saved_at:new Date().toISOString(), schema:"anthares-reserva-browser-state.v1"};
      if (!record.ciphertext) return json({error:"missing_ciphertext"}, 400);
      await this.ctx.storage.put("state", record);
      return json({ok:true, stored:true, saved_at:record.saved_at});
    }
    if (u.pathname === "/session" && request.method === "GET") {
      return json({ok:true, session_id:String((await this.ctx.storage.get("session_id")) || "")});
    }
    if (u.pathname === "/session" && request.method === "POST") {
      const body = await request.json();
      const id = String(body.session_id || "");
      if (id) await this.ctx.storage.put("session_id", id); else await this.ctx.storage.delete("session_id");
      return json({ok:true, active:!!id});
    }
    return json({error:"not_found"}, 404);
  }
}

function stateStub(env) { return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("owner")); }
async function stateRecord(env) { const r = await stateStub(env).fetch("https://state/state"); return r.json(); }
async function setState(env, ciphertext) { const r = await stateStub(env).fetch("https://state/state", {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({ciphertext})}); return r.json(); }
async function sessionId(env) { const r = await stateStub(env).fetch("https://state/session"); return String((await r.json()).session_id || ""); }
async function setSessionId(env, id) { await stateStub(env).fetch("https://state/session", {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({session_id:id || ""})}); }

function authorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}
function cookieValue(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return "";
}
async function issueOwnerSession(env) {
  const payload = b64url(te.encode(JSON.stringify({exp:Math.floor(Date.now()/1000)+3600, nonce:crypto.randomUUID()})));
  return `${payload}.${await hmac(env, payload)}`;
}
async function ownerAuthorized(request, env) {
  const token = cookieValue(request, OWNER_COOKIE);
  const [payload, sig, extra] = String(token).split(".");
  if (!payload || !sig || extra !== undefined || !sameSecret(sig, await hmac(env, payload))) return false;
  try { const p = JSON.parse(td.decode(fromB64url(payload))); return Number(p.exp) > Math.floor(Date.now()/1000); } catch { return false; }
}
const ownerCookie = token => `${OWNER_COOKIE}=${token}; Path=/; Max-Age=3600; HttpOnly; Secure; SameSite=Strict`;
const clearOwnerCookie = `${OWNER_COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict`;

async function restoreState(env, page) {
  const record = await stateRecord(env);
  if (!record.available) { await page.goto(START_URL, {waitUntil:"domcontentloaded", timeout:15000}); return "empty"; }
  let state;
  try { state = await decryptState(env, record.ciphertext); } catch { await page.goto(START_URL, {waitUntil:"domcontentloaded", timeout:15000}); return "decrypt_failed"; }
  await page.goto(START_URL, {waitUntil:"domcontentloaded", timeout:15000});
  const cookies = Array.isArray(state.cookies) ? state.cookies : [];
  if (cookies.length) {
    const safe = cookies.map(c => {
      const out = {};
      for (const k of ["name","value","domain","path","expires","httpOnly","secure","sameSite"]) if (c[k] !== undefined) out[k] = c[k];
      return out;
    });
    await page.setCookie(...safe).catch(() => {});
  }
  const items = state.localStorage && typeof state.localStorage === "object" ? state.localStorage : {};
  await page.evaluate(values => { try { localStorage.clear(); for (const [k,v] of Object.entries(values)) localStorage.setItem(k, String(v)); } catch {} }, items).catch(() => {});
  await page.reload({waitUntil:"domcontentloaded", timeout:15000}).catch(() => {});
  return "restored";
}
async function captureState(env, page) {
  const cookies = await page.cookies().catch(() => []);
  const localStorage = await page.evaluate(() => { const out={}; try { for(let i=0;i<window.localStorage.length;i++){const k=window.localStorage.key(i); if(k!==null) out[k]=window.localStorage.getItem(k);} } catch {} return out; }).catch(() => ({}));
  const state = {schema:"anthares-reserva-browser-state.v1", cookies, localStorage, url:page.url(), saved_at:new Date().toISOString()};
  return setState(env, await encryptState(env, state));
}
async function connectActive(env) {
  const id = await sessionId(env);
  if (!id) return null;
  try { return await puppeteer.connect(env.BROWSER, id); }
  catch { await setSessionId(env, ""); return null; }
}
async function activePage(browser) {
  const pages = await browser.pages();
  return pages.find(p => p.url().includes("kwai.com")) || pages[0] || browser.newPage();
}
async function liveView(page) {
  const cdp = await page.createCDPSession();
  const result = await cdp.send("Cloudflare.getLiveView", {mode:"full", expiresInMs:600000});
  await cdp.detach().catch(() => {});
  return String(result.devtoolsFrontendUrl || "");
}
async function startOwnerBrowser(env) {
  let browser = await connectActive(env);
  let restore_status = "reused";
  if (!browser) {
    browser = await puppeteer.launch(env.BROWSER, {keep_alive:600000});
    await setSessionId(env, browser.sessionId());
    const page = await activePage(browser);
    restore_status = await restoreState(env, page);
  }
  const page = await activePage(browser);
  if (!page.url().includes("kwai.com")) await page.goto(START_URL, {waitUntil:"domcontentloaded", timeout:15000});
  const url = await liveView(page);
  await browser.disconnect();
  return {ok:true, live_view_url:url, restore_status};
}
async function mintLiveView(env) {
  const browser = await connectActive(env);
  if (!browser) return {ok:false, error:"no_active_session"};
  const page = await activePage(browser); const url = await liveView(page); await browser.disconnect();
  return {ok:true, live_view_url:url};
}
async function saveAndClose(env) {
  const browser = await connectActive(env);
  if (!browser) return {ok:false, error:"no_active_session"};
  try { const page = await activePage(browser); const stored = await captureState(env, page); return {ok:!!stored.stored, saved_at:stored.saved_at}; }
  finally { await browser.close().catch(() => {}); await setSessionId(env, ""); }
}
async function ownerStatus(env) {
  const record = await stateRecord(env); const id = await sessionId(env);
  return {active:!!id, persisted:!!record.available, saved_at:record.saved_at || null};
}

function ownerLoginPage(message="") {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Reserva</title></head><body style="font-family:system-ui;max-width:720px;margin:40px auto;padding:0 20px"><h1>Anthares Reserva Browser</h1><p>Canal Cloudflare isolado para recuperação e autenticação manual.</p>${message?`<p><strong>${esc(message)}</strong></p>`:""}<form method="post" action="/owner/login"><label>Código do proprietário <input type="password" name="code" autocomplete="one-time-code" required></label> <button type="submit">Entrar</button></form></body></html>`;
}
async function ownerDashboard(env, notice="", live="") {
  const st = await ownerStatus(env);
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Reserva</title></head><body style="font-family:system-ui;max-width:820px;margin:40px auto;padding:0 20px"><h1>Anthares Reserva Browser</h1>${notice?`<p><strong>${esc(notice)}</strong></p>`:""}<p>Sessão Browser Run: <b>${st.active?"ativa":"inativa"}</b>. Estado criptografado persistido: <b>${st.persisted?"sim":"não"}</b>${st.saved_at?` (${esc(st.saved_at)})`:""}.</p>${live?`<p><a href="${esc(live)}" rel="noopener noreferrer" target="_blank">Abrir navegador remoto</a></p>`:""}<form method="post" action="/owner/start"><button type="submit">Iniciar/recuperar sessão</button></form><form method="post" action="/owner/live"><button type="submit">Gerar novo link Live View</button></form><form method="post" action="/owner/save"><button type="submit">Salvar autenticação e encerrar</button></form><form method="post" action="/owner/logout"><button type="submit">Sair</button></form><p>O Live View roda integralmente na Cloudflare. Ao concluir o login, volte aqui e use “Salvar autenticação e encerrar” para liberar a cota gratuita.</p></body></html>`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      return json({ok:true, service:"anthares-reserva-browser", version:VERSION, provider:"cloudflare", mode:"on-demand", browser_binding:!!env.BROWSER, durable_state_binding:!!env.BROWSER_STATE, live_view:true, persistent_profile_support:true, authenticated_session:"not_verified", render_required:false, purpose:"emergency browser continuity"});
    }
    if (url.pathname === "/status" && request.method === "GET") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      const st = await ownerStatus(env);
      return json({ok:!!env.BROWSER, service:"anthares-reserva-browser", version:VERSION, provider:"cloudflare", browser_binding:!!env.BROWSER, durable_state_binding:!!env.BROWSER_STATE, continuous_runtime:false, persistent_profile:st.persisted, active_session:st.active, production_login:"not_verified", live_view:true, render_required:false});
    }
    if (url.pathname === "/session/start" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      try { return json(await startOwnerBrowser(env)); } catch (err) { return json({ok:false,error:"session_start_failed",detail:String(err?.message||err).slice(0,180)},503); }
    }
    if (url.pathname === "/session/live" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      return json(await mintLiveView(env));
    }
    if (url.pathname === "/session/save" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      return json(await saveAndClose(env));
    }
    if (url.pathname === "/owner" && request.method === "GET") {
      if (!(await ownerAuthorized(request, env))) return html(ownerLoginPage());
      return html(await ownerDashboard(env));
    }
    if (url.pathname === "/owner/login" && request.method === "POST") {
      const form = await request.formData(); const code = String(form.get("code") || "");
      if (!sameSecret(await sha256b64(code), OWNER_APPROVAL_HASH)) return html(ownerLoginPage("Código inválido."), 403);
      const token = await issueOwnerSession(env);
      return new Response(null, {status:303, headers:{location:"/owner", "set-cookie":ownerCookie(token), "cache-control":"no-store"}});
    }
    if (url.pathname === "/owner/logout" && request.method === "POST") return new Response(null,{status:303,headers:{location:"/owner","set-cookie":clearOwnerCookie}});
    if (["/owner/start","/owner/live","/owner/save"].includes(url.pathname) && request.method === "POST") {
      if (!(await ownerAuthorized(request, env))) return new Response(null,{status:303,headers:{location:"/owner"}});
      try {
        if (url.pathname === "/owner/start") { const x=await startOwnerBrowser(env); return html(await ownerDashboard(env, `Sessão pronta (${x.restore_status}).`, x.live_view_url)); }
        if (url.pathname === "/owner/live") { const x=await mintLiveView(env); return html(await ownerDashboard(env, x.ok?"Novo link gerado.":"Nenhuma sessão ativa.", x.live_view_url || "")); }
        const x=await saveAndClose(env); return html(await ownerDashboard(env, x.ok?"Estado criptografado salvo e navegador encerrado.":"Nenhuma sessão ativa."));
      } catch (err) { return html(await ownerDashboard(env, `Falha: ${String(err?.message||err).slice(0,160)}`), 503); }
    }
    if (url.pathname === "/probe" && request.method === "POST") {
      if (!authorized(request, env)) return json({error:"unauthorized"}, 401);
      let body; try { body = await request.json(); } catch { return json({error:"invalid_json"},400); }
      const handle = String(body?.handle || "").replace(/^@/, "");
      if (!/^[a-zA-Z0-9._-]{1,40}$/.test(handle)) return json({error:"invalid_handle"},400);
      let browser;
      try {
        browser = await puppeteer.launch(env.BROWSER);
        const page = await browser.newPage();
        await page.goto("https://www.kwai.com/@" + encodeURIComponent(handle), {waitUntil:"domcontentloaded", timeout:12000});
        const result = await page.evaluate(() => ({host:location.hostname,path:location.pathname,owner_edit:!!document.querySelector('[data-testid*="edit-profile" i],[href*="/profile/edit" i]'),login_gate:!!document.querySelector('input[type="password"]')}));
        return json({ok:true,mode:"isolated_ephemeral",profile:result,identity_verified:false,upload_verified:false});
      } catch (err) { return json({ok:false,error:"browser_probe_failed",detail:String(err?.message||err).slice(0,120)},503); }
      finally { if (browser) await browser.close().catch(() => {}); }
    }
    return json({error:"not_found"},404);
  },
};
