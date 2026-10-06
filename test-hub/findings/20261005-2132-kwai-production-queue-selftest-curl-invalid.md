# Kwai production queue OIDC self-test invalidated by incompatible curl flags before POST
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37392227134
JOB: 112039748806
COMMIT: bf1d232aa7e9ee364477dab5ef1f3519148794a4
SUPERSEDES: test-hub/findings/20261005-2127-kwai-production-queue-oidc-selftest-running.md

BASELINE_PROVEN: production v12 health/queue bound and exact `kwai-real-publish.yml` OIDC identity setup.
FAILED_AVOIDED: real publication guard was skipped; no real Kwai job/media path executed; no conclusion about OIDC authorization or queue lifecycle is inferred from the harness failure.
SUCCESS_SIGNAL: not reached.
FAILURE_SIGNAL: not reached.
TEST_VALIDITY: INVALID/NOT_TESTED. The run positively validated public health as v12 with queue_bound=true and pc_fallback=false and successfully reached the OIDC-token acquisition lines. The subsequent curl command failed locally with `You must select either --fail or --fail-with-body, not both` because `--fail-with-body` was combined with `-f` through `-fsS`. The POST `/queue-self-test` was not sent.

## Resultado
This is a command-line harness error before the production queue hypothesis. The publication guard job was skipped exactly as designed. The causal fix is to keep `--fail-with-body` and remove `-f`, e.g. use `curl --fail-with-body -sS`.

## Consequência
Repeat the isolated self-test once with only the curl flag corrected. Preserve the exact workflow identity, v12 health gate, isolated Worker self-test endpoint and required invariant list. Do not enqueue or lease a real Kwai job.
