# Item 10 — automatic GitLab rescue receipt trigger integrated
STATUS: PARTIAL
AREA: architecture/ci-quota-gitlab-failover
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40937331835
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40937331835/job/123671241002
COMMIT: c1515aa275ac08f257ec0c0a77d882ae285ec458
SUPERSEDES: 20261029-item10-gitlab-receipt-trigger-running.md

## Result
PR #1918 merged to main. The quota watcher is subscribed to the existing CORTES and private CI rescue workflow_run completion events. Its job gate admits only main-branch completed-success dispatches with recognized rescue names and quota-rescue titles, while preserving trusted scheduled parents, concurrency fencing and exact-receipt deduplication.

## Live evidence
Push-triggered watcher run 40937331835 ended SUCCESS. Decisive log lines: cortes=FALLBACK_CONFIRMED run=40933045761 and cortes=DEDUPED sha=ffe437d02911. No new GitLab quota successor was dispatched. The four earlier real-success incident receipts 3005298759, 3005095179, 3004729641 and 3002177551 were independently reconciled in Neon to FALLBACK_CONFIRMED, lease_generation=3, with exact SHA and GitHub run IDs.

## Remaining acceptance
Observe a future naturally arising successful rescue workflow_dispatch followed by the newly subscribed watcher workflow_run and its authenticated Neon receipt confirmation. Forgejo fallback remains repo-scoped for nonpublishing CI; autonomous general dispatch and dual-outage handoff have not been proven. No synthetic quota incident or publication should be generated.
