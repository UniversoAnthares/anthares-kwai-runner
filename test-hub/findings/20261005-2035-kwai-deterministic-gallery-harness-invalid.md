# Kwai deterministic gallery validation invalid due literal newline serialization
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394573030
JOB: 112047368377
COMMIT: d8cf15a1eb69a7fa03cd4f567b464352a12bbe4a
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md remains preserved conceptually; deterministic gallery hardening test was source/static only.
FAILED_AVOIDED: no Android or Publish action occurred.
SUCCESS_SIGNAL: deterministic gallery markers plus absence of candidates[0], followed by prior lifecycle static signals.
FAILURE_SIGNAL: a syntactically valid source violates any declared invariant.
TEST_VALIDITY: Python compilation must pass before any invariant is evaluated.

## Resultado
INVALID/NOT_TESTED. The run stopped at py_compile because the source contained a literal backslash-n sequence between JOB_ID and MEDIA_SHA. No deterministic-selection assertion ran.

## Evidência decisiva
Job 112047368377: SyntaxError at kwai_publish_video.py line 7, pointing at the literal \\nMEDIA_SHA sequence.

## Consequência
Repair only the serialization/newline defect, re-read the hub, then rerun the same static hypothesis. This run does not count against deterministic selection.
