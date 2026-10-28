# Item fixo 9 — rota externa de alertas QA P0, prova real em andamento
STATUS: RUNNING
AREA: architecture/qa-p0-supervision-alerts
DATE: 2026-10-28
RUN: pending push workflow .github/workflows/cortes-qa-p0-publication-watchdog.yml
JOB: pending
COMMIT: 257c2fb51154236b6ab85158b71cda3f2d81a9c2
SUPERSEDES: none
OWNER: ChatGPT AOI item 9; feature/qa-p0-hosted-alert-redundancy-20261028
LEASE: limited to this QA watchdog and findings; release after one scoped GitHub-hosted proof.

BASELINE_PROVEN: GitHub P0 watchdog run 40775681413 on dedicated runner success; incident #1810 contains sanitized source-run evidence and P0 fingerprint; QA executor run 40774789486 appended diagnostic. Forgejo independent nonpublishing QA run 243 success and 12h schedule registered, not an alert delivery.
FAILED_AVOIDED: migration of Windows-only SSH WordPress credentials and source-code execution on Forgejo; no Codeberg retry, social repost, new cron/service or synthetic media.
SUCCESS_SIGNAL: existing GitHub watchdog runs hosted ubuntu-24.04 cloud-alert-redundancy job; log records QA_P0_CLOUD_MONITOR=PASS and QA_P0_CLOUD_DELIVERY_READBACK=PASS with existing/new actual P0 issue and source-run ID; newly created issues require GitHub GET readback. Preserves Windows source-specific WordPress QA and GitHub incident controller.
FAILURE_SIGNAL: hosted job cannot allocate, GitHub Issues API denies write/readback, no matching real run, ambiguous alert delivery, or false duplicate.
TEST_VALIDITY: actual workflow push on main from approved PR, cloud-hosted Actions runner identified in job receipt; one run only, no fabricated P0 failure. Success conclusion alone is insufficient. If there are no observed real failures, idle marker is valid but delivery verification remains pending.
