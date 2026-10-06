# QA acceptance/hub consistency 5-way
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: hub protocol is authoritative and several old RUNNING findings coexist with completed runs.
FAILED_AVOIDED: read-only audit only; no serialized mutation area.
SUCCESS_SIGNAL: each probe emits an explicit QA result for stale RUNNING, v15/v16 drift, false production claims, acceptance evidence, or active lease consistency.
FAILURE_SIGNAL: a contradiction is found and reported fail-closed.
TEST_VALIDITY: repository checkout and hub files must be readable.

## Objetivo
Audit five independent architecture/acceptance consistency dimensions while execution agents continue.