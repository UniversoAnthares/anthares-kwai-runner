import { DurableObject } from "cloudflare:workers";

/**
 * CF-03 isolated acceptance harness. No social API, no external fetches,
 * no shared store, no social publisher references, no cron, no production queues.
 */
const MAIN = "cf03-qa-main-r0725";
const DLQ = "cf03-qa-dlq-r0725";
const CASES = Object.freeze({
  "cf03-r0725-once": "once",
  "cf03-r0725-retry": "retry_once",
  "cf03-r0725-fail": "always_fail",
});
const json = (value, status = 200) => Response.json(value, {
  status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" },
});

export class Cf03Ledger extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    const sql = this.ctx.storage.sql;
    sql.exec("CREATE TABLE IF NOT EXISTS seeds (key TEXT PRIMARY KEY)");
    sql.exec("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, attempts INTEGER NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS effects (id TEXT PRIMARY KEY)");
    sql.exec("CREATE TABLE IF NOT EXISTS deadletter (id TEXT PRIMARY KEY)");
  }
  async fetch(request) {
    const path = new URL(request.url).pathname;
    const sql = this.ctx.storage.sql;
    if (request.method === "GET" && path === "/status") {
      return json({
        attempts: sql.exec("SELECT id, attempts FROM attempts ORDER BY id").toArray(),
        effects: sql.exec("SELECT id FROM effects ORDER BY id").toArray(),
        deadletter: sql.exec("SELECT id FROM deadletter ORDER BY id").toArray(),
        seeds: sql.exec("SELECT key FROM seeds ORDER BY key").toArray().length,
      });
    }
    if (request.method !== "POST") return json({ok:false,error:"method"},405);
    let body;
    try { body = await request.json(); } catch { return json({ok:false,error:"json"},400); }
    if (path === "/claim") {
      if (body.key !== "cf03-r0725-seed") return json({ok:false,error:"claim"},400);
      const already = sql.exec("SELECT key FROM seeds WHERE key=?", body.key).toArray().length > 0;
      if (already) return json({ok:true,claimed:false});
      sql.exec("INSERT INTO seeds (key) VALUES (?)", body.key);
      return json({ok:true,claimed:true});
    }
    const id = body.id, mode = CASES[id];
    if (!mode || mode !== body.mode) return json({ok:false,error:"fixture"},400);
    if (path === "/attempt") {
      sql.exec("INSERT INTO attempts(id,attempts) VALUES (?,1) ON CONFLICT(id) DO UPDATE SET attempts=attempts+1", id);
      if (mode !== "always_fail") sql.exec("INSERT OR IGNORE INTO effects(id) VALUES (?)", id);
      const row = sql.exec("SELECT attempts FROM attempts WHERE id=?", id).toArray()[0];
      return json({ok:true,attempts:row.attempts});
    }
    if (path === "/dlq" && mode === "always_fail") {
      sql.exec("INSERT OR IGNORE INTO deadletter(id) VALUES (?)", id);
      return json({ok:true,dlq:true});
    }
    return json({ok:false,error:"route"},404);
  }
}

function ledger(env) {
  return env.CF03_LEDGER.get(env.CF03_LEDGER.idFromName("cf03-test-r0725"));
}

async function internal(stub, path, data) {
  const response = await stub.fetch("https://cf03.internal" + path, data === undefined
    ? {method:"GET"} : {method:"POST",body:JSON.stringify(data)});
  if (!response.ok) throw new Error("CF03_LEDGER_OPERATION_DENIED");
  const value = await response.json();
  if (value.ok === false) throw new Error("CF03_LEDGER_CONTRACT_FAILED");
  return value;
}

export default {
  async fetch(request, env) {
    const p = new URL(request.url).pathname;
    if (request.method === "GET" && p === "/health") {
      return json({ok:true,service:"cf03-queue-dlq-qa",
        queue:MAIN,dlq:DLQ,durable_ledger:!!env.CF03_LEDGER,
        source_queue_binding:!!env.CF03_QUEUE,publication_allowed:false,
        external_destinations:0});
    }
    if (request.method === "GET" && p === "/status") {
      return json(await internal(ledger(env),"/status"));
    }
    if (request.method === "POST" && p === "/__cf03/seed") {
      const given = request.headers.get("X-CF03-Run-Key");
      if (!given || !env.CF03_RUN_KEY || given !== String(env.CF03_RUN_KEY).trim()) {
        return json({ok:false,error:"unauthorized"},401);
      }
      const ticket = await internal(ledger(env),"/claim",{key:"cf03-r0725-seed"});
      if (!ticket.claimed) return json({ok:true,already_seeded:true},200);
      await env.CF03_QUEUE.sendBatch(Object.entries(CASES).map(([id,mode]) => ({
        body:{id,mode,scope:"synthetic-cf03"},
      })));
      return json({ok:true,seeded:3,scope:"synthetic-cf03"},202);
    }
    return json({ok:false,error:"not_found"},404);
  },
  async queue(batch, env) {
    if (batch.queue !== MAIN && batch.queue !== DLQ) {
      throw new Error("CF03_FOREIGN_QUEUE_REFUSED");
    }
    const stub = ledger(env);
    for (const message of batch.messages) {
      const body = message.body || {};
      if (body.scope !== "synthetic-cf03" || CASES[body.id] !== body.mode) {
        message.retry({delaySeconds:1});
        continue;
      }
      if (batch.queue === DLQ) {
        if (body.mode !== "always_fail") throw new Error("CF03_FOREIGN_DLQ_MESSAGE");
        await internal(stub,"/dlq",body);
        message.ack();
        continue;
      }
      const evidence = await internal(stub,"/attempt",body);
      if (body.mode === "always_fail" ||
          (body.mode === "retry_once" && evidence.attempts === 1)) {
        message.retry({delaySeconds:1});
      } else {
        message.ack();
      }
    }
  },
};
