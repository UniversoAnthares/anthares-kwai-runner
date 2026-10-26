# R07.6 item 13 / CORTES-ISO-07 — independent hosted Linux admission QA
STATUS: PROVEN (QA admission only); PRODUCTION: PENDING
AREA: architecture / tiktok / ISO-07
DATE: 2026-10-25
OWNER: chatgpt-iso07
JOB: ISO07-20261025-RETAKE
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40236871248
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40236871248/job/121300208888
COMMIT: ce7e4caf825e671dba384c66046ec5933e88dabe
SUPERSEDES: test-hub/findings/20261025-iso07-cloud-ci-running.md

## BASELINE_PROVEN
The prior independent Windows test had 10/10 Python tests pass and a fail-closed BLOCKED result from production workflow sources plus sanitized read-only Neon metadata. PR draft #1396 isolates new code to qa/iso07 and findings.

## FAILED_AVOIDED
No production publish, token / secret read, OIDC mint, privileged identity, database write, environment admin mutation, changing any publisher or restart. No claim that sandbox assertions are real DENIED/ALLOWED.

## SUCCESS_SIGNAL (actual)
GitHub Actions self-started by push to exclusive branch, Linux hosted ubuntu-24.04, 2026-10-25T21:44 UTC.
- Workflow CORTES ISO-07 readonly admission QA, run 40236871248, job 121300208888, conclusion SUCCESS.
- Real hosted Python: Ran 10 tests in 0.001s, OK.
- Actual admission CLI against two workflow source files of the repo: ISO07_QA_ASSERT=PASS; ISO07_QA_ONLY=true; ISO07_PRODUCTION_CUTOVER=false; ISO07_GATE_COUNT=23.
- Workflow permissions contents:read, no environment, deployment or OIDC, no secrets inputs and no external publisher invocation in audit job.
- No durable state/secret output persisted as artifact.

## LIMITS
This CI execution only demonstrates fail-closed logic on hosted environment; unlike Windows run it did not inject provider Neon attestation, so 23 rather than 22 unverified gates. Cannot conclude GitHub Environment/secret scope, privileged versus nonprivileged SQL roles, cross-account DENIED, real single-writer or canary publication. Production must remain closed pending provider IAM admission. Tool-level security denials for admin Environment and database role provisioning are binding, and cannot be worked around via alternate controllers.

## ROLLBACK
Close draft PR #1396. GitHub main, Neon production, media queues, external social accounts, schedules and running publishers remain unchanged. CI test triggers only on isolated branch; branch PR is not merged.
