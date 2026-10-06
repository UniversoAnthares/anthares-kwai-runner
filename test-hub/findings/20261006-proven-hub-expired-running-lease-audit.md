# Hub expired RUNNING lease audit — PROVEN
STATUS: PROVEN
AREA: test-hub / coordination
DATE: 2026-10-06
RUN: 37402920736
JOB: 112073915579
COMMIT_BASELINE: da8bd246dbb89ca92ae2b5ff20673395f73b382a

A repository-local audit scanned all test-hub findings and found 17 entries with STATUS: RUNNING whose LEASE_EXPIRES timestamp was already in the past at execution time.

Decision: historical findings remain append-only. Coordination must evaluate LEASE_EXPIRES, not STATUS alone; RUNNING + expired is not an active mutation lease.

Reusable workflow: .github/workflows/hub-lease-hygiene.yml
Artifact: expired-running-leases.txt
No production mutation occurred.
