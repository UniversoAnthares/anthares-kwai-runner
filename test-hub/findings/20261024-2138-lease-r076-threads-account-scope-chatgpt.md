# Lease: R07.6 CORTES Threads primary inventory and code-scope gate
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
RUN: none
JOB: r076-iso01-iso02-20261024
COMMIT: anthares-clipper main 2084019a95cfa04560866bb3a18722e92344771f
SUPERSEDES: none
LEASE_AREA: cortes-threads-owned-inventory-ci
LEASE_OWNER: ChatGPT current conversation
LEASE_STATUS: ACTIVE
LEASE_SCOPE: new isolated branch and draft PR; no main merge, deployment, publication, queue, SQL, credential or runner modification
LEASE_START_UTC: 2026-10-24T21:38:00Z
LEASE_EXPIRY_UTC: 2026-10-24T22:08:00Z

## Baseline and preflight
- Governance manifest f6fc9ca59a96e451 and policy.py audit 218/218 with zero failures; mandatory preflight on D:\AntharesWork\anthares-clipper.
- Base GitHub SHA 2084019a95cfa04560866bb3a18722e92344771f; peer GitLab main SHA 1eab2129e71027a14e68407f52e86e643c0ada2b, different history; do not mirror.
- Existing trusted-base network-scope-guard.yml; self-hosted contract run 40134193308 succeeded.
- Existing Threads adapter draft PR #186 cannot be merged and is not active production.

## Experiment
BASELINE_PROVEN: 23 approved tests of ci/network_scope_guard.py and trusted base PR checks, including real renames/foreign paths.
FAILED_AVOIDED: do not use cloud probe 40134278061 as evidence; it failed before runner allocation. Do not rerun four historically denied security tests via another runner.
SUCCESS_SIGNAL: single Threads primary inventory with explicit owner, credential refs, source/queue/deploy paths and UNKNOWN flags; scoped draft PR allowed by trusted-base guard and cross-network negative offline regression on authorized test only.
FAILURE_SIGNAL: baseline SHA drift, cross-network path in the diff, guard refusal of own Threads paths, unauthorized deployment/cost, security refusal.
TEST_VALIDITY: no publisher job, zero secrets, no activation, no checkout of untrusted PR head by CI, no modification of other networks.
NEXT: only docs/networks/threads/ and tests/networks/threads/ on dedicated network/threads branch; create closing finding and mark checklist only on verifiable completion.
