# Kwai authentication-first workflow and two acceptance runs
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947415466
JOB: pending
COMMIT: be52eb792817262e50ab3ee0ea651f6e7349eee9
SUPERSEDES: none

## Objective
Move network diagnostics behind interactive login, publish remote tunnel link earlier, cap interactive login to 12 minutes and total job to 25 minutes. Do not modify login-agent scripts or use user's PC.

## Baseline and validity
BASELINE_PROVEN: cached Android Kwai app launch run 37940202375. Source shell syntax fix e3c70d1.
FAILED_AVOIDED: previous unbounded interactive waiting and collecting diagnostics before login.
SUCCESS_SIGNAL: verified expected account identity, encrypted session and independent restore; mere job completion insufficient.
FAILURE_SIGNAL: timeout, missing UI, mismatch, no session.
TEST_VALIDITY: require real Android login evidence; do not claim authentication from tunnel creation.

## Executions
First: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947415466 (push be52eb7, in progress at observation).
Second: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947449351 (push 03cbacb, queued at observation).

## Limitation
Android boot and vault preparation remain prerequisites for app-based login. This change prioritizes login over diagnostics, but does not make Android authentication possible before Android startup.
