# QA 40 parallel contracts and real GitLab checkout closure
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38076986441
JOB: 40 independent matrix jobs
COMMIT: 8519561fe0bd742ce570c18f2fd88aa47662e1c6
SUPERSEDES: none

## Objective
Close the 40-test runner-contract stage and advance to real publisher integration without repeating these diagnostics.

## Evidence
- All 40 distinct Python contract tests completed success on GitHub-hosted Linux runners. First start 18:44:22Z, last completion 18:44:36Z, observed peak 20 concurrently executing jobs. No secrets or local PC.
- Real GitLab branch job 17084427523 in pipeline 2934134870 successfully completed prepare_script and get_sources, checked out SHA 77b910ac on Render custom executor; image preparation reached container execution before external cancellation. Do not claim image job success.
- GitLab main pipeline 2933736510 status success: PHP QA, JS QA, extreme static QA, render smoke, mirroring and failover jobs succeeded on Render. One optional Copilot autofix job failed due 3600s server timeout and was non-blocking.
- Six GitLab-hosted QA branch jobs failed ci_quota_exceeded, not code failure; GitHub private mirror jobs also failed before running steps. Do not repeat quota-bound tests without a changed execution provider.

## Consequence
40 contract tests are complete and must not be rerun as a gate to publication. Real private-branch image-aware integration and GitLab quota routing remain separate tracked issues. Preserve MR !34 without merging before a green target-branch validation. Next: advance to Kwai publisher preflight/Cloudflare version and real account identity; no real publication claimed.
