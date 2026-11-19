# LinkedIn company fixed-code authorization failure reason diagnosis

AREA: LinkedIn-company reason string only. STATE: RUNNING; START 2026-11-19T04:09:31.195Z; EXPIRES 2026-11-19T04:38:31.195Z.
BASELINE: workflow 44455474304 reached real script after passing tests and returned ConfigRequired, class-only output. HEAD 5f96a9e1288139b9b1c7ec3e7baf26701790bb2c.
FAILED_AVOIDED: never expose bearer tokens/HTTP bodies, never assume organization permissions, never bypass OAuth, never mutate Neon queue for this fix.
SUCCESS_SIGNAL: bounded reason code from predefined constants in live log, QA confirms unknown text redacted.
FAILURE_SIGNAL: tests fail, foreign errors appear, or main HEAD drifts.
TEST_VALIDITY: branch only prior to QA, GitLab mirror stale/missing these targets, current production LinkedIn status still unverified.
