# Kwai UNCERTAIN reconciler executable behavior proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37397424741
JOB: 112056609767
COMMIT: 2126db586ea750f6a8fe092e0099b028b70c94a4
SUPERSEDES: test-hub/findings/20261005-2110-lease-kwai-reconcile-executable-tests.md

## Resultado
Executable fixtures prove the observation-only UNCERTAIN reconciler behavior, not only source shape.

## Casos provados
- verifier success + specific evidence -> central reconcile exactly once -> CONFIRMED;
- verifier nonzero/loading -> UNCERTAIN, zero reconcile calls;
- missing evidence -> UNCERTAIN, zero reconcile calls;
- missing specific proof -> UNCERTAIN, zero reconcile calls;
- central reconcile rejection -> UNCERTAIN, exactly one reconcile attempt;
- reconciler contains no publisher/commit/Publish invocation.

## Evidência
Run emitted KWAI_UNCERTAIN_RECONCILE_EXECUTABLE_OK while v16 fencing, deterministic gallery, started-before-commit and publication safety checks also remained green.

## Consequência
The ambiguous-outcome recovery path is behaviorally fail-closed. Real runtime remains gated by independent authenticated Android Agent readiness.
