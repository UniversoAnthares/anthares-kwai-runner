# OAuth grant backend outage classification deployed
STATUS: PARTIAL — FAILURE MODE FIXED; REPORTED CHATGPT PERSISTENCE NOT CONFIRMED
AREA: cloudflare-control / ara-oauth
DATE: 2026-10-30
OWNER: codex ara-oauth-refresh-disconnect-20261030
GOVERNANCE: 84905aefc5589d17
COMMIT: 7d9dde05594f58530d9ac1f6eaa9bd66431f98eb
SUPERSEDES: test-hub/findings/20261030-lease-ara-refresh-backend-errors.md
LEASE: CLOSED

## Confirmed failure mode and change
User confirms accounts request reconnect after page reload, not only device offline. Existing consumeViaControl catches replay backend failures and returns false, so refresh and code exchanges return invalid_grant400. PR1979 preserves failures as a distinct internal error and returns temporary503 with Retry-After5 and existing no-store. Atomic claims, replay400, PKCE, scopes and all credentials unchanged. Existing Vercel route, independent standby and owner cookie isolation retained.

## Evidence
Validation run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41067237783:30 tests,30 pass,0 fail. Both separate synthetic ChatGPT client IDs receive503 on three-controller outage, then successful retry of unused token, rotated credentials, authenticated ping and400 on reuse. Code exchange outage likewise preserves one-use/PKCE behavior.
First run41067135752 failed only because new header duplicated shared no-store; removed redundant header and reran causally. Nothing from failed version deployed.
Canonical deployment https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41067344555 SUCCESS, version883973f7-ebd3-4924-b3b1-69f818e4cf37; ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS and ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS. Independent public curl health200/control_readytrue/owneridentitymode verified. Python urllib public probe403 is transport-specific and not evidence of OAuth invalidation; no protection changed.
Before deployment both actual connector capabilities returned authenticated ara.read/ara.write but device_connected=false. Read-only Neon45min snapshot showed11 refresh claims, latest13:52:33Z, five code claims latest13:41:43Z. These are successful consume counts, not failed-refresh telemetry or proof of browser persistence.
Sanitized bounded owned Cloudflare tails closed: first two MCP200 events, no OAuth400 observed; second capture empty. No secrets or full callback URLs recorded.

## Limits and next acceptance
Reported browser disconnection root cause is NOT confirmed by the above. A temporary-backend failure is a verified code defect and plausible cause, not a proven explanation of this exact event. Existing access-token success does not prove refresh persistence. Actual affected browser reconnect/reload and refresh acceptance remain open. Do not request repeated blind reconnects, relax refresh replay, rotate signing keys, uninstall plugins or mark item6 complete.
Windows transport remains independently offline; no queue job, duplicate agent, supervisor mutation, production Vercel change, AVS item12 POST or fixed13 update.
Rollback through canonical reviewed source/workflow; keep protected secrets and reserve unchanged.
