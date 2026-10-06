# Production queue self-test reached Worker through Kwai OIDC and returned server-side HTTP 500
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37392518704
JOB: 112040689322
COMMIT: a5dc1a8df2642dfd387bc8aefbc09168f36718e9
SUPERSEDES: test-hub/findings/20261005-2134-kwai-production-queue-oidc-selftest-retry-running.md

BASELINE_PROVEN: production v12 health and queue binding; exact kwai-real-publish GitHub OIDC workflow identity.
FAILED_AVOIDED: publication guard stayed skipped and no real Kwai jobs/media path executed. The earlier incompatible curl flags were fixed.
SUCCESS_SIGNAL: not achieved; acceptance self-test returned server-side failure.
FAILURE_SIGNAL: HTTP error from `/queue-self-test` after valid v12 health and OIDC path.
TEST_VALIDITY: VALID up to the Worker self-test execution boundary. Public health returned v12, queue_bound=true, pc_fallback=false; GitHub OIDC token acquisition completed; POST `/queue-self-test` reached the production Worker and returned HTTP 500. The current harness suppressed the JSON error body because curl exited during command substitution.

## Resultado
The production queue acceptance hypothesis is now PARTIAL/FAILED at the Worker's selfTest implementation rather than at authentication or transport. The exact internal invariant/error remains unknown because the response body was not printed when curl exited 22.

## Consequência
Do not rerun the acceptance test unchanged. Next test is diagnostic-only: capture HTTP status and JSON body from `/queue-self-test` without treating HTTP 500 as a curl transport failure. Its success criterion is recovery of the explicit server `error` string. Use that error to make the causal controller/selfTest correction before another acceptance run.
