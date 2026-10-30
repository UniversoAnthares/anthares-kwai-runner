# QA-P0 controller offloaded to GitHub-hosted Ubuntu
STATUS: PROVEN
AREA: architecture/qa-p0
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40992225120
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40992225120/job/123857093476
COMMIT: c2537fdadad687582438bb2e127f01b7d6672b2d
SUPERSEDES: lease-20261029-qa-p0-cloud-controller.md

## Objective
Migrate only the JavaScript incident controller from the Windows runner to hosted Ubuntu.

## Verified result
PR #1935 merged. PR run 40992193359 succeeded, then main run 40992225120 finished SUCCESS on runner GitHub Actions 1000049554 using ubuntu-24.04. Main YAML content has runs-on: ubuntu-24.04.

## Decisive evidence
QA_P0_FINGERPRINT_DEDUP=PASS candidates=800 unique=483 suppressed=317.
Two dispatch acknowledgments: issues 590 and 592, each attempt=1. QA_P0_BACKLOG_INCOMPLETE logged. Neither dispatch acknowledgment constitutes successful source repair or publication; incidents remain open.

## Consequence
Controller runner offload PROVEN. Do not disable other Windows QA paths until independent migration proof. Executor and authenticated WordPress route remain pending. Preserve fingerprint dedup, bounded dispatch and media fencing. No automated retries of uncertain posts.
