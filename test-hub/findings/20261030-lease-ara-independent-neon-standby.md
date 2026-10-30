# ARA independent compute reserve
STATUS: RUNNING
AREA: cloudflare-control / ara-oauth
DATE: 2026-10-30
OWNER: Codex ara-independent-neon-standby-20261030
COMMIT: baseline ff6d7bf5e327e1e512c797e2398dfe9ca336ee52
SUPERSEDES: none
LEASE: 30 minutes from commit timestamp; new independent standby and gateway transport only.
GOVERNANCE: 84905aefc5589d17
## BASELINE_PROVEN
Both connectors require reauthentication; owner callback returns owner_control_unavailable. Vercel team quota pause confirmed by email (108% CPU), independent request HTTP402 DEPLOYMENT_DISABLED. Main replay table PRIMARY KEY(kind,issuer,jti) verified. GitLab gateway blob ba7450c9cb69b37c58e95003e67209a0fc0940ff matches GitHub baseline. Relevant Oct28 lease expired and superseded; no causally relevant running GitHub deployment.
## FAILED_AVOIDED
Do not repeat suspended Vercel jobs, provision paid resources, change owner GitHub identity/keys, use independent replay ledgers or switch after 401/403. Preserve Vercel transports first. No PC staging/runtime; sources and CI on GitHub, remote unit execution on Hostinger. Existing DO quota/write amplification avoids DO reactivation.
## SUCCESS_SIGNAL
Remote safety tests pass; independent compute installed; same Neon tables/atomic replay across routes; gateway health control_ready with Vercel paused; anonymous 401. Owner reconnect remains NOT_TESTED until real user authorization completes.
## FAILURE_SIGNAL
Split replay acceptance, unsolicited job duplication, HTTP401/403 bypass, deployment rejection, missing secret or failed health gate.
## TEST_VALIDITY
Use exact immutable branch SHA, same SQL schema. Separate source/unit/deployed/end-user evidence. Unknown writes require reconciliation. Close lease append-only.
