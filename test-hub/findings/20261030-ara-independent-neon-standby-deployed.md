# ARA independent compute reserve deployed; owner reconnection pending
STATUS: PARTIAL — RESERVE DEPLOYED AND VERIFIED; OWNER RECONNECTION AND DEVICE TRANSPORT PENDING
AREA: cloudflare-control / ara-oauth
DATE: 2026-10-30
OWNER: Codex ara-independent-neon-standby-20261030
COMMIT: ca74e9eb5af859e4400f2b1ed57323ab23e31593
SUPERSEDES: test-hub/findings/20261030-lease-ara-independent-neon-standby.md
LEASE: CLOSED
GOVERNANCE: 84905aefc5589d17

## BASELINE_PROVEN
Vercel team quota pause and HTTP402 DEPLOYMENT_DISABLED affected both Vercel aliases. Owner callback depended on that control for single-use claims and returned owner_control_unavailable. Both connectors required reauthentication.

## CHANGE
PR #1940 merged normally. Vercel remains first transport, with independent Cloudflare worker anthares-ara-neon-standby added through an authenticated internal service binding. Both compute paths use the SAME existing Neon replay and job tables; no divergent replay ledger or second queue consumer. Existing ara_mcp_reserve_runtime role provisioned through secret manager, no key rotation or permission expansion. Existing public verifier pinned, private/OAuth secrets retained in their current Worker. Free-plan defaults, no paid feature or local staging/runtime installed.

Sequential failover skips aliases sharing confirmed exhausted Vercel quota. HTTP401/403 stop; ambiguous non-idempotent writes return RECONCILE_REQUIRED. Replay consume retains the exact claim and atomic INSERT ON CONFLICT uniqueness across compute routes. No destructive DB migration or cleanup.

## EVIDENCE
- Remote validation run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40996189989: 24 tests, 24 pass, 0 fail; ARA_SHARED_LEDGER_FALLBACK_HEALTH_AND_ANON_DENIAL=PASS.
- Standby deployment run 40996091942; version d916a3a5-ab4b-45cd-baf6-0e53615ec1a7. Secret manager installed restricted database credential without displaying or staging it; one-shot helper closed with exit0, no local work files.
- Final canonical main deployment https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40996377835 SUCCESS, version 7b1995c4-5263-4b0f-9379-b40bfb4848e4, ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS, ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS.
- Public standby health ok=true, state=shared-neon, vercel_preserved=true.
- Public gateway health ok=true, control_ready=true, control_error=null, oauth_owner_code_mode=github_owner_identity; anonymous gateway MCP and unsigned replay consume HTTP401.
- Read-only Neon verification found 4 new mcp_signature claims after03:14Z under the existing reserve issuer, proving signed standby requests persist to the shared authority. No claim contents recorded.
- Initial failed deployment was free-plan unsupported custom CPU configuration (100328); removed optional setting rather than purchasing. Old 2-route test fixture updated to explicitly fail all3 routes. A public Worker-to-Worker 404 was resolved with the supported internal service binding, without changing protections.

## LIMITS
- Owner reconnect is NOT_TESTED; asynchronous request delivered only after successful external verification.
- device_connected=false. Existing Windows selector still contains only the two unavailable Vercel endpoints. No protected local supervisor/service changed or duplicate agent started. Runtime transport recovery needs a separate coordinated installation through its authorized control.
- Neon remains a common data dependency; this is compute/quota redundancy, not independent database HA.
- No production Vercel deployment/config change, no AVS item12 POST and no claim that the13 fixed items are updated.

## RECOVERY
Keep Vercel origins and shared SQL ledger. Restore gateway prior reviewed source only via canonical workflow if needed; retain standby and its existing encrypted secret. Public verifier rotation requires coordinated config update. No repeated quota job is left running.
