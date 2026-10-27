# Harness → GitHub CI quota fallback — bounded implementation and QA
STATUS: IMPLEMENTED_CONTRACT_TESTED_DEPLOYMENT_PENDING
AREA: github-ci/harness-readonly-fallback
DATE: 2026-10-27
OWNER: ChatGPT
SUPERSEDES: none
BASELINE_PROVEN: Genuine watcher run 40573476128 success; API authenticated to owned Harness execution #908; 12 observed owned statuses with NO_STRUCTURED_QUOTA. Existing Vercel provider-cancel claim/report source and shared Neon CAS; latest production controller deployment did not yet prove current source.
FAILED_AVOIDED: No fake quota, no real AbortAll without provider signal, no side-effect-bearing workflow successor, no Bitrise executor promotion, no duplicate submission, no stale GitHub source SHA checkout, no re-dispatch after timeout.
SUCCESS_SIGNAL: CI test run 40576068709; 41 Python unittest passes, HARNESS_NEON_CONTROLLER_CONTRACT=PASS CASES=11, HARNESS_FALLBACK_OIDC_NEON_FENCE=PASS CASES=8, HARNESS_FENCED_FAILOVER_CONTRACTS=PASS. Fenced Harness cancel then GitHub dispatch only after terminal + signed report + exact pipeline blob; successor independently acquires OIDC/Neon single-winner lock; idempotent terminal success receipt.
FAILURE_SIGNAL: Vercel deployment rejected or unpublished; fallback variable remains disabled, and full operational fallback is NOT claimed. Actual provider quota event remains unobserved. An uncertain submission must remain reserved and never be retried.
TEST_VALIDITY: GitHub hosted runner tests with fake JWT, fake Neon, fake HTTP; no production mutations, secrets, publication, or provider cancellation.
FILES: tools/ci_quota_harness_watcher.py, tools/harness_fallback_receipt.py, deploy/anthares-ci-quota-controller/api/provider-cancel.mjs, deploy/anthares-ci-quota-controller/api/harness-fallback-verify.mjs, .github/workflows/harness-quota-rescue.yml, .github/workflows/ci-quota-external-cancel.yml, tests/test_ci_quota_harness_watcher.py, tests/test_ci_quota_harness_controller.mjs, tests/test_harness_fallback_controller.mjs.
