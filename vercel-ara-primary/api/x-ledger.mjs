import crypto from 'node:crypto';
import { Pool } from 'pg';

// ARA production X exactly-once ledger. All runners share this Neon-backed
// service, never an independent local or Northflank-only publication fence.
const REPO = 'UniversoAnthares/anthares-kwai-runner';
const ACCOUNT = 'lucasyahn';
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 3,
  ssl: { rejectUnauthorized: false }, connectionTimeoutMillis: 12000 });
const authCache = new Map();
const id = key => crypto.createHash('sha256').update('x:'+ACCOUNT+':'+key).digest('hex');
const validKey = key => /^[A-Za-z0-9_.:-]{12,160}$/.test(key || '');
const validPost = url => /^https:\/\/x\.com\/lucasyahn\/status\/[0-9]+$/.test(url || '');
function reply(res, status, data) {
  res.setHeader('Cache-Control','no-store');
  return res.status(status).json(data);
}
async function authorize(req) {
  const match = /^Bearer\s+(.+)$/i.exec(String(req.headers.authorization || ''));
  if (!match || match[1].length < 25 || match[1].length > 1000) return false;
  const token = match[1];
  const digest = crypto.createHash('sha256').update(token).digest('hex');
  if (authCache.get(digest) > Date.now()) return true;
  const header = { 'Authorization':'Bearer '+token, 'Accept':'application/vnd.github+json',
    'User-Agent':'Anthares-X-Neon-Ledger' };
  const fetchJson = async url => {
    const response = await fetch(url, { headers:header, signal:AbortSignal.timeout(8500) });
    if (!response.ok) return null;
    return response.json();
  };
  const user = await fetchJson('https://api.github.com/user');
  if (String(user?.login || '').toLowerCase() !== 'universoanthares') return false;
  const issue = await fetchJson('https://api.github.com/repos/'+REPO+'/issues/1002');
  if (issue?.number !== 1002) return false;
  authCache.set(digest, Date.now()+60000);
  if (authCache.size > 120) authCache.clear();
  return true;
}

export default async function handler(req,res) {
  const action = String(req.query?.action || '');
  if (action === 'health' && req.method === 'GET') {
    try {
      const row = await pool.query('SELECT 1 AS healthy');
      return reply(res,200,{ok:row.rows[0]?.healthy===1,backend:'neon'});
    } catch { return reply(res,503,{ok:false,error:'X_LEDGER_UNAVAILABLE'}); }
  }
  try {
    if (!(await authorize(req))) return reply(res,401,{ok:false,error:'unauthorized'});
    const data = req.body && typeof req.body === 'object' ? req.body : {};
    const key = action === 'post-status' ? String(req.query?.idempotency_key || '') :
      String(data.idempotency_key || '');
    if (!validKey(key)) return reply(res,400,{ok:false,error:'invalid_idempotency_key'});
    const hash = id(key);
    if (action === 'post-status' && req.method === 'GET') {
      const result = await pool.query('SELECT status,post_url FROM anthares_x_submission_ledger WHERE idempotency_sha256=$1 AND account=$2',
        [hash,ACCOUNT]);
      const row = result.rows[0];
      return reply(res,200,{ok:true,status:!row?'NOT_FOUND':row.status==='confirmed'?'CONFIRMED':'UNCERTAIN',
        post_url:row?.status==='confirmed'?row.post_url:null});
    }
    if (action === 'claim-local' && req.method === 'POST') {
      if (data.account !== ACCOUNT) return reply(res,400,{ok:false,error:'account_mismatch'});
      const c = await pool.connect();
      try {
        await c.query('BEGIN');
        await c.query("SELECT pg_advisory_xact_lock(hashtext('anthares-x:lucasyahn:daily'))");
        const quota = await c.query(
          "SELECT count(*)::int AS n FROM anthares_x_submission_ledger WHERE account=$1 AND status IN ('started','confirmed') AND (created_at AT TIME ZONE 'America/Campo_Grande')::date=(now() AT TIME ZONE 'America/Campo_Grande')::date",
          [ACCOUNT]);
        if (Number(quota.rows[0].n) >= 10) {
          await c.query('ROLLBACK');return reply(res,429,{ok:false,error:'daily_limit_10'});
        }
        const inserted = await c.query(
          "INSERT INTO anthares_x_submission_ledger(idempotency_sha256,account,status) VALUES($1,$2,'started') ON CONFLICT DO NOTHING RETURNING idempotency_sha256",
          [hash,ACCOUNT]);
        if (!inserted.rows.length) {
          await c.query('ROLLBACK');return reply(res,409,{ok:false,error:'already_started_reconcile'});
        }
        await c.query('COMMIT');
        return reply(res,200,{ok:true,claimed:true,account:ACCOUNT});
      } catch (error) {
        try { await c.query('ROLLBACK'); } catch {}
        throw error;
      } finally { c.release(); }
    }
    if (action === 'confirm-local' && req.method === 'POST') {
      if (data.account !== ACCOUNT || data.video_verified !== true ||
          data.caption_verified !== true || !validPost(String(data.post_url || '')))
        return reply(res,400,{ok:false,error:'invalid_confirmation_evidence'});
      const updated = await pool.query(
        "UPDATE anthares_x_submission_ledger SET status='confirmed',post_url=$1,confirmed_at=now() WHERE idempotency_sha256=$2 AND account=$3 AND status='started' RETURNING idempotency_sha256",
        [data.post_url,hash,ACCOUNT]);
      if (!updated.rows.length) return reply(res,409,{ok:false,error:'not_started_reconcile'});
      return reply(res,200,{ok:true,confirmed:true,account:ACCOUNT,post_url:data.post_url,video_verified:true});
    }
    return reply(res,404,{ok:false,error:'unknown_action'});
  } catch {
    return reply(res,503,{ok:false,error:'X_LEDGER_UNAVAILABLE'});
  }
}
