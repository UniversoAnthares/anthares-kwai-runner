# Lease — CORTES R07.6: isolamento de propriedade Kwai/TikTok
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
RUN: none
JOB: r076-cortes-iso01-iso02-kwai-tiktok-20261024
COMMIT: anthares-clipper main 2084019a95cfa04560866bb3a18722e92344771f
SUPERSEDES: none
LEASE_AREA: cortes-kwai-tiktok-owner-map-and-code-paths
LEASE_OWNER: ChatGPT authorized owner request
LEASE_STATUS: ACTIVE
LEASE_SCOPE: two network-scoped branches (Kwai/TikTok), read-only current runtime inventory, protected base branch CI checks. No merge, deploy, social publication, credentials, production databases or workflow runtime modification.
LEASE_START_UTC: 2026-10-24T22:10:29.086Z
LEASE_EXPIRY_UTC: 2026-10-24T22:40:29.086Z

## Baseline and governance
- Owner explicitly authorized formal network owner mapping and cross-network write-path authorization.
- Governance manifest f6fc9ca59a96e451, preflight passed for authenticated worktree D:\AntharsWork\repos\anthares-kwai-runner.
- Anthares clipper main 2084019a95cfa04560866bb3a18722e92344771f has trusted-base ci/network_scope_guard.py plus pull_request_target workflow; scope is Kwai/TikTok ONLY. Threads lease cortes-threads-owned-inventory-ci is separate and remains untouched.
- CI gate does not itself separate OS identities, secrets, SQL or production runners. No claims of full isolation before those controls.

## Experiment
BASELINE_PROVEN: ci/network_scope_guard.py owns explicit network roots and legacy paths, blocks cross-network edits and shared paths; prior unit regressions.
FAILED_AVOIDED: no direct main edits, no overwrite of dirty shared Windows working trees, no security-denial workaround, no production publication, no synthetic check mistaken for OS ACL.
SUCCESS_SIGNAL: network/kwai and network/tiktok scoped draft PRs, each containing ONLY its own network inventory/docs/tests; current trusted-base read-only CI reports APPROVED per network, cross-network changes denied in negative tests, readback hashes and immutable references.
FAILURE_SIGNAL: any cross-network edit approved, missed rename old/new, mixed branch admitted, untracked filesystem mutation or live publication.
TEST_VALIDITY: Execute guard against actual code paths plus CLI/CI; record runner startup failure as harness failure, not policy denial. No secret values.

## Finish
Append a new finding with tests/PRs/proof; close this lease. Preserve the pending Threads agent and PRs.
