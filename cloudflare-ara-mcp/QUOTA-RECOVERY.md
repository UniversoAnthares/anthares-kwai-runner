# ARA quota recovery — independent execution and OAuth

Incident 2026-11-26: Vercel HTTP 402; Neon HTTP 402; standby HTTP 503. Windows agent remains operational. Private GitHub queue issue UniversoAnthares/anthares-ara-queue#330 returned a successful agent_health receipt and was closed. Both preexisting Cloudflare DO control reserve endpoints passed authenticated device auth checks, but reported disconnected. No agent restart or control-ledger reassignment has been performed.

## Recovery mode

This change is inactive unless the gateway deployment explicitly sets ARA_QUOTA_RECOVERY_MODE=queue-v1. Legacy default behavior is preserved. In recovery mode the authenticated gateway dispatches to the already implemented private GitHub queue. OAuth uses a separate Durable Object name in the existing SQLite-backed ARA_LIVE_CHANNEL binding. Recovery tokens have a domain-separated HMAC input, so legacy and recovery tokens cannot be exchanged or replayed against independent ledgers. No credential is changed or copied. Existing OAuth connections must be reauthorized after activating this mode; recovery connections require reauthorization after rollback. The existing GitHub owner identity, PKCE, client restrictions, scope checks, anonymous denial and one-time claims remain mandatory. Failure to access the replay store fails closed.

Public /health is deliberately configuration-only in this mode: device_connected=null and device_status_verified=false. It never queues a job. An authenticated capabilities or session_status call is required to prove a live agent.

## Release procedure

1. Review the isolated PR; require syntax and regression checks to pass, including domain separation, SQL one-time claims, replay failure 503, replay rejection 400 and anonymous 401. Do not declare production based on tests alone.
2. Check for unresolved existing mutations in the active transport. If outcome is unknown, reconcile before using the private queue for the same action. No new command may be retried through a second route following an ambiguous result.
3. Confirm Cloudflare DO quota/availability and existing private-queue credential availability without logging any secret. Confirm one Windows executor; the private queue does not require restarting it.
4. Follow the existing reviewed-SHA and incident deployment policy. Explicitly approve activation and its OAuth reconnection consequence. The standard Neon readiness gate cannot validate a Neon-independent recovery mode; a separate approved release gate must require a fresh authenticated queue canary and DO replay canary. Do not bypass existing release approval or use the legacy gate as proof of recovery.
5. Deploy with the explicit recovery flag using the approved release mechanism; verify anonymous 401, health mode/flags, fresh owner authorization and authenticated agent_health/capabilities. For rollback explicitly remove/clear the recovery flag and use an approved SHA; do not leave the flag in retained Worker variables.
6. Keep token values, passwords, OTPs and sensitive content out of private queue payloads/receipts. Bot token handling requires the approved secret storage path. Do not use the queue to export Chrome cookies or Telegram sessions.

No new paid resource or storage provider is required by this proposed mode. Production activation and live Cloudflare replay validation are pending. The GitHub queue proof is already real; the new OAuth path is not yet proven live.
