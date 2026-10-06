# Lease — Android redundancy research
STATUS: RUNNING
AREA: android
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

OWNER: chatgpt-android-redundancy
EXPIRES: 2026-10-06T13:30:00Z
SCOPE: provider research/read-only integration design only; no kwai-login mutation.

BASELINE_PROVEN: GitHub Android API 35 x86_64 + ARM translation reaches KWAI_LAUNCHED; current kwai-login chain is leased by another agent.
FAILED_AVOIDED: no bare login URI/activity retries; no PC/Oracle fallback; no mutation to current login harness.
SUCCESS_SIGNAL: identify at least two causally independent remote Android substrates meeting automation/logging constraints and document exact account/credential blockers.
FAILURE_SIGNAL: candidates lack remote Android, automation, network, sufficient runtime, or sustainable free access.
TEST_VALIDITY: claims must be backed by current provider documentation; no provider is called PROVEN without an Anthares run.
