import { EXTERNAL_DEVICE, externalReadOnly } from "./external-readonly.mjs";
import {requestControl} from "./control-transport.mjs";
var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
import { DurableObject } from "cloudflare:workers";
import { isClaudeClient, isClaudeCallbackPair, permittedClaudeScopes } from "./claude-client-policy.mjs";
import { isKiloClient, isKiloCallbackPair, isKiloResource } from "./kilo-client-policy.mjs";
import { githubTools, callGithubTool, recordApprovedRegression } from "./github-bridge.mjs";
import { approvedTestTool, runApprovedTests } from "./approved-tests.mjs";
import { ownerGithubConfigured, startOwnerGithub, finishOwnerGithub } from "./owner-github-auth.mjs";
import { CLIENT_INSTRUCTIONS, DISCOVERY_REVISION, clientDiscovery } from "./client-discovery.mjs";
var ORIGIN = "https://anthares-ara-mcp.anthares1.workers.dev";
var CONTROL = "https://anthares-ara-vercel-reserve.vercel.app";
var CONTROL_STANDBY = "https://anthares-ara-vercel-reserve-lucasyahn-6808.vercel.app";
var DEFAULT_DEVICE = "DESKTOP-FTDK0HP";
var FALLBACK_DEVICE = "DESKTOP-FTDK0HP-SYSTEM";
var SCOPES = /* @__PURE__ */ new Set(["ara.read", "ara.write", "github.read", "github.write"]);
var WRITE_TOOLS = /* @__PURE__ */ new Set(["remote_exec", "clipboard_set", "file_write", "file_write_chunk", "file_mkdir", "file_remove", "file_rename", "file_copy", "file_write_atomic", "remote_job_start", "remote_job_cancel", "process_start", "process_kill", "service_start", "service_stop"]);
var AUTH_EMAIL = "lucasyahn@gmail.com";
var te = new TextEncoder();
var td = new TextDecoder();
function b64urlBytes(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
__name(b64urlBytes, "b64urlBytes");
function fromB64url(v) {
  let s = String(v).replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const raw = atob(s);
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}
__name(fromB64url, "fromB64url");
function rand(n = 32) {
  const b = new Uint8Array(n);
  crypto.getRandomValues(b);
  return b64urlBytes(b);
}
__name(rand, "rand");
function json(data, status2 = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status: status2, headers: { "content-type": "application/json", "cache-control": "no-store", "x-content-type-options": "nosniff", ...headers } });
}
__name(json, "json");
function html(body, status2 = 200) {
  return new Response(body, { status: status2, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self' https://github.com https://claude.ai https://chatgpt.com; base-uri 'none'; frame-ancestors 'none'", "referrer-policy": "same-origin", "x-content-type-options": "nosniff" } });
}
__name(html, "html");
function esc(v) {
  return String(v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot", "'": "&#39;" })[c]);
}
__name(esc, "esc");
function eq(a, b) {
  a = String(a);
  b = String(b);
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
__name(eq, "eq");
async function sha256b64(v) {
  return b64urlBytes(new Uint8Array(await crypto.subtle.digest("SHA-256", te.encode(String(v)))));
}
__name(sha256b64, "sha256b64");
var _statelessStates = /* @__PURE__ */ new WeakMap();
function st(env) {
  let x = _statelessStates.get(env);
  if (!x) {
    x = new StatelessGatewayState(env);
    _statelessStates.set(env, x);
  }
  return x;
}
__name(st, "st");
var StatelessGatewayState = class {
  static {
    __name(this, "StatelessGatewayState");
  }
  constructor(env) {
    this.env = env;
  }
  async ensure() {
    const a = String(this.env.ARA_OAUTH_SECRET || "");
    const pr = String(this.env.ARA_SIGNING_PRIVATE_JWK || "");
    const pu = String(this.env.ARA_SIGNING_PUBLIC_JWK || "");
    if (!a || !pr || !pu) throw new Error("stateless_gateway_secrets_missing");
    let priv, pub;
    try {
      priv = JSON.parse(pr);
      pub = JSON.parse(pu);
    } catch {
      throw new Error("stateless_gateway_key_invalid");
    }
    return { priv, pub, secret: a };
  }
  async publicPem() {
    const { pub } = await this.ensure();
    const k = await crypto.subtle.importKey("jwk", pub, { name: "Ed25519" }, true, ["verify"]);
    const spki = new Uint8Array(await crypto.subtle.exportKey("spki", k));
    const b64 = btoa(String.fromCharCode(...spki));
    const lines = b64.match(/.{1,64}/g) || [];
    return `-----BEGIN PUBLIC KEY-----
${lines.join("\n")}
-----END PUBLIC KEY-----
`;
  }
  async signControl(method, path, raw = "") {
    const { priv } = await this.ensure();
    const k = await crypto.subtle.importKey("jwk", priv, { name: "Ed25519" }, false, ["sign"]);
    const ts = String(Date.now());
    const payload = `${ts}
${String(method).toUpperCase()}
${path}
${raw}`;
    const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, k, te.encode(payload)));
    return { timestamp: ts, signature: b64urlBytes(sig) };
  }
  async hmac(input) {
    const { secret } = await this.ensure();
    const k = await crypto.subtle.importKey("raw", fromB64url(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    return b64urlBytes(new Uint8Array(await crypto.subtle.sign("HMAC", k, te.encode(input))));
  }
  async signToken(payload) {
    const body = b64urlBytes(te.encode(JSON.stringify(payload)));
    return `${body}.${await this.hmac(body)}`;
  }
  async verifyToken(token, type) {
    const parts = String(token || "").split(".");
    if (parts.length !== 2) return null;
    const [body, sig] = parts;
    if (!eq(sig, await this.hmac(body))) return null;
    try {
      const p = JSON.parse(td.decode(fromB64url(body)));
      if (p.typ !== type || p.iss !== ORIGIN || p.aud !== ORIGIN || !p.exp || p.exp <= Math.floor(Date.now() / 1e3) || !Array.isArray(p.scp)) return null;
      return p;
    } catch {
      return null;
    }
  }
  async consume(kind, jti, exp) {
    return consumeViaControl(this.env, kind, jti, exp);
  }
  async createEmailChallenge(txId) {
    const h = await this.hmac("email-otp:" + String(txId));
    let n = 0;
    for (let i = 0; i < Math.min(20, h.length); i++) n = (n * 67 + h.charCodeAt(i)) % 1e8;
    return String(n).padStart(8, "0");
  }
  async verifyEmailChallenge(txId, code) {
    const v = String(code || "");
    if (await verifyBootstrapOtp(this.env, v)) return true;
    return eq(await this.createEmailChallenge(txId), v);
  }
  async pinnedClient() {
    return String(this.env.ARA_PINNED_CLIENT || "");
  }
  async pinClient(clientId) {
    const p = await this.pinnedClient();
    return !p || p === String(clientId);
  }
};
var GatewayState = class extends DurableObject {
  static {
    __name(this, "GatewayState");
  }
  constructor(ctx, env) {
    super(ctx, env);
    this.ctx = ctx;
  }
  async ensure() {
    let priv = await this.ctx.storage.get("priv");
    let pub = await this.ctx.storage.get("pub");
    let secret = await this.ctx.storage.get("oauthSecret");
    if (!priv || !pub) {
      const p = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
      priv = await crypto.subtle.exportKey("jwk", p.privateKey);
      pub = await crypto.subtle.exportKey("jwk", p.publicKey);
      await this.ctx.storage.put({ priv, pub });
    }
    if (!secret) {
      secret = rand(48);
      await this.ctx.storage.put("oauthSecret", secret);
    }
    return { priv, pub, secret };
  }
  async publicPem() {
    const { pub } = await this.ensure();
    const k = await crypto.subtle.importKey("jwk", pub, { name: "Ed25519" }, true, ["verify"]);
    const spki = new Uint8Array(await crypto.subtle.exportKey("spki", k));
    const b64 = btoa(String.fromCharCode(...spki));
    const lines = b64.match(/.{1,64}/g) || [];
    return `-----BEGIN PUBLIC KEY-----
${lines.join("\n")}
-----END PUBLIC KEY-----
`;
  }
  async signControl(method, path, raw = "") {
    const { priv } = await this.ensure();
    const k = await crypto.subtle.importKey("jwk", priv, { name: "Ed25519" }, false, ["sign"]);
    const ts = String(Date.now());
    const payload = `${ts}
${String(method).toUpperCase()}
${path}
${raw}`;
    const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, k, te.encode(payload)));
    return { timestamp: ts, signature: b64urlBytes(sig) };
  }
  async hmac(input) {
    const { secret } = await this.ensure();
    const k = await crypto.subtle.importKey("raw", fromB64url(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    return b64urlBytes(new Uint8Array(await crypto.subtle.sign("HMAC", k, te.encode(input))));
  }
  async signToken(payload) {
    const body = b64urlBytes(te.encode(JSON.stringify(payload)));
    return `${body}.${await this.hmac(body)}`;
  }
  async verifyToken(token, type) {
    const parts = String(token || "").split(".");
    if (parts.length !== 2) return null;
    const [body, sig] = parts;
    if (!eq(sig, await this.hmac(body))) return null;
    try {
      const p = JSON.parse(td.decode(fromB64url(body)));
      if (p.typ !== type || p.iss !== ORIGIN || p.aud !== ORIGIN || !p.exp || p.exp <= Math.floor(Date.now() / 1e3) || !Array.isArray(p.scp)) return null;
      return p;
    } catch {
      return null;
    }
  }
  async consume(kind, jti, exp) {
    const key = `used:${kind}:${jti}`;
    if (await this.ctx.storage.get(key)) return false;
    await this.ctx.storage.put(key, Number(exp) * 1e3);
    return true;
  }
  async createEmailChallenge(txId) {
    const now = Date.now();
    const key = "email-code:" + txId;
    const existing = await this.ctx.storage.get(key);
    if (existing && existing.sentAt && now - existing.sentAt < 6e4) return null;
    const code = String(crypto.getRandomValues(new Uint32Array(1))[0] % 1e8).padStart(8, "0");
    const digest = await crypto.subtle.digest("SHA-256", te.encode(txId + ":" + code));
    const hash = b64urlBytes(new Uint8Array(digest));
    await this.ctx.storage.put(key, { hash, expires: now + 6e5, attempts: 0, sentAt: now });
    return code;
  }
  async verifyEmailChallenge(txId, code) {
    const key = "email-code:" + txId;
    const rec = await this.ctx.storage.get(key);
    if (!rec || Date.now() > rec.expires || rec.attempts >= 5) return false;
    rec.attempts++;
    const digest = await crypto.subtle.digest("SHA-256", te.encode(txId + ":" + String(code || "")));
    const valid = eq(rec.hash, b64urlBytes(new Uint8Array(digest)));
    if (valid) await this.ctx.storage.delete(key);
    else await this.ctx.storage.put(key, rec);
    return valid;
  }
  async pinnedClient() {
    return String(await this.ctx.storage.get("pinnedClient") || "");
  }
  async pinClient(clientId) {
    const current = await this.pinnedClient();
    if (current && current !== clientId) return false;
    if (!current) await this.ctx.storage.put("pinnedClient", String(clientId));
    return true;
  }
};
async function control(env,path,opts={}) {return requestControl({origins:[CONTROL,CONTROL_STANDBY,"https://anthares-ara-neon-standby.anthares1.workers.dev"],path,...opts,fetchImpl:(url,init)=>url.startsWith("https://anthares-ara-neon-standby.anthares1.workers.dev/")&&env.ARA_NEON_STANDBY?env.ARA_NEON_STANDBY.fetch(url,init):fetch(url,init),sign:(method,p,raw)=>st(env).signControl(method,p,raw)});}
__name(control, "control");
async function controlJson(env, path, opts) {
  const r = await control(env, path, opts);
  const raw = await r.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { raw };
  }
  if (!r.ok) throw new Error(`control ${r.status}: ${data.error || data.raw || "request failed"}`);
  return data;
}
__name(controlJson, "controlJson");
async function consumeViaControl(env, kind, jti, exp) {
  try {
    const r = await control(env, "/v1/mcp/oauth/consume", { method: "POST", body: { kind, issuer: ORIGIN, jti, exp } });
    if (r.status === 409) return false;
    if (!r.ok) throw new Error("replay_backend_http_" + r.status);
    return true;
  } catch {
    if (kind === "oauth_owner_callback") throw new Error("owner_replay_store_unavailable");
    if (kind === "refresh_token" || kind === "authorization_code") throw new Error("oauth_replay_store_unavailable");
    return false;
  }
}
__name(consumeViaControl, "consumeViaControl");
async function status(env, device = DEFAULT_DEVICE) {
  return controlJson(env, `/v1/mcp/status?device_id=${encodeURIComponent(device)}`);
}
__name(status, "status");
async function bootstrapOtpStatus(env) {
  try {
    const r = await controlJson(env, "/v1/mcp/oauth/bootstrap-status");
    console.log("oauth_bootstrap_status active=" + String(!!r.active));
    return r;
  } catch (e) {
    console.error("oauth_bootstrap_status_error " + String(e?.message || e).slice(0, 180));
    return { active: false };
  }
}
__name(bootstrapOtpStatus, "bootstrapOtpStatus");
async function verifyBootstrapOtp(env, code) {
  try {
    const r = await controlJson(env, "/v1/mcp/oauth/bootstrap-verify", { method: "POST", body: { code: String(code || "") } });
    return !!r.ok;
  } catch (e) {
    console.error("oauth_bootstrap_verify_error " + String(e?.message || e).slice(0, 180));
    return false;
  }
}
__name(verifyBootstrapOtp, "verifyBootstrapOtp");
async function resolveDevice(env, device = DEFAULT_DEVICE) {
  if (device !== DEFAULT_DEVICE) return device;
  try {
    if ((await status(env, DEFAULT_DEVICE)).connected) return DEFAULT_DEVICE;
  } catch {
  }
  try {
    if ((await status(env, FALLBACK_DEVICE)).connected) return FALLBACK_DEVICE;
  } catch {
  }
  return DEFAULT_DEVICE;
}
__name(resolveDevice, "resolveDevice");
async function execute(env, type, args = {}, timeout = 30, device = DEFAULT_DEVICE) {
  const active = await resolveDevice(env, device);
  return controlJson(env, "/v1/mcp/execute", { method: "POST", timeoutMs: Math.min(15e4, (Number(timeout) + 12) * 1e3), body: { device_id: active, type, args, timeout_seconds: Math.max(1, Math.min(Number(timeout) || 30, 120)), idempotency_key: `cfmcp-${crypto.randomUUID()}` } });
}
__name(execute, "execute");
var TOOLS = [
  ["session_status", "Check Anthares Remote heartbeat and active control", { type: "object", properties: { device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["system_info", "Return OS, CPU, RAM, GPU and disk information", { type: "object", properties: { device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["remote_exec", "Execute PowerShell or CMD on the authorized Windows device", { type: "object", properties: { command: { type: "string" }, shell: { type: "string", enum: ["powershell", "cmd"], default: "powershell" }, timeout_seconds: { type: "integer", minimum: 1, maximum: 120, default: 30 }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["command"] }],
  ["process_list", "List running processes", { type: "object", properties: { device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["process_start", "Start an allowlisted executable", { type: "object", properties: { path: { type: "string" }, args: { type: "array", items: { type: "string" } }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["process_kill", "Terminate an allowlisted process by PID", { type: "object", properties: { pid: { type: "integer" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["pid"] }],
  ["service_status", "Read a Windows service status", { type: "object", properties: { name: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["name"] }],
  ["service_start", "Start an allowlisted Windows service", { type: "object", properties: { name: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["name"] }],
  ["service_stop", "Stop an allowlisted Windows service", { type: "object", properties: { name: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["name"] }],
  ["clipboard_get", "Read interactive desktop clipboard text", { type: "object", properties: { device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["clipboard_set", "Set interactive desktop clipboard text", { type: "object", properties: { text: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["text"] }],
  ["screenshot", "Capture a JPEG screenshot", { type: "object", properties: { display: { type: "string", default: "0" }, device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["file_stat", "Stat a file or directory inside allowlisted roots", { type: "object", properties: { path: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_list", "List a directory inside allowlisted roots", { type: "object", properties: { path: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_read", "Read a file up to 1 MiB and return base64", { type: "object", properties: { path: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_write", "Write a file up to 1 MiB from base64", { type: "object", properties: { path: { type: "string" }, base64: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path", "base64"] }],
  ["file_read_chunk", "Read a chunk of a larger file", { type: "object", properties: { path: { type: "string" }, offset: { type: "integer", minimum: 0, default: 0 }, length: { type: "integer", minimum: 1, maximum: 524288, default: 524288 }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_write_chunk", "Write a base64 chunk to a larger file", { type: "object", properties: { path: { type: "string" }, offset: { type: "integer", minimum: 0 }, base64: { type: "string" }, truncate: { type: "boolean", default: false }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path", "offset", "base64"] }],
  ["file_mkdir", "Create a directory inside allowlisted roots", { type: "object", properties: { path: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_remove", "Remove a file or directory inside allowlisted roots", { type: "object", properties: { path: { type: "string" }, recursive: { type: "boolean", default: false }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_rename", "Rename or move an allowlisted path", { type: "object", properties: { src: { type: "string" }, dst: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["src", "dst"] }],
  ["file_copy", "Copy an allowlisted path", { type: "object", properties: { src: { type: "string" }, dst: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["src", "dst"] }],
  ["file_sha256", "Calculate SHA-256 of an allowlisted file", { type: "object", properties: { path: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path"] }],
  ["file_write_atomic", "Atomically replace a file from base64", { type: "object", properties: { path: { type: "string" }, base64: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["path", "base64"] }],
  ["remote_job_start", "Start a detached background command", { type: "object", properties: { command: { type: "string" }, name: { type: "string", default: "" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["command"] }],
  ["remote_job_list", "List detached jobs", { type: "object", properties: { limit: { type: "integer", minimum: 1, maximum: 100, default: 20 }, include_command: { type: "boolean", default: false }, device_id: { type: "string", default: DEFAULT_DEVICE } } }],
  ["remote_job_status", "Get detached job status", { type: "object", properties: { job_id: { type: "string" }, include_command: { type: "boolean", default: false }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["job_id"] }],
  ["remote_job_logs", "Read detached job logs", { type: "object", properties: { job_id: { type: "string" }, offset_bytes: { type: "integer", minimum: 0 }, max_bytes: { type: "integer", minimum: 1, maximum: 262144, default: 262144 }, tail_lines: { type: "integer", minimum: 1, maximum: 5e3, default: 200 }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["job_id"] }],
  ["remote_job_cancel", "Terminate a detached job process tree", { type: "object", properties: { job_id: { type: "string" }, device_id: { type: "string", default: DEFAULT_DEVICE } }, required: ["job_id"] }],
  ["capabilities", "List capabilities exposed by the signed ARA control bridge", { type: "object", properties: {} }]
].map(([name, description, inputSchema]) => ({ name, description, inputSchema }));
function textResult(v) {
  return { content: [{ type: "text", text: typeof v === "string" ? v : JSON.stringify(v, null, 2) }] };
}
__name(textResult, "textResult");
async function callTool(env, name, a = {}, scopes = []) {
  const device = a.device_id || DEFAULT_DEVICE;
  if (device === EXTERNAL_DEVICE) return textResult(await externalReadOnly(name, { sign: (method, path, raw) => st(env).signControl(method, path, raw) }));
  if (name === "session_status") {
    let x = await status(env, device);
    if (device === DEFAULT_DEVICE && !x.connected) {
      try {
        const y = await status(env, FALLBACK_DEVICE);
        if (y.connected) x = { ...y, requested_device_id: DEFAULT_DEVICE, active_device_id: FALLBACK_DEVICE, device_failover: true };
      } catch {
      }
    }
    return textResult({ ...x, client_access: clientDiscovery(scopes) });
  }
  if (name === "capabilities") {
    // The signed Vercel bridge supports status/execute but has no capabilities route.
    // Verify the legitimate signed control path before reporting the gateway contract.
    const current = await status(env, device);
    return textResult({
      ok: true,
      protocol: "anthares-remote-agent/1.0",
      backend: current.backend,
      auth: "oauth-scopes-and-ed25519-service-signature",
      device_connected: !!current.connected,
      client_access: clientDiscovery(scopes),
      mcp_connector: { version: "1.2.0", delegated_tools: githubTools.filter(t => scopes.includes(t.scope) && (t.name === "run_claude_code" || t.name === "get_claude_code_status" || t.name === "get_claude_code_result")).map(t => ({ name: t.name, required_scope: t.scope })) },
      capabilities: ["status", "system_info", "shell", "process_list", "process_start", "process_kill",
        "service_status", "service_start", "service_stop", "clipboard_get", "clipboard_set", "screenshot",
        "file_stat", "file_list", "file_read", "file_write", "file_read_chunk", "file_write_chunk",
        "file_mkdir", "file_remove", "file_rename", "file_copy", "file_sha256", "file_write_atomic",
        "job_start", "job_list", "job_status", "job_logs", "job_cancel"]
    });
  }
  const map = { system_info: ["system_info", {}], process_list: ["process_list", {}], clipboard_get: ["clipboard_get", {}], screenshot: ["screenshot", { display: a.display || "0" }], file_stat: ["file_stat", { path: a.path }], file_list: ["file_list", { path: a.path }], file_read: ["file_read", { path: a.path }], file_write: ["file_write", { path: a.path, base64: a.base64 }], file_read_chunk: ["file_read_chunk", { path: a.path, offset: String(a.offset || 0), length: String(a.length || 524288) }], file_write_chunk: ["file_write_chunk", { path: a.path, offset: String(a.offset), base64: a.base64, truncate: a.truncate ? "1" : "0" }], file_mkdir: ["file_mkdir", { path: a.path }], file_remove: ["file_remove", { path: a.path, recursive: a.recursive ? "1" : "0" }], file_rename: ["file_rename", { src: a.src, dst: a.dst }], file_copy: ["file_copy", { src: a.src, dst: a.dst }], file_sha256: ["file_sha256", { path: a.path }], file_write_atomic: ["file_write_atomic", { path: a.path, base64: a.base64 }], clipboard_set: ["clipboard_set", { text: a.text }], process_start: ["process_start", { path: a.path, args_json: JSON.stringify(a.args || []) }], process_kill: ["process_kill", { pid: String(a.pid) }], service_status: ["service_status", { name: a.name }], service_start: ["service_start", { name: a.name }], service_stop: ["service_stop", { name: a.name }], remote_job_start: ["job_start", { command: a.command, name: a.name || "" }], remote_job_list: ["job_list", { limit: String(a.limit || 20), include_command: a.include_command ? "1" : "0" }], remote_job_status: ["job_status", { job_id: a.job_id, include_command: a.include_command ? "1" : "0" }], remote_job_logs: ["job_logs", { job_id: a.job_id, offset_bytes: a.offset_bytes === void 0 ? "" : String(a.offset_bytes), max_bytes: String(a.max_bytes || 262144), tail_lines: String(a.tail_lines || 200) }], remote_job_cancel: ["job_cancel", { job_id: a.job_id }], remote_exec: ["shell", { command: a.command, shell: a.shell || "powershell" }] };
  const m = map[name];
  if (!m) throw new Error("unknown_tool");
  const timeout = name === "remote_exec" ? a.timeout_seconds || 30 : name === "screenshot" ? 45 : 40;
  const out = await execute(env, m[0], m[1], timeout, device);
  if (name === "screenshot" && out.output) return { content: [{ type: "image", data: out.output, mimeType: "image/jpeg" }] };
  return textResult(out);
}
__name(callTool, "callTool");
function validClient(v) {
  return isKiloClient(v) || isClaudeClient(v) || v === "https://chatgpt.com/oauth/client.json" || /^https:\/\/chatgpt\.com\/oauth\/[A-Za-z0-9_-]{8,}\/client\.json$/.test(v || "");
}
__name(validClient, "validClient");
function validRedirect(v, clientId) {
  if (isKiloClient(clientId)) return isKiloCallbackPair(clientId, v);
  if (isClaudeClient(clientId)) return isClaudeCallbackPair(clientId, v);
  return v === "https://chatgpt.com/connector_platform_oauth_redirect" || /^https:\/\/chatgpt\.com\/connector\/oauth\/[A-Za-z0-9_-]+$/.test(v || "");
}
__name(validRedirect, "validRedirect");
function parseScopes(v, clientId) {
  const xs = String(v || (isClaudeClient(clientId) ? "ara.read github.read github.write" : "ara.read ara.write")).trim().split(/\s+/).filter(Boolean);
  if (!xs.length || xs.some((x) => !SCOPES.has(x))) return null;
  // A client may request ara.write, but Claude receives only the narrower scopes.
  const granted = isClaudeClient(clientId) ? xs.filter((scope) => scope !== "ara.write") : xs;
  if (!granted.length || (isClaudeClient(clientId) && !permittedClaudeScopes(granted))) return null;
  return [...new Set(granted)];
}
__name(parseScopes, "parseScopes");
function bearer(req) {
  const m = /^Bearer\s+(.+)$/i.exec(req.headers.get("authorization") || "");
  return m ? m[1] : "";
}
__name(bearer, "bearer");
async function issueTokens(env, cid, scopes) {
  const now = Math.floor(Date.now() / 1e3);
  const base = { iss: ORIGIN, aud: ORIGIN, sub: "anthares-owner", cid, scp: scopes };
  return { access_token: await st(env).signToken({ ...base, typ: "access", iat: now, exp: now + 900, jti: rand(16) }), token_type: "Bearer", expires_in: 900, refresh_token: await st(env).signToken({ ...base, typ: "refresh", iat: now, exp: now + 30 * 24 * 3600, jti: rand(16) }), scope: scopes.join(" ") };
}
__name(issueTokens, "issueTokens");
async function clientAllowed(env, cid) {
  if (!validClient(cid)) return false;
  if (isKiloClient(cid)) return true;
  // Claude Free is an independently authorized read-only client. Do not overwrite the ChatGPT client pin.
  if (isClaudeClient(cid)) return true;
  const pinned = await st(env).pinnedClient();
  return !pinned || pinned === cid;
}
__name(clientAllowed, "clientAllowed");
async function sendAuthEmail(env, code) {
  if (!env.AUTH_EMAIL_SEND) throw new Error("email_binding_not_configured");
  const from = String(env.AUTH_EMAIL_FROM || "");
  if (!from || /[\r\n]/.test(from)) throw new Error("email_sender_not_configured");
  const text = "Seu codigo de autorizacao Anthares Remote e: " + code + "\nValidade: 10 minutos. Nao compartilhe este codigo.\n";
  const r = await env.AUTH_EMAIL_SEND.send({ to: AUTH_EMAIL, from, subject: "Codigo de autorizacao Anthares Remote", text });
  if (r && r.messageId) console.log("oauth_email_sent message_id=" + String(r.messageId).slice(0, 80));
}
__name(sendAuthEmail, "sendAuthEmail");
function rpcResult(id, result) {
  return json({ jsonrpc: "2.0", id, result });
}
__name(rpcResult, "rpcResult");
function rpcError(id, code, message, data) {
  return json({ jsonrpc: "2.0", id, error: { code, message, ...data ? { data } : {} } });
}
__name(rpcError, "rpcError");
async function pendingOwner(env, tx) {
  const p = await st(env).verifyToken(tx, "oauth_pending");
  if (!p || !await clientAllowed(env, p.clientId) || !validRedirect(p.redirectUri,p.clientId) ||
      !parseScopes(p.scopes.join(" "),p.clientId)) return null;
  return p;
}
async function completeOwner(env, tx) {
  const p = await pendingOwner(env, tx);
  if (!p) return json({error:"authorization_expired"},400);
  if (!await st(env).consume("oauth_pending", p.jti, p.exp)) return json({error:"authorization_replayed"},400);
  if (!isKiloClient(p.clientId) && !await st(env).pinClient(p.clientId)) return json({error:"invalid_client"},400);
      const code = await st(env).signToken({ typ: "oauth_code", iss: ORIGIN, aud: ORIGIN, exp: Math.floor(Date.now() / 1e3) + 300, jti: rand(16), clientId: p.clientId, redirectUri: p.redirectUri, challenge: p.challenge, scopes: p.scopes, scp: p.scopes });
      const target = new URL(p.redirectUri);
      target.searchParams.set("code", code);
      if (p.state) target.searchParams.set("state", p.state);
      target.searchParams.set("iss", ORIGIN);
      return new Response(null, {status:302, headers:{location:target.toString(), "cache-control":"no-store", "referrer-policy":"no-referrer"}});
}
const ownerHelpers={origin:ORIGIN,state:st,pending:pendingOwner,complete:completeOwner};

var index_default = { async fetch(req, env) {
  const u = new URL(req.url);
  try {
    if (req.method === "GET" && (u.pathname === "/" || u.pathname === "/health")) {
      await st(env).ensure();
      let controlReady = false, connected = false, controlError = null;
      try {
        const s = await status(env, DEFAULT_DEVICE);
        controlReady = true;
        connected = !!s.connected;
      } catch(e) {controlError=/^control(?:_http_| )[0-9]{3}/.test(String(e?.message))?String(e.message).slice(0,100):"control_unavailable";
      }
      const pinned = !!await st(env).pinnedClient();
      return json({ ok: controlReady, service: "anthares-ara-mcp", provider: "cloudflare", render_independent: true, control: CONTROL, control_ready: controlReady, control_error: controlError, device_connected: connected, oauth: true, mcp: true, oauth_owner_code_mode: ownerGithubConfigured(env) ? "github_owner_identity" : "email_otp", oauth_client_pinned: pinned, mcp_server_version: "1.2.0", discovery_revision: DISCOVERY_REVISION, mcp_delegation_tools: githubTools.filter(t => t.name === "run_claude_code" || t.name === "get_claude_code_status" || t.name === "get_claude_code_result").map(t => t.name) }, controlReady ? 200 : 503);
    }
    if (req.method === "GET" && u.pathname === "/.well-known/ara-control-key") return new Response(await st(env).publicPem(), { headers: { "content-type": "application/x-pem-file", "cache-control": "no-store" } });
    if (req.method === "GET" && u.pathname === "/.well-known/oauth-protected-resource") return json({ resource: ORIGIN, authorization_servers: [ORIGIN], scopes_supported: [...SCOPES], resource_documentation: "https://github.com/UniversoAnthares/anthares-kwai-runner" });
    if (req.method === "GET" && (u.pathname === "/.well-known/oauth-authorization-server" || u.pathname === "/.well-known/openid-configuration")) return json({ issuer: ORIGIN, authorization_endpoint: `${ORIGIN}/oauth/authorize`, token_endpoint: `${ORIGIN}/oauth/token`, response_types_supported: ["code"], grant_types_supported: ["authorization_code", "refresh_token"], code_challenge_methods_supported: ["S256"], token_endpoint_auth_methods_supported: ["none"], scopes_supported: [...SCOPES], client_id_metadata_document_supported: true, authorization_response_iss_parameter_supported: true });
    if (req.method === "GET" && u.pathname === "/oauth/authorize") {
      const cid = u.searchParams.get("client_id") || "", red = u.searchParams.get("redirect_uri") || "", challenge = u.searchParams.get("code_challenge") || "", method = u.searchParams.get("code_challenge_method") || "", resource = u.searchParams.get("resource") || ORIGIN, scopes = parseScopes(u.searchParams.get("scope"), cid);
      if (!await clientAllowed(env, cid) || !validRedirect(red, cid) || u.searchParams.get("response_type") !== "code" || method !== "S256" || challenge.length < 43 || !(resource === ORIGIN || isKiloResource(cid, resource, ORIGIN) || (isClaudeClient(cid) && resource === ORIGIN + "/mcp")) || !scopes) return json({ error: "invalid_request" }, 400);
      const tx = await st(env).signToken({ typ: "oauth_pending", iss: ORIGIN, aud: ORIGIN, exp: Math.floor(Date.now() / 1e3) + 600, jti: rand(16), clientId: cid, redirectUri: red, challenge, scopes, scp: scopes, state: u.searchParams.get("state") || "" });
      if (ownerGithubConfigured(env)) return html(`<!doctype html><html><head><meta charset="utf-8"><title>Autorizar Anthares</title></head><body><main><h1>Autorizar Anthares</h1><p>Confirme a identidade da conta proprietaria UniversoAnthares pelo GitHub.</p><p>Permissoes solicitadas: ${esc(scopes.join(", "))}</p><form method="post" action="/oauth/owner/github"><input type="hidden" name="tx" value="${esc(tx)}"><button type="submit">Autorizar com GitHub</button></form></main></body></html>`);
      const bs = await bootstrapOtpStatus(env);
      if (!bs.active) {
        const code = await st(env).createEmailChallenge(tx);
        if (!code) return json({ error: "rate_limited" }, 429);
        try {
          await sendAuthEmail(env, code);
        } catch (e) {
          console.error("oauth_email_delivery_error " + String(e?.message || e).slice(0, 180));
          return json({ error: "email_delivery_unavailable" }, 503);
        }
      }
      return html(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Remote</title></head><body><main><h1>Anthares Remote</h1><p>Digite o c\xF3digo tempor\xE1rio enviado ao e-mail cadastrado. Esta autoriza\xE7\xE3o n\xE3o depende da \xE1rea de transfer\xEAncia nem da sess\xE3o interativa do Windows.</p><form method="post" action="/oauth/authorize"><input type="hidden" name="tx" value="${esc(tx)}"><label>C\xF3digo <input type="password" name="approval" autocomplete="one-time-code" required autofocus></label><button type="submit">Autorizar</button></form></main></body></html>`);
    }
    if (req.method === "POST" && u.pathname === "/oauth/owner/github") return startOwnerGithub(req,env,ownerHelpers);
    if (req.method === "GET" && u.pathname === "/oauth/owner/github/callback") return finishOwnerGithub(req,env,ownerHelpers);
    if (req.method === "POST" && u.pathname === "/oauth/authorize") {
      const f = await req.formData();
      const tx=String(f.get("tx")||"");
      const p=await pendingOwner(env,tx);
      if (!p) return json({error:"authorization_expired"},400);
      if (ownerGithubConfigured(env)) return json({error:"use_owner_github_authorization"},403);
      let attempt=false;
      for(let i=0;i<5;i++) if(await st(env).consume("oauth_email_attempt_"+i,p.jti,p.exp)){attempt=true;break;}
      if(!attempt) return json({error:"authorization_attempts_exceeded"},429);
      if (!await st(env).verifyEmailChallenge(tx,f.get("approval")||"")) return json({error:"authorization_denied"},403);
      return completeOwner(env,tx);
    }
    if (req.method === "POST" && u.pathname === "/oauth/token") {
      const f = await req.formData();
      const grant = f.get("grant_type") || "", cid = f.get("client_id") || "";
      if (!await clientAllowed(env, cid)) return json({ error: "invalid_client" }, 400);
      if (grant === "authorization_code") {
        const p = await st(env).verifyToken(f.get("code") || "", "oauth_code");
        if (!p || p.clientId !== cid || p.redirectUri !== (f.get("redirect_uri") || "")) return json({ error: "invalid_grant" }, 400);
        const verifier = f.get("code_verifier") || "";
        if (verifier.length < 43 || !eq(await sha256b64(verifier), p.challenge) || !await consumeViaControl(env, "authorization_code", p.jti, p.exp)) return json({ error: "invalid_grant" }, 400);
        return json(await issueTokens(env, cid, p.scopes));
      }
      if (grant === "refresh_token") {
        const p = await st(env).verifyToken(f.get("refresh_token") || "", "refresh");
        if (!p || p.cid !== cid || !await consumeViaControl(env, "refresh_token", p.jti, p.exp)) return json({ error: "invalid_grant" }, 400);
        return json(await issueTokens(env, cid, p.scp));
      }
      return json({ error: "unsupported_grant_type" }, 400);
    }
    if (u.pathname === "/mcp") {
      if (req.method !== "POST") return new Response("", { status: 405, headers: { Allow: "POST" } });
      const token = await st(env).verifyToken(bearer(req), "access");
      if (!token) return json({ error: "unauthorized" }, 401, { "www-authenticate": `Bearer resource_metadata="${ORIGIN}/.well-known/oauth-protected-resource", scope="ara.read ara.write github.read github.write"` });
      let rpc;
      try {
        rpc = await req.json();
      } catch {
        return json({ error: "invalid_json" }, 400);
      }
      if (rpc.method === "notifications/initialized" || String(rpc.method || "").startsWith("notifications/")) return new Response(null, { status: 202 });
      if (rpc.method === "initialize") return rpcResult(rpc.id, { protocolVersion: rpc.params?.protocolVersion || "2025-06-18", capabilities: { tools: { listChanged: false } }, serverInfo: { name: "Anthares Remote", version: "1.2.0" }, instructions: CLIENT_INSTRUCTIONS });
      if (rpc.method === "ping") return rpcResult(rpc.id, {});
      if (rpc.method === "tools/list") return rpcResult(rpc.id, { tools: TOOLS.filter(t => token.scp.includes(WRITE_TOOLS.has(t.name) ? "ara.write" : "ara.read")).concat(githubTools.concat(approvedTestTool).filter(t => token.scp.includes(t.scope)).map(({scope, ...tool}) => tool)) });
      if (rpc.method === "tools/call") {
        const name = rpc.params?.name || "";
        const githubTool = githubTools.concat(approvedTestTool).find(t => t.name === name);
        const required = githubTool ? githubTool.scope : (WRITE_TOOLS.has(name) ? "ara.write" : "ara.read");
        if (!token.scp.includes(required)) return rpcError(rpc.id, -32003, "insufficient_scope", { required_scope: required });
        try {
          const result = name === "run_tests" ? textResult(await runApprovedTests(env, rpc.params?.arguments || {}, (type,args,timeout)=>execute(env,type,args,timeout), (kind,jti,exp)=>st(env).consume(kind,jti,exp), (status,id,result)=>recordApprovedRegression(env,status,id,result))) : githubTool ? textResult(await callGithubTool(env, name, rpc.params?.arguments || {})) : await callTool(env, name, rpc.params?.arguments || {}, token.scp);
          return rpcResult(rpc.id, result);
        } catch (e) {
          return rpcResult(rpc.id, { content: [{ type: "text", text: String(e?.message || e) }], isError: true });
        }
      }
      return rpcError(rpc.id, -32601, "Method not found");
    }
    return json({ error: "not_found" }, 404);
  } catch (e) {
    if (e?.message === "oauth_replay_store_unavailable") return json({ error: "temporarily_unavailable" }, 503, { "Retry-After": "5" });
    return json({ error: "internal_error", detail: String(e?.message || e) }, 500);
  }
} };
export {
  GatewayState,
  index_default as default
};
//# sourceMappingURL=index.js.map
