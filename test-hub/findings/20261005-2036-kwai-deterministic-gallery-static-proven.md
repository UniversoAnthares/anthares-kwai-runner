# Kwai gallery selection now fails closed on unidentified media
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394638955
JOB: 112047582710
COMMIT: 142f30e97b8a3c41459ecb1cdc415352846dc5ec
SUPERSEDES: test-hub/findings/20261005-2034-kwai-deterministic-gallery-selection-running.md

BASELINE_PROVEN: test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md.
FAILED_AVOIDED: direct ACTION_SEND remains NOT_TESTED after run 37392541208 failed before MAIN; generic first-thumbnail selection was removed; invalid run 37394573030 was repaired only at its literal-newline harness defect.
SUCCESS_SIGNAL: deterministic gallery markers and absence of candidates[0], followed by KWAI_STARTED_BEFORE_COMMIT_STATIC_OK and KWAI_PUBLISH_SAFETY_STATIC_OK.
FAILURE_SIGNAL: unidentified generic thumbnail remains selectable or lifecycle ordering regresses.
TEST_VALIDITY: source/static proof only; no Android/login/publication claim.

## Resultado
PROVEN in snapshot. prepare() now requires exactly one clickable gallery node whose accessible label contains the exact media filename, filename stem, SHA-256 prefix, or normalized job identity. Zero or multiple matches return FAILED_SAFE before READY_TO_PUBLISH and before central started. The ready proof now also carries media_sha256 and commit verifies it.

## Evidência decisiva
Run 37394638955 / job 112047582710 completed success after Python compile, deterministic-gallery guard checks, absence of candidates[0], and emitted KWAI_STARTED_BEFORE_COMMIT_STATIC_OK plus KWAI_PUBLISH_SAFETY_STATIC_OK.

## Consequência
Preserve fail-closed selection. Runtime acceptance still requires real accessible UI identity or the separately tested direct ACTION_SEND path. Static proof must not be called real media-selection proof.
