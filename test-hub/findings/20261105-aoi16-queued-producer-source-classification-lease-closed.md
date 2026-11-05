# AOI #16 — classificação de incidentes pré-publicação no QA P0
STATUS: PARTIAL
AREA: qa-p0-incident-taxonomy-queued-and-producer
DATE_UTC: 2026-11-05T01:31:56.889Z
ITEMS: [16]
LEASE: CLOSED
LEASE_OWNER: chatgpt-aoi16-20261105-incident-taxonomy
SUPERSEDES: lease-20261105-aoi16-queued-producer-classification.md
SOURCE_BASE: 5fac1d649fb39df7ca5ec29d6814faecfc8de779
SOURCE_PATCH: 30bc0cf258b2e9528f354007944cf09a55cac1ab
TEST_BASE: 5825b58f7c94559c677889a9dd0dadb2c87622e5
TEST_PATCH: 064f290e5a448d555ae239bcc4f490f1abd2a01b
GITHUB_MAIN_BASE: ac7711074981ddf29e7fbcc82d6456a553c3f8ed
PEER_CHECK: GitLab project 87307248 main diverges from both current GitHub files; no GitLab writes.
COST_ADDED: 0
PRODUCTION_PUBLICATION_CHANGE: NONE

## Diagnóstico
Read-only search in GitHub issues uncovered 56 open QA-P0 tickets with stage `github_actions_queued_stale` and 11 with `P0_DAILY_PRODUCER_ZERO_MASTERS`, all titled `Falha de publicação` with label `publication-failure`. Queued means the job has not begun; producer zero-master stage explicitly notes that the Kwai downstream zero counter is insufficient evidence of failed source production or social publication.

## Correção
`tools/cortes_qa_p0_router.py` now categorizes `github_actions_queued_stale` as an infrastructure queue P0, and `P0_DAILY_PRODUCER_ZERO_MASTERS` / `P0_DAILY_KWAI_DISTRIBUTION_STALLED` as producer/distribution diagnostics. Each retains QA-P0 priority/fingerprint/evidence and an instruction to verify original source before further action. New tickets get label QA-P0 only; actual publisher failure stages retain `QA-P0` + `publication-failure` and original idempotency/no-blind-retry requirements.
Two regression methods added to `tests/test_cortes_qa_p0_router.py`, covering queue and both daily stages.

## Verificação
Isolated, exact function-level Python reproduction was compiled and executed without external calls: 5 PASS, covering queued, producer zero, distribution stalled, genuine publisher failure and prior visibility-only classification. Source branch re-read confirmed exact patch blobs. **Full repository tests and CI not run**, because the QA controller, watchdog and executor workflows are `disabled_manually` under current quota policy.
No social post, CI job, provider deployment, token, Neon row, queue state or shared runtime was altered. Historical metadata correction is separate, permitted only with exact per-issue stage/fingerprint revalidation and independent Test Hub lease; no P0 closures without real causal proof.
Item fixed #16 remains PARTIAL due actual publisher outages still pending.
