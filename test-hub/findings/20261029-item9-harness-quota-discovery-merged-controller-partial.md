# Item fixo 9 — cancelamento por cota: descoberta Harness ampliada; gate produtivo parcial
STATUS: PARTIAL
AREA: github-ci/quota-provider-cancel/harness-discovery
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40994588875
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40994588875/job/123864645969
COMMIT: 4ea2aa25dbf108542d369eaf62ecb2b0d095e2bd
SUPERSEDES: 20261029-item9-harness-quota-discovery-running.md

## Verified contract and live operations
- PR #1937 merged on main. Harness watcher enumerates up to 16 recent main commits instead of six, retaining exact owner/context, SHA, structured provider quota, Neon claim, terminal check, and fail-closed nonpublishing rescue.
- GitHub CI run 40994588875 / job 123864645969: SUCCESS; 45 Python tests PASS; new test `test_recent_discovery_includes_seventh_commit` PASS; `HARNESS_FENCED_FAILOVER_CONTRACTS=PASS`. Production blob readback confirms `per_page=16`.
- Real GitHub controlled cancellation: source run 40502470893 CANCELLED, independent allowlisted listener 40502486145 SUCCESS. It was a controlled no-side-effect fixture, not a natural quota event.
- Previously observed real GitLab CI quota exhaustion was terminal before any external cancel request; independently executed GitHub successor 40510154187 SUCCESS. GitLab latest pipeline 3006844775 on 2026-10-30T02:57:59Z was FAILED with six `ci_quota_exceeded` jobs and zero active: no remote active job remained to cancel.
- GitHub scheduled external watcher 40992530819 / job 123858071629 SUCCESS at 02:35Z with `HARNESS_API_AUTH_READONLY=VERIFIED_OWNED_EXECUTION_908`, Harness watcher enabled, `HARNESS_QUOTA=NO_RECENT_OWNED_RUNS`, verified AppVeyor and Bitrise API identity, `QUOTA_EVENTS=NO_STRUCTURED_EVENTS`.
- **LIVE BLOCKER:** after merge, push-triggered external watcher 40994661753 / job 123864882215 FAILED in the controller OIDC/Neon read-only acceptance step at 02:57Z: `CONTROLLER_ACCEPTANCE=Unexpected token 'P', "Payment re"... is not valid JSON`. The Vercel project API still reports production deployment dpl_GpybXDXSumX4MBMYAjaV34SanXoc as READY, but the acceptance HTTP response was not usable JSON. This is a provider access/billing response, not a proven code-test regression. No second synthetic job dispatched. Runtime error aggregate had no relevant function errors; hobby runtime log API could not provide logs for window.

## Remaining explicit acceptance
- Restore genuine HTTP 200 JSON health/ledger=READY/mode=ENABLED on the existing authorized controller **without paid-plan upgrade, quota evasion, duplicate dispatch or lowered authentication**; verify OIDC provider-cancel acceptance. Reconcile current HTTP response before touching execution state.
- Observe an independently proven, owned, provider-structured quota incident in a still-active remote job; request cancel once, verify terminal remote state, fence old lease, and confirm durable Neon receipt. When already terminal, classify terminal without asserting live cancellation.
- Safe fallback only after terminal plus NOT_APPLIED side-effect reconciliation and independently eligible successor; GitLab real terminal-to-GitHub nonpublishing handoff already separately proven. Other external providers remain unproven for natural quota cancellation.

TEST_VALIDITY: actual CI ran; no quota incident fabricated, no publication or financial changes, no provider cancellation attempted against unrelated executions.
