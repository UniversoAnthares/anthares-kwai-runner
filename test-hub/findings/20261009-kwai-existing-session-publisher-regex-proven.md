# Existing-session publisher Playwright selector correction
STATUS: PROVEN
AREA: kwai-codespaces-existing-session-publisher
DATE: 2026-10-09
RUN: 37960192767
JOB: 113920772902
COMMIT: 3c220bbc80d2c9892843b86a97bc5530bcc233cf
SUPERSEDES: 20261009-kwai-existing-session-publisher-core-proven.md

BASELINE_PROVEN: existing-session publisher core already passed the six fail-closed contract tests.
FAILED_AVOIDED: a raw string passed as Playwright accessible-name matcher would be interpreted as literal text rather than a regular expression in real Playwright. The final control now uses a compiled case-insensitive regex.
SUCCESS_SIGNAL: hosted job 113920772902 reran all six publisher safety tests at commit 3c220bbc80d2c9892843b86a97bc5530bcc233cf and all passed.
FAILURE_SIGNAL: none observed in the declared offline QA scope.
TEST_VALIDITY: PROVEN for selector semantics plus the existing offline publisher safety contract only. No live upload or publish was attempted.
