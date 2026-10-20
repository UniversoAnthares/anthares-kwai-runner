// Stub do pg para testes de unidade do router.mjs
// Suporta: CREATE TABLE, SELECT 1, ara_rate_limit, ara_remote_job_audit,
// ara_reserve_jobs (insert/select/update), ara_reserve_devices, ara_oauth_consumed

let rateLimitRows = new Map(); // key: "${token_identity}:${window_start}" -> {count}
let auditRows = [];
let jobs = new Map(); // job_id -> {id, status, result, type, args}
let nextRemoteJobResult = null; // fixture para simular o handler do agente

export class Pool {
  constructor(opts) { this.opts = opts; }
  async query(sql, params) {
    const s = String(sql);
    if (s.includes('CREATE TABLE') || s.includes('CREATE UNIQUE INDEX') || s.includes('SELECT 1')) {
      return { rows: [], rowCount: 0 };
    }
    if (s.includes('INSERT INTO ara_rate_limit') || s.includes('UPDATE ara_rate_limit')) {
      const [identity, windowStart] = params;
      const key = `${identity}:${windowStart}`;
      const existing = rateLimitRows.get(key) || { count: 0 };
      existing.count++;
      rateLimitRows.set(key, existing);
      return { rows: [{ count: existing.count }], rowCount: 1 };
    }
    if (s.includes('DELETE FROM ara_rate_limit')) {
      return { rows: [], rowCount: 0 };
    }
    if (s.includes('INSERT INTO ara_remote_job_audit')) {
      auditRows.push({ params });
      return { rows: [], rowCount: 1 };
    }
    if (s.includes('SELECT heartbeat,seen_at FROM ara_reserve_devices')) {
      return { rows: [{ heartbeat: '{}', seen_at: new Date() }], rowCount: 1 };
    }
    if (s.includes('INSERT INTO ara_reserve_jobs')) {
      const [id, device, type, args, timeout, , , status] = params;
      const jobId = id || `job-${Math.random().toString(36).slice(2)}`;
      const job = { id: jobId, status: 'queued', result: null, type, args: JSON.parse(args || '{}') };
      if (type === 'remote_job') {
        // Simula o agente Windows executando: por padrao devolve sucesso
        job.status = 'done';
        job.result = nextRemoteJobResult || { ok: true, exit_code: 0, output: 'ok' };
      }
      jobs.set(jobId, job);
      return { rows: [{ id: jobId, status: job.status }], rowCount: 1 };
    }
    if (s.includes('SELECT * FROM ara_reserve_jobs WHERE id')) {
      const [id] = params;
      const job = jobs.get(id);
      if (!job) return { rows: [], rowCount: 0 };
      return { rows: [job], rowCount: 1 };
    }
    if (s.includes('idempotency_key')) {
      //_lookup de idempotencia: devolve vazio (job novo a cada chamada de teste)
      return { rows: [], rowCount: 0 };
    }
    if (s.includes('UPDATE ara_reserve_jobs SET status')) {
      const [status, result, id] = params;
      const job = jobs.get(id);
      if (job) {
        job.status = result?.ok ? 'done' : 'failed';
        job.result = JSON.parse(result || '{}');
      }
      return { rows: [], rowCount: 1 };
    }
    if (s.includes('INSERT INTO ara_oauth_consumed')) {
      return { rows: [], rowCount: 1 };
    }
    throw new Error('db_not_available: ' + s.slice(0, 80));
  }
  async end() { return Promise.resolve(); }
}

// Estado exportado para inspeção nos testes
export function getState() { return { rateLimitRows, auditRows, jobs }; }
export function resetState() {
  rateLimitRows.clear();
  auditRows = [];
  jobs.clear();
  nextRemoteJobResult = null;
}
export function setNextRemoteJobResult(result) { nextRemoteJobResult = result; }
