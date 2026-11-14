# Agent 06 — SpawnDroid monthly admission, safe staging
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-14
RUN: none (offline contracts pending)
JOB: agent06-spawndroid-capacity-failclosed-20261114
COMMIT: base 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
SUPERSEDES: none
OWNER: agent06 (isolated branch, offline code only)

## BASELINE_PROVEN
Neon cortesqueue production deployment 77 active, canonical 06:00–23:00 pacing, existing CAS/lease/fencing; SpawnDroid Hub canary only starts and closes official Kwai app, never authenticates or publishes. Two historical public accounts have Neon receipts. Physical publisher retained. Main cloud_cutover.enabled=false.

## FAILED_AVOIDED
Avoid OCI no-capacity, unverified free VPS, direct GitHub Android production, unverified login persistence, historical uncertain replay, and credentials transfer. GitLab main diverges from GitHub main (3c001d5 vs 5db0bf2); no mirroring.

## SUCCESS_SIGNAL
Isolated module and offline CI validate conservative 200-minute Hobby monthly budget, freshness, real-measurement prerequisites, separate account telemetry, 15-minute sessions, daily cap, shared slot, quotas and cancelled/uncertain state handling. No Android launch or media publication.

## FAILURE_SIGNAL
Cloud cutover changed, live sessions started, service tokens copied, work on desktop, fake measured capacity, duplicate publication, or green CI without asserted test signals.

## TEST_VALIDITY
Offline synthetic contract tests on GitHub-hosted Ubuntu. Real device metrics, account authentication, publication proof and remote work independence remain NOT_TESTED by this work.
