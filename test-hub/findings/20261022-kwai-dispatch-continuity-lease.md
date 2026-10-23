# Lease: Kwai queue dispatch continuity remediation
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-22
RUN: none
JOB: none
COMMIT: be5b6ca38db244c6ba7155a00dcd2503fcdc6e24
SUPERSEDES: none
LEASE_AREA: kwai-publish
LEASE_OWNER: ChatGPT dispatch continuity investigation 2026-10-22
LEASE_START_UTC: 2026-10-23T00:07:14.978Z
LEASE_MAX_EXPIRY_UTC: 2026-10-23T00:32:14.978Z

## BASELINE_PROVEN
Neon holds 36 Kwai jobs queued, zero leased; latest confirmed 2026-10-22T17:50:48Z. Code inspection revealed noncanonical Cloudflare default routing for /job/ operations, and literal task response markers corrupting three recovery scripts. Windows controllers unreachable at time of investigation.

## FAILED_AVOIDED
No live publish probe, no SQL queue mutation, no duplicate/uncertain retry, no overwriting dirty Windows workspace or interactive windows; GitHub protected main requires PR.

## SUCCESS_SIGNAL
Canonical Neon-only job operations, parseable recovery scripts, autonomous local scheduled daemon-recovery watchdog, static regression acceptance. Deployment and a real verified new post required for production PROVEN.

## FAILURE_SIGNAL
Concurrent branch change, syntax failure, watchdog risks in-flight duplicate execution, Windows unreachable during deploy.

## TEST_VALIDITY
STATIC tests demonstrate code behavior only; live restoration requires a separately observed post and central ledger confirmation.
