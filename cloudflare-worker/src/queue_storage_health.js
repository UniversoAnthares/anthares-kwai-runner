// A constructor must not rewrite every legacy/default job on each cold start.
export function migrateLegacyTargetAccounts(sql) {
  for (const raw of sql.exec('SELECT id,payload,account_id FROM jobs').toArray()) {
    if (raw.account_id && raw.account_id !== 'default') continue;
    let payload = {};
    try { payload = JSON.parse(raw.payload || '{}'); } catch {}
    const account = String(payload.account_id || payload.expected_account_id || payload.account || 'default')
      .trim().replace(/^@/, '').toLowerCase() || 'default';
    if (account !== (raw.account_id || 'default')) {
      sql.exec('UPDATE jobs SET account_id=? WHERE id=?', account, raw.id);
    }
  }
}

export function storageQuotaResponse(error) {
  if (!/Exceeded allowed rows (written|read) in Durable Objects free tier/i.test(String(error?.message || error))) return null;
  return Response.json({ok: false, error: 'queue_storage_quota_exhausted',
    publication_allowed: false, retry_after_seconds: 900},
    {status: 503, headers: {'Cache-Control': 'no-store', 'Retry-After': '900'}});
}
