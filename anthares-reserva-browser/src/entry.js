import puppeteer from "@cloudflare/puppeteer";
import base, { BrowserState } from "./index.js";

export { BrowserState };

const te = new TextEncoder();
const td = new TextDecoder();
const OWNER_COOKIE = "anthares_reserva_owner";
const PROFILE_URL = "https://www.kwai.com/@lucasrosalem";
const STUDIO_URL = "https://studio.kwai.com/";

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
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

async function hmac(env, value) {
  if (!env.ANTHARES_RESERVA_TOKEN) throw new Error("reserve_token_unavailable");
  const key = await crypto.subtle.importKey("raw", te.encode(env.ANTHARES_RESERVA_TOKEN), {name:"HMAC", hash:"SHA-256"}, false, ["sign"]);
  return b64url(new Uint8Array(await crypto.subtle.sign("HMAC", key, te.encode(value))));
}

function cookieValue(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return "";
}

async function ownerAuthorized(request, env) {
  const token = cookieValue(request, OWNER_COOKIE);
  const [payload, sig, extra] = String(token).split(".");
  if (!payload || !sig || extra !== undefined || !sameSecret(sig, await hmac(env, payload))) return false;
  try {
    const p = JSON.parse(td.decode(fromB64url(payload)));
    return Number(p.exp) > Math.floor(Date.now()/1000);
  } catch { return false; }
}

function apiAuthorized(request, env) {
  const supplied = (request.headers.get("authorization") || "").replace(/^Bearer /i, "");
  return sameSecret(supplied, env.ANTHARES_RESERVA_TOKEN);
}

function stateStub(env) {
  return env.BROWSER_STATE.get(env.BROWSER_STATE.idFromName("owner"));
}

async function readStateRecord(env) {
  const r = await stateStub(env).fetch("https://state/state");
  return r.json();
}

async function readSessionId(env) {
  const r = await stateStub(env).fetch("https://state/session");
  return String((await r.json()).session_id || "");
}

async function writeSessionId(env, id) {
  await stateStub(env).fetch("https://state/session", {
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({session_id:id || ""}),
  });
}

async function writeStateCiphertext(env, ciphertext) {
  const r = await stateStub(env).fetch("https://state/state", {
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify({ciphertext}),
  });
  return r.json();
}

async function stateKey(env) {
  const raw = new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode("anthares-reserva-state-v1:" + env.ANTHARES_RESERVA_TOKEN)));
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}

async function decryptState(env, value) {
  const blob = fromB64url(value);
  if (blob.length < 29) throw new Error("invalid_state_blob");
  const clear = await crypto.subtle.decrypt(
    {name:"AES-GCM", iv:blob.slice(0,12), additionalData:te.encode("anthares-reserva-browser-state-v1")},
    await stateKey(env), blob.slice(12),
  );
  return JSON.parse(td.decode(clear));
}

async function encryptState(env, state) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cipher = new Uint8Array(await crypto.subtle.encrypt(
    {name:"AES-GCM", iv, additionalData:te.encode("anthares-reserva-browser-state-v1")},
    await stateKey(env), te.encode(JSON.stringify(state)),
  ));
  const out = new Uint8Array(iv.length + cipher.length);
  out.set(iv); out.set(cipher, iv.length);
  return b64url(out);
}

async function restorePersistedState(env, page) {
  const record = await readStateRecord(env);
  if (!record.available) return {status:"empty", available:false};
  let state;
  try { state = await decryptState(env, record.ciphertext); }
  catch { return {status:"decrypt_failed", available:true}; }
  await page.goto("https://www.kwai.com/", {waitUntil:"domcontentloaded", timeout:15000});
  const cookies = Array.isArray(state.cookies) ? state.cookies.slice(0,128) : [];
  const safe = cookies.filter(c => c && c.name && typeof c.value === "string" && /(^|\.)kwai\.com$/i.test(String(c.domain || "").replace(/^\./,""))).map(c => {
    const out = {};
    for (const k of ["name","value","domain","path","expires","httpOnly","secure","sameSite"]) if (c[k] !== undefined) out[k] = c[k];
    return out;
  });
  if (safe.length) await page.setCookie(...safe);
  const items = state.localStorage && typeof state.localStorage === "object" ? state.localStorage : {};
  const bounded = {};
  for (const [k,v] of Object.entries(items).slice(0,256)) if (String(k).length <= 512 && String(v).length <= 32768) bounded[String(k)] = String(v);
  await page.evaluate(values => { try { localStorage.clear(); for (const [k,v] of Object.entries(values)) localStorage.setItem(k,v); } catch {} }, bounded);
  return {status:"restored", available:true, cookie_count:safe.length, local_storage_count:Object.keys(bounded).length};
}

async function capturePersistedState(env, page) {
  const cookies = (await page.cookies().catch(() => [])).filter(c => /(^|\.)kwai\.com$/i.test(String(c.domain || "").replace(/^\./,""))).slice(0,128);
  const localStorage = await page.evaluate(() => {
    const out = {};
    try { for (let i=0;i<Math.min(window.localStorage.length,256);i++) { const k=window.localStorage.key(i); if (k !== null) out[k]=window.localStorage.getItem(k); } } catch {}
    return out;
  }).catch(() => ({}));
  const state = {schema:"anthares-reserva-browser-state.v1", cookies, localStorage, url:page.url(), saved_at:new Date().toISOString()};
  return writeStateCiphertext(env, await encryptState(env, state));
}

async function connectOrLaunch(env) {
  const existing = await readSessionId(env);
  if (existing) {
    try { return {browser:await puppeteer.connect(env.BROWSER, existing), reused:true}; }
    catch { await writeSessionId(env, ""); }
  }
  const browser = await puppeteer.launch(env.BROWSER, {keep_alive:600000});
  await writeSessionId(env, browser.sessionId());
  return {browser, reused:false};
}

async function inspectProfile(page) {
  return page.evaluate(() => {
    const visible = e => { const r=e.getBoundingClientRect(),s=getComputedStyle(e); return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden"; };
    const text = e => ((e.innerText||e.textContent||"")+" "+(e.getAttribute?.("aria-label")||"")+" "+(e.getAttribute?.("title")||"")).replace(/\s+/g," ").trim();
    const nodes=[...document.querySelectorAll('a,button,input,[role="button"],[role="menuitem"],span,div')];
    const login=nodes.some(e=>visible(e)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(text(e))||["password","tel"].includes((e.getAttribute?.("type")||"").toLowerCase())));
    const owner=nodes.some(e=>visible(e)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(text(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.("data-testid")||"")||/\/(profile|account)\/(edit|settings)(\/|$)/i.test(e.getAttribute?.("href")||"")));
    const logout=nodes.some(e=>visible(e)&&/^(log\s*out|logout|sign\s*out|sair)$/i.test(text(e)));
    return {host:location.hostname.toLowerCase(),path:location.pathname.replace(/\/$/,"").toLowerCase(),login_gate:login,owner_edit:owner,logout_visible:logout};
  });
}

async function inspectStudio(page) {
  return page.evaluate(() => {
    const visible = e => { const r=e.getBoundingClientRect(),s=getComputedStyle(e); return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden"; };
    const text = e => ((e.innerText||e.textContent||"")+" "+(e.getAttribute?.("aria-label")||"")+" "+(e.getAttribute?.("title")||"")).replace(/\s+/g," ").trim();
    const nodes=[...document.querySelectorAll('a,button,label,input,[role="button"],[role="menuitem"]')];
    const login=nodes.some(e=>visible(e)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(text(e))||["password","tel"].includes((e.getAttribute?.("type")||"").toLowerCase())));
    const file=[...document.querySelectorAll('input[type="file"]')].some(e=>!e.disabled);
    const upload=nodes.some(e=>visible(e)&&/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(text(e)));
    return {host:location.hostname.toLowerCase(),login_gate:login,file_input:file,upload_control:upload};
  });
}

async function verifyPersistedSession(env) {
  let browser = null;
  let page = null;
  let restore = {status:"reused", available:true};
  try {
    const opened = await connectOrLaunch(env);
    browser = opened.browser;
    const pages = await browser.pages();
    page = pages.find(p => p.url().includes("kwai.com")) || pages[0] || await browser.newPage();
    if (!opened.reused) restore = await restorePersistedState(env, page);
    if (!restore.available) return {ok:true, persisted_state:false, identity_verified:false, upload_surface_verified:false, session_state:"no_persisted_state", restore_status:restore.status};
    await page.goto(PROFILE_URL, {waitUntil:"domcontentloaded", timeout:18000});
    await new Promise(r=>setTimeout(r,2200));
    const profile = await inspectProfile(page);
    const identity = profile.host === "www.kwai.com" && profile.path === "/@lucasrosalem" && !profile.login_gate && (profile.owner_edit || profile.logout_visible);
    const evidence = {profile_host_ok:profile.host === "www.kwai.com", profile_path_ok:profile.path === "/@lucasrosalem", login_gate:!!profile.login_gate, owner_edit:!!profile.owner_edit, logout_visible:!!profile.logout_visible};
    if (!identity) return {ok:true, persisted_state:true, identity_verified:false, upload_surface_verified:false, session_state:profile.login_gate?"unauthenticated":"unknown", restore_status:restore.status, evidence};
    await page.goto(STUDIO_URL, {waitUntil:"domcontentloaded", timeout:18000});
    await new Promise(r=>setTimeout(r,2500));
    const studio = await inspectStudio(page);
    const upload = studio.host === "studio.kwai.com" && !studio.login_gate && (studio.file_input || studio.upload_control);
    const stored = await capturePersistedState(env, page);
    return {ok:true, persisted_state:true, identity_verified:true, upload_surface_verified:upload, session_state:upload?"authenticated_surface":"authenticated_profile_only", restore_status:restore.status, state_refreshed:!!stored.stored, evidence, studio:{host_ok:studio.host === "studio.kwai.com", login_gate:!!studio.login_gate, file_input:!!studio.file_input, upload_control:!!studio.upload_control}};
  } catch (err) {
    return {ok:false, identity_verified:false, upload_surface_verified:false, error:"session_verify_failed", detail:String(err?.message || err).slice(0,160)};
  } finally {
    if (browser) await browser.close().catch(() => {});
    await writeSessionId(env, "").catch(() => {});
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/session/verify" && request.method === "POST") {
      if (!apiAuthorized(request, env)) return json({error:"unauthorized"}, 401);
      const result = await verifyPersistedSession(env);
      return json(result, result.ok ? 200 : 503);
    }
    if (url.pathname === "/owner/verify" && request.method === "GET") {
      if (!(await ownerAuthorized(request, env))) return new Response(null, {status:303, headers:{location:"/owner", "cache-control":"no-store"}});
      const result = await verifyPersistedSession(env);
      return json(result, result.ok ? 200 : 503);
    }
    if (url.pathname === "/health" && request.method === "GET") {
      const response = await base.fetch(request, env, ctx);
      if (!response.ok) return response;
      const body = await response.json();
      body.authenticated_probe = true;
      body.authenticated_probe_path = "/session/verify";
      return json(body, 200);
    }
    return base.fetch(request, env, ctx);
  },
};
