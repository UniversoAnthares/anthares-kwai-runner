# Production queue self-test exposed failure counter reset bug
STATUS: FAILED
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37392715203
JOB: 112041336473
COMMIT: e214939447c9dec65889a7615dcea29475474ab8
SUPERSEDES: test-hub/findings/20261005-2138-queue-selftest-error-capture-running.md

BASELINE_PROVEN: production v12, exact `kwai-real-publish.yml` GitHub OIDC identity, isolated `__selftest__` queue namespace.
FAILED_AVOIDED: no real Kwai job/media/publication path; diagnostic captured server JSON instead of repeating blind acceptance.
SUCCESS_SIGNAL: explicit server error recovered.
FAILURE_SIGNAL: response body/status unavailable.
TEST_VALIDITY: VALID. Public health confirmed v12/queue_bound/pc_fallback=false, OIDC transport succeeded, `/queue-self-test` returned HTTP 500 with JSON `{"ok":false,"error":"failure_counter_reset_failed"}`.

## Resultado
The Worker's self-test reached the failure-counter circuit-breaker invariant and found a real state bug. `recordFailure()` sets `disabled_until` after three consecutive failures. `recordSuccess()` currently spreads the prior executor state and resets `consecutive_failures`/`failures` to zero while leaving `disabled_until` intact. The self-test correctly rejects that state as `failure_counter_reset_failed`.

## Consequência
Patch `recordSuccess()` so a confirmed success clears `disabled_until` together with both failure counters. Do not rerun acceptance until this causal controller change is applied, statically validated, version-bumped and deployed. Preserve all other queue invariants.
