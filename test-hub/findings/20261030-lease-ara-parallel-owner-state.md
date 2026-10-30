# Parallel connector owner authorization
STATUS: RUNNING
AREA: cloudflare-control / ara-oauth
DATE: 2026-10-30
OWNER: codex ara-owner-cookie-20261030
LEASE: expires30min after commit; owner cookie module and regression tests only
GOVERNANCE: 84905aefc5589d17
SUPERSEDES: none
## BASELINE_PROVEN
PR1940 and canonical40996377835 deployed shared-ledger independent compute. One real connector now authenticates with ara.read/ara.write; other screenshot owner_state_invalid. Device remains offline, zero queued/leased/uncertain. Single fixed __Host-ara-owner browser cookie is shared by both connector flows.
## FAILED_AVOIDED
Do not change active connector, clear all cookies, reuse screenshot codes, weaken nonce/PKCE/identity/replay verification or rotate keys. No PC source staging. Test-only baseline reproduction before causal fix. Previous deployment lease CLOSED.
## SUCCESS_SIGNAL
Browser cookie-jar regression reproduces lost authorization on baseline; per-transaction cookie fix accepts reverse completion order and still rejects forged/missing/expired cookies and replay. Remote tests+canonical deploy pass; real second owner consent separately pending.
## FAILURE_SIGNAL
Identity bypass, broken existing OAuth contracts, production unhealthy or competing deployment.
## TEST_VALIDITY
Exact branch SHA; isolated tests execute on GitHub. No browser tokens or codes used. No security guard bypass.
