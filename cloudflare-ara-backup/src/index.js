import { DurableObject } from "cloudflare:workers";

const VERSION = "2026-10-13-ara-cloudflare-backup-v1";
const SIGNER = "anthares-remote-mcp";
const KEY_URLS = [
  "https://anthares-remote-mcp-v2.onrender.com/.well-known/ara-control-key",
  "https://anthares-remote-mcp.onrender.com/.well-known/ara-control-key",
];
const DEVICE_HASH_BASE =
  "https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices";
const SAFE_RETRY = new Set([
  "ping", "system_info", "process_list", "clipboard_get", "file_stat",
  "file_list", "file_read", "file_read_chunk", "job_list", "job_status", "job_logs",
]);
const FINAL = new Set(["done", "failed", "expired"]);
const CAPABILITIES = [
  "status", "system_info", "shell", "process_list", "process_start", "process_kill",
  "service_status", "service_start", "service_stop", "clipboard_get", "clipboard_set", "screenshot",
  "file_stat", "file_list", "file_read", "file_write", "file_read_chunk", "file_write_chunk",
  "file_mkdir", "file_remove", "file_rename", "file_copy", "file_sha256", "file_write_atomic",
  "job_start", "job_list", "job_status", "job_logs", "job_cancel",
];

function json(data, status = 200) {
  return Response.json(data, {
    status,
    headers: {
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}
function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function iso(ms) { return new Date(ms).toISOString(); }
function parseJson(text, fallback = {}) {
  try { return JSON.parse(text); } catch { return fallback; }
}
function b64urlBytes(value) {
  let s = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const raw = atob(s);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}
function pemDer(pem) {
  const body = String(pem || "")
    .replace(/-----BEGIN PUBLIC KEY-----/g, "")
    .replace(/-----END PUBLIC KEY-----/g, "")
    .replace(/\s+/g, "");
  const raw = atob(body);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}
function concatBytes(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0);
  out.set(b, a.length);
  return out;
}
async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(String(value || ""));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, "0")).join("");
}
function constantEqual(a, b) {
  a = String(a || ""); b = String(b || "");
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
function state(env) {
  const id = env.ARA_STATE.idFromName("global");
  return env.ARA_STATE.get(id);
}

let keyCache = { at: 0, keys: [] };
async function signingKeys(force = false) {
  if (!force && keyCache.keys.length && Date.now() - keyCache.at < 60000) return keyCache.keys;
  const keys = [];
  for (const url of KEY_URLS) {
    try {
      const r = await fetch(url, {
        headers: { "User-Agent": "AntharesARACloudflare/1.0", "cache-control": "no-cache" },
      });
      if (!r.ok) continue;
      const pem = await r.text();
      if (pem.length > 4096) continue;
      const key = await crypto.subtle.importKey(
        "spki", pemDer(pem), { name: "Ed25519" }, false, ["verify"]
      );
      keys.push(key);
    } catch {}
  }
  if (!keys.length) throw new Error("no_mcp_signing_key");
  keyCache = { at: Date.now(), keys };
  return keys;
}
async function verifyMcp(request, env) {
  if ((request.headers.get("X-ARA-Signer") || "") !== SIGNER) return false;
  const ts = request.headers.get("X-ARA-Timestamp") || "";
  const sig = request.headers.get("X-ARA-Signature") || "";
  const tsNum = Number(ts);
  if (!Number.isFinite(tsNum) || Math.abs(Date.now() - tsNum) > 30000 || !sig) return false;
  const clone = request.clone();
  const raw = new Uint8Array(await clone.arrayBuffer());
  if (raw.length > 3 * 1024 * 1024) return false;
  const u = new URL(request.url);
  const prefix = new TextEncoder().encode(`${ts}\n${request.method.toUpperCase()}\n${u.pathname}${u.search}\n`);
  const payload = concatBytes(prefix, raw);
  let signature;
  try { signature = b64urlBytes(sig); } catch { return false; }

  for (const force of [false, true]) {
    let keys = [];
    try { keys = await signingKeys(force); } catch {}
    for (const key of keys) {
      try {
        if (await crypto.subtle.verify({ name: "Ed25519" }, key, signature, payload)) {
          return await state(env).consumeReplay(sig, Date.now() + 60000);
        }
      } catch {}
    }
  }
  return false;
}

const deviceHashCache = new Map();
function validDeviceId(device) {
  return /^[A-Za-z0-9_.-]{1,200}$/.test(String(device || ""));
}
function validHash(value) {
  return /^[0-9a-f]{64}$/.test(String(value || "").toLowerCase());
}
async function expectedDeviceHash(device) {
  const cached = deviceHashCache.get(device);
  if (cached && Date.now() - cached.at < 60000) return cached.hash;
  try {
    const r = await fetch(`${DEVICE_HASH_BASE}/${encodeURIComponent(device)}.sha256`, {
      headers: { "User-Agent": "AntharesARACloudflare/1.0", "cache-control": "no-cache" },
    });
    if (!r.ok) return "";
    const hash = (await r.text()).trim().toLowerCase();
    if (!validHash(hash)) return "";
    deviceHashCache.set(device, { at: Date.now(), hash });
    return hash;
  } catch {
    return "";
  }
}
async function deviceOk(request) {
  const device = (request.headers.get("X-Anthares-Device") || "").trim();
  if (!validDeviceId(device)) return { ok: false, device: "" };
  const auth = request.headers.get("Authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token) return { ok: false, device };
  const expected = await expectedDeviceHash(device);
  const actual = await sha256Hex(token);
  return { ok: !!expected && constantEqual(expected, actual), device };
}

export class AraState extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS ara_devices(
        device_id TEXT PRIMARY KEY,
        heartbeat TEXT NOT NULL,
        seen_at INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS ara_jobs(
        id TEXT PRIMARY KEY,
        device_id TEXT NOT NULL,
        type TEXT NOT NULL,
        args TEXT NOT NULL,
        timeout_seconds INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        status TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        lease_until INTEGER,
        idempotency_key TEXT,
        result TEXT
      );
      CREATE UNIQUE INDEX IF NOT EXISTS ara_jobs_dedupe
        ON ara_jobs(device_id,idempotency_key) WHERE idempotency_key IS NOT NULL;
      CREATE INDEX IF NOT EXISTS ara_jobs_pick
        ON ara_jobs(device_id,status,created_at);
      CREATE TABLE IF NOT EXISTS ara_oauth_consumed(
        kind TEXT NOT NULL,
        issuer TEXT NOT NULL,
        jti TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER NOT NULL,
        PRIMARY KEY(kind,issuer,jti)
      );
      CREATE TABLE IF NOT EXISTS ara_replay(
        signature TEXT PRIMARY KEY,
        expires_at INTEGER NOT NULL
      );
    `);
  }

  _row(raw) {
    if (!raw) return null;
    return {
      id: raw.id,
      device_id: raw.device_id,
      type: raw.type,
      args: parseJson(raw.args, {}),
      timeout_seconds: Number(raw.timeout_seconds || 30),
      status: raw.status,
      created_at: iso(Number(raw.created_at)),
      expires_at: iso(Number(raw.expires_at)),
      lease_until: raw.lease_until ? iso(Number(raw.lease_until)) : null,
      attempts: Number(raw.attempts || 0),
      result: raw.result ? parseJson(raw.result, {}) : null,
      idempotency_key: raw.idempotency_key || null,
    };
  }

  _one(sql, ...args) {
    return this.sql.exec(sql, ...args).toArray()[0] || null;
  }

  _reap(device) {
    const now = Date.now();
    const rows = this.sql.exec(
      "SELECT * FROM ara_jobs WHERE device_id=? AND status IN ('queued','leased','uncertain')",
      device
    ).toArray();
    const unknown = JSON.stringify({
      ok: false, error: "execution_outcome_unknown", reconciled: "expired_after_deadline",
    });
    for (const row of rows) {
      const expires = Number(row.expires_at || 0);
      const lease = row.lease_until == null ? null : Number(row.lease_until);
      if (row.status === "uncertain" && expires <= now) {
        this.sql.exec(
          "UPDATE ara_jobs SET status='expired',lease_until=NULL,result=COALESCE(result,?) WHERE id=?",
          unknown, row.id
        );
        continue;
      }
      if (expires <= now) {
        const next = row.status === "leased" && !SAFE_RETRY.has(row.type) ? "uncertain" : "expired";
        this.sql.exec("UPDATE ara_jobs SET status=?,lease_until=NULL WHERE id=?", next, row.id);
        continue;
      }
      if (row.status === "leased" && lease !== null && lease <= now) {
        this.sql.exec(
          "UPDATE ara_jobs SET status=?,lease_until=NULL WHERE id=?",
          SAFE_RETRY.has(row.type) ? "queued" : "uncertain",
          row.id
        );
      }
    }
  }

  async consumeReplay(signature, expiresAt) {
    const now = Date.now();
    this.sql.exec("DELETE FROM ara_replay WHERE expires_at<=?", now);
    const existing = this._one("SELECT signature FROM ara_replay WHERE signature=?", signature);
    if (existing) return false;
    this.sql.exec("INSERT INTO ara_replay(signature,expires_at) VALUES(?,?)", signature, Number(expiresAt));
    return true;
  }

  async heartbeat(device, payload) {
    const now = Date.now();
    const body = { ...(payload || {}), seen_at: iso(now) };
    this.sql.exec(
      `INSERT INTO ara_devices(device_id,heartbeat,seen_at) VALUES(?,?,?)
       ON CONFLICT(device_id) DO UPDATE SET heartbeat=excluded.heartbeat,seen_at=excluded.seen_at`,
      device, JSON.stringify(body), now
    );
    return { heartbeat: body, seen_at: iso(now) };
  }

  async status(device, freshnessSeconds = 90) {
    this._reap(device);
    const d = this._one("SELECT heartbeat,seen_at FROM ara_devices WHERE device_id=?", device);
    const counts = this._one(
      `SELECT
         SUM(CASE WHEN status='queued' THEN 1 ELSE 0 END) queued,
         SUM(CASE WHEN status='leased' THEN 1 ELSE 0 END) leased,
         SUM(CASE WHEN status='uncertain' THEN 1 ELSE 0 END) uncertain
       FROM ara_jobs WHERE device_id=?`, device
    ) || {};
    const seen = d ? Number(d.seen_at) : 0;
    const age = seen ? (Date.now() - seen) / 1000 : null;
    return {
      heartbeat: d ? parseJson(d.heartbeat, null) : null,
      seen_at: seen ? iso(seen) : null,
      connected: age !== null && age >= 0 && age <= Number(freshnessSeconds || 90),
      queued: Number(counts.queued || 0),
      leased: Number(counts.leased || 0),
      uncertain: Number(counts.uncertain || 0),
    };
  }

  async createJob(device, type, args, timeoutSeconds = 30, idempotencyKey = null) {
    const timeout = Math.max(1, Math.min(Number(timeoutSeconds || 30), 120));
    const key = String(idempotencyKey || "").trim() || null;
    if (key) {
      const existing = this._one(
        "SELECT * FROM ara_jobs WHERE device_id=? AND idempotency_key=?", device, key
      );
      if (existing) return { job: this._row(existing), created: false };
    }
    const id = crypto.randomUUID().replace(/-/g, "");
    const created = Date.now();
    const expires = created + (timeout + 30) * 1000;
    this.sql.exec(
      `INSERT INTO ara_jobs(
         id,device_id,type,args,timeout_seconds,created_at,expires_at,status,attempts,lease_until,idempotency_key,result
       ) VALUES(?,?,?,?,?,?,?,'queued',0,NULL,?,NULL)`,
      id, device, type, JSON.stringify(args || {}), timeout, created, expires, key
    );
    return { job: this._row(this._one("SELECT * FROM ara_jobs WHERE id=?", id)), created: true };
  }

  async leaseNext(device, leaseSeconds = 35) {
    this._reap(device);
    const picked = this._one(
      "SELECT * FROM ara_jobs WHERE device_id=? AND status='queued' AND expires_at>? ORDER BY created_at LIMIT 1",
      device, Date.now()
    );
    if (!picked) return null;
    const until = Date.now() + Math.max(5, Math.min(Number(leaseSeconds || 35), 120)) * 1000;
    this.sql.exec(
      "UPDATE ara_jobs SET status='leased',attempts=attempts+1,lease_until=? WHERE id=? AND status='queued'",
      until, picked.id
    );
    return this._row(this._one("SELECT * FROM ara_jobs WHERE id=?", picked.id));
  }

  async submitResult(device, jobId, result) {
    const row = this._one("SELECT * FROM ara_jobs WHERE id=? AND device_id=?", jobId, device);
    if (!row) return "missing";
    if (FINAL.has(row.status)) {
      const oldResult = row.result ? parseJson(row.result, {}) : {};
      return JSON.stringify(oldResult) === JSON.stringify(result || {}) ? "duplicate" : "conflict";
    }
    if (!["leased", "uncertain"].includes(row.status)) return "not_leased";
    const previous = row.status;
    const status = result && result.ok ? "done" : "failed";
    this.sql.exec(
      "UPDATE ara_jobs SET status=?,result=?,lease_until=NULL WHERE id=? AND device_id=?",
      status, JSON.stringify(result || {}), jobId, device
    );
    return previous === "uncertain" ? "resolved_uncertain" : "stored";
  }

  async getJob(device, jobId) {
    this._reap(device);
    return this._row(this._one("SELECT * FROM ara_jobs WHERE id=? AND device_id=?", jobId, device));
  }

  async consumeOauth(kind, issuer, jti, expSeconds) {
    const now = Date.now();
    const exp = Number(expSeconds) * 1000;
    if (!["authorization_code", "refresh_token"].includes(kind)) return false;
    if (!issuer || issuer.length > 300 || !jti || jti.length > 128) return false;
    if (!Number.isFinite(exp) || exp <= now || exp > now + 32 * 24 * 3600 * 1000) return false;
    this.sql.exec("DELETE FROM ara_oauth_consumed WHERE expires_at<=?", now);
    const existing = this._one(
      "SELECT jti FROM ara_oauth_consumed WHERE kind=? AND issuer=? AND jti=?", kind, issuer, jti
    );
    if (existing) return false;
    this.sql.exec(
      "INSERT INTO ara_oauth_consumed(kind,issuer,jti,expires_at,consumed_at) VALUES(?,?,?,?,?)",
      kind, issuer, jti, exp, now
    );
    return true;
  }

  async health() {
    const probe = "health-" + crypto.randomUUID();
    const t = Date.now();
    this.sql.exec(
      "INSERT INTO ara_replay(signature,expires_at) VALUES(?,?)",
      probe, t + 5000
    );
    const exists = !!this._one("SELECT signature FROM ara_replay WHERE signature=?", probe);
    this.sql.exec("DELETE FROM ara_replay WHERE signature=?", probe);
    return { ok: exists, backend: "cloudflare-durable-object-sqlite", version: VERSION };
  }

  async selfTest() {
    const device = "selftest-" + crypto.randomUUID().replace(/-/g, "");
    const idem = "selftest-" + crypto.randomUUID().replace(/-/g, "");
    const created = await this.createJob(device, "ping", { probe: true }, 30, idem);
    const duplicate = await this.createJob(device, "ping", { probe: true }, 30, idem);
    const leased = await this.leaseNext(device, 5);
    const result = { ok: true, output: "pong" };
    const stored = leased ? await this.submitResult(device, leased.id, result) : "missing";
    const final = leased ? await this.getJob(device, leased.id) : null;
    const checks = {
      create: !!created.created,
      idempotency: duplicate.job && duplicate.job.id === created.job.id && !duplicate.created,
      lease: leased && leased.id === created.job.id && leased.status === "leased",
      result: stored === "stored" && final && final.status === "done" && final.result?.output === "pong",
    };
    this.sql.exec("DELETE FROM ara_jobs WHERE device_id=?", device);
    return { ok: Object.values(checks).every(Boolean), checks };
  }
}

async function handleMcpExecute(request, env) {
  if (!(await verifyMcp(request, env))) return json({ error: "unauthorized" }, 401);
  let body;
  try { body = await request.json(); } catch { return json({ error: "invalid_request" }, 400); }
  const device = String(body.device_id || "").trim();
  const type = String(body.type || "").trim();
  const timeout = Math.max(1, Math.min(Number(body.timeout_seconds || 30), 120));
  const idem = String(body.idempotency_key || "").trim();
  if (!device || !type) return json({ error: "missing_device_id_or_type" }, 400);
  if (idem.length > 200) return json({ error: "idempotency_key_too_long" }, 400);
  const st = state(env);
  const created = await st.createJob(device, type, body.args || {}, timeout, idem || null);
  const deadline = Date.now() + Math.min(timeout + 8, 130) * 1000;
  let current = created.job;
  while (Date.now() < deadline) {
    current = await st.getJob(device, created.job.id);
    if (!current) return json({ error: "job_lost" }, 503);
    if (["done", "failed", "expired", "uncertain"].includes(current.status)) break;
    await delay(200);
  }
  if (!current) return json({ error: "job_lost" }, 503);
  if (current.status === "uncertain") {
    return json({
      ok: false, status: current.status, job_id: current.id, error: "execution_outcome_unknown",
    }, 409);
  }
  if (!["done", "failed"].includes(current.status)) {
    return json({
      ok: false, status: current.status, job_id: current.id, error: "timeout_waiting_for_device",
    }, 504);
  }
  const result = current.result || {};
  return json({
    ok: !!result.ok,
    status: current.status,
    job_id: current.id,
    output: result.output ?? null,
    error: result.error ?? null,
    started_at: result.started_at ?? null,
    ended_at: result.ended_at ?? null,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const st = state(env);

    if (url.pathname === "/healthz" || url.pathname === "/") {
      try {
        const h = await st.health();
        return json({
          ...h,
          provider: "cloudflare",
          role: "ara-backup-control",
          persistence_cycle: true,
          independent_of_render_postgres: true,
        }, h.ok ? 200 : 503);
      } catch (e) {
        return json({ ok: false, backend: "cloudflare-durable-object-sqlite", error: e?.name || "error" }, 503);
      }
    }
    if (url.pathname === "/_selftest") {
      try {
        const r = await st.selfTest();
        return json(r, r.ok ? 200 : 503);
      } catch (e) {
        return json({ ok: false, error: e?.name || "error" }, 503);
      }
    }

    if (url.pathname === "/v1/device/auth-check" && request.method === "GET") {
      const auth = await deviceOk(request);
      return auth.ok ? json({ ok: true }) : json({ ok: false, error: "unauthorized" }, 401);
    }

    if (url.pathname === "/v1/device/heartbeat" && request.method === "POST") {
      const auth = await deviceOk(request);
      if (!auth.ok) return json({ error: "unauthorized" }, 401);
      let body = {};
      try { body = await request.json(); } catch {}
      await st.heartbeat(auth.device, body);
      return json({ ok: true });
    }

    if (url.pathname === "/v1/device/jobs/next" && request.method === "GET") {
      const auth = await deviceOk(request);
      if (!auth.ok) return json({ error: "unauthorized" }, 401);
      const job = await st.leaseNext(auth.device, 35);
      return job ? json({ job }) : new Response(null, { status: 204 });
    }

    const resultMatch = url.pathname.match(/^\/v1\/device\/jobs\/([A-Za-z0-9_-]{1,100})\/result$/);
    if (resultMatch && request.method === "POST") {
      const auth = await deviceOk(request);
      if (!auth.ok) return json({ error: "unauthorized" }, 401);
      let body = {};
      try { body = await request.json(); } catch {}
      const outcome = await st.submitResult(auth.device, resultMatch[1], body);
      if (outcome === "missing") return json({ error: "unknown_job_or_wrong_device" }, 404);
      if (outcome === "not_leased") return json({ error: "job_not_leased" }, 409);
      if (outcome === "conflict") return json({ error: "result_conflict" }, 409);
      return json({ ok: true, duplicate: outcome === "duplicate" });
    }

    if (url.pathname === "/v1/mcp/status" && request.method === "GET") {
      if (!(await verifyMcp(request, env))) return json({ error: "unauthorized" }, 401);
      const device = (url.searchParams.get("device_id") || "").trim();
      if (!device) return json({ error: "missing_device_id" }, 400);
      return json(await st.status(device));
    }

    if (url.pathname === "/v1/mcp/capabilities" && request.method === "GET") {
      if (!(await verifyMcp(request, env))) return json({ error: "unauthorized" }, 401);
      return json({
        ok: true,
        protocol: "anthares-remote-agent/1.0",
        auth: "ed25519-service-signature",
        durability: "cloudflare-durable-object-sqlite",
        provider: "cloudflare",
        replay_protection: true,
        oauth_one_time_tokens: "cloudflare-durable-object-sqlite",
        redundant_mcp_keys: true,
        rotating_service_key_refresh: true,
        trusted_mcp_services: KEY_URLS.length,
        capabilities: CAPABILITIES,
      });
    }

    if (url.pathname === "/v1/mcp/oauth/consume" && request.method === "POST") {
      if (!(await verifyMcp(request, env))) return json({ error: "unauthorized" }, 401);
      let body;
      try { body = await request.json(); } catch { return json({ error: "invalid_request" }, 400); }
      const consumed = await st.consumeOauth(
        String(body.kind || ""), String(body.issuer || ""), String(body.jti || ""), body.exp
      );
      if (!consumed) return json({ ok: false, error: "already_used_or_invalid" }, 409);
      return json({ ok: true, consumed: true });
    }

    if (url.pathname === "/v1/mcp/execute" && request.method === "POST") {
      return await handleMcpExecute(request, env);
    }

    return json({ error: "not_found" }, 404);
  },
};
