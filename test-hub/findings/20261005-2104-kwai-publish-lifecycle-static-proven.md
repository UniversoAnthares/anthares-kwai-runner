# Kwai publish lifecycle started-before-commit hardening is statically proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37391014212
JOB: 112035828277
COMMIT: 12590ca86bf3db2b38e358fc7813e783521492fd
SUPERSEDES: test-hub/findings/20261005-2103-kwai-publish-lifecycle-validation-running.md

BASELINE_PROVEN: queue fail-closed confirmation invariants and prior Kwai media staging safety.
FAILED_AVOIDED: no real Publish action; malformed workflow commit 071c53e not reused; generic recency markers removed from verifier success; stale control-plane version is rejected by queue adapter.
SUCCESS_SIGNAL: `KWAI_STARTED_BEFORE_COMMIT_STATIC_OK` and `KWAI_PUBLISH_SAFETY_STATIC_OK` after syntax/compile/guard/order checks.
FAILURE_SIGNAL: any missing invariant or ordering failure.
TEST_VALIDITY: source/static proof only; authentication and real publication remain outside this result.

## Resultado
PROVEN in snapshot. `kwai_publish_video.py` now has explicit prepare/commit phases and emits READY_TO_PUBLISH before PUBLISH_REQUESTED. `kwai_publish.sh` orders prepare -> central started -> commit -> specific verifier -> central complete -> CONFIRMED. `kwai_queue_state.sh` uses GitHub OIDC, rejects a non-v12/stale controller, requires publication_started acknowledgement, and validates complete/fail acknowledgements. `kwai_verify_publication.py` requires expected account, stable Profile, intended title, job/media identity and emits specific confirmation evidence; generic `published/just now/agora` cannot close the ledger.

## Evidência decisiva
Run 37391014212 / job 112035828277 completed success. The decisive log emitted `KWAI_STARTED_BEFORE_COMMIT_STATIC_OK` followed by `KWAI_PUBLISH_SAFETY_STATIC_OK` after all assertions.

## Consequência
Preserve this ordering. Real publication remains quarantined until kwai-login proves READY/account identity and the v12 Worker is deployed. Next independent publication-layer test is direct ACTION_SEND media ingress and must stop before Publish.
