# Lease — ARA infrastructure merge validation
STATUS: RUNNING
AREA: queue
DATE: 2026-10-12
RUN: none
JOB: none
COMMIT: 913f73d7a572f6c447135a262e00fa058427fa0d
SUPERSEDES: none
OWNER: Codex ARA infrastructure
LEASE_START_UTC: 2026-10-13T01:10:00Z
LEASE_EXPIRES_UTC: 2026-10-13T01:40:00Z

## Objective
Resolve the PR 105 merge conflict without re-enabling implicit ARA route registration, then validate the durable PostgreSQL queue, concurrency, and route security matrix.

## Baseline and validity
BASELINE_PROVEN: PR 105 implements durable Postgres state and requires the explicit `ara_canary_app` entrypoint; main adds Runtime Mesh registration through `sitecustomize`.
FAILED_AVOIDED: no existing relevant ARA validation run is active for the current head; the canary must not inherit legacy implicit bootstrap routes.
SUCCESS_SIGNAL: merged tree has no conflicts; all three GitHub Actions matrix jobs show the declared unittest and syntax steps succeeding; no secret is committed.
FAILURE_SIGNAL: unresolved merge conflict, test failure, missing Postgres integration evidence, or security test failure.
TEST_VALIDITY: each runner must connect to its own Postgres 16 service and emit the unittest result; a green workflow shell without these signals is not sufficient.
