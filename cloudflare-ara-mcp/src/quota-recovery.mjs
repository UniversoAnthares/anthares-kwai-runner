// Explicit recovery epoch. Never share a replay ledger between independent
// authorities, and never let the old gateway accept recovery tokens on rollback.
export function quotaRecoveryEnabled(env) {
  const mode=String(env.ARA_QUOTA_RECOVERY_MODE||"");
  if(!mode)return false;
  if(mode!=="queue-v1")throw new Error("quota_recovery_mode_invalid");
  return true;
}
export function tokenMacInput(env,body) {
  return quotaRecoveryEnabled(env)?"ara-oauth-quota-recovery-v1:"+body:body;
}
const MAX_AGE=31*24*3600;
export function consumeReplayClaim(sql,kind,jti,exp,now=Math.floor(Date.now()/1000)) {
  if(!/^(oauth_owner_callback|oauth_pending|authorization_code|refresh_token)$/.test(kind)
      || !/^[A-Za-z0-9_-]{12,128}$/.test(jti)
      || !Number.isSafeInteger(exp) || exp<=now || exp>now+MAX_AGE)return false;
  sql.exec("CREATE TABLE IF NOT EXISTS recovery_oauth_claims (kind TEXT NOT NULL, jti TEXT NOT NULL, expires INTEGER NOT NULL, PRIMARY KEY(kind,jti))");
  sql.exec("CREATE INDEX IF NOT EXISTS recovery_oauth_expiry ON recovery_oauth_claims(expires)");
  sql.exec("DELETE FROM recovery_oauth_claims WHERE expires <= ?",now);
  // A single atomic statement reserves the claim before token issuance.
  return sql.exec("INSERT INTO recovery_oauth_claims(kind,jti,expires) VALUES(?,?,?) ON CONFLICT(kind,jti) DO NOTHING RETURNING jti",kind,jti,exp).toArray().length===1;
}
export async function consumeRecoveryReplay(env,kind,jti,exp) {
  try {
    if(!quotaRecoveryEnabled(env)||!env.ARA_LIVE_CHANNEL)throw new Error("binding_missing");
    const stub=env.ARA_LIVE_CHANNEL.get(env.ARA_LIVE_CHANNEL.idFromName("ARA-OAUTH-QUOTA-RECOVERY-V1"));
    const result=await stub.consumeQuotaReplay(kind,jti,exp);
    if(typeof result!=="boolean")throw new Error("invalid_replay_receipt");
    return result;
  } catch {
    // No fallback to a different ledger; unavailable is not an unused claim.
    throw new Error("oauth_replay_store_unavailable");
  }
}
export function recoveryReady(env,ownerConfigured) {
  return Boolean(ownerConfigured && env.ARA_LIVE_CHANNEL &&
    String(env.ANTHARES_GITHUB_TOKEN||"").trim());
}
