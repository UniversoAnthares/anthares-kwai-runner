# Lease — Forgejo sync CDN readback without destructive fetch
STATUS: RUNNING
AREA: architecture/forgejo-git-ci-redundancy
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40735222520
JOB: 122981830347
COMMIT: main (read before mutation)
SUPERSEDES: 20261006-0945-forgejo-operational-gitlab-auth-remains.md
LEASE_STARTED_UTC: 2026-10-28T18:33:00Z
LEASE_EXPIRES_UTC: 2026-10-28T19:03:00Z

BASELINE_PROVEN: Hostinger Git daemon has a fresh verified 15-repository receipt; independent OIDC identity run 266 passed; GitHub-to-Forgejo isolated restorations 15/15 proven.
FAILED_AVOIDED: GitHub Actions run 40735222520 failed on CDN 403 to git ls-remote Forgejo after receiving SYNC_PROVEN SHA. The legacy fixed endpoint mutates branches via fetch --prune and +refspec.
SUCCESS_SIGNAL: A read-only Hostinger endpoint validates a fresh independent receipt and local main SHA, GitHub workflow compares that receipt with authoritative GitHub main, and the job emits CROSS_PROVIDER_SHA_CHECK=PROVEN without a 403.
FAILURE_SIGNAL: Status is expired, mismatched, invalid or unavailable; endpoint fails closed without any Git mutation, or GitHub CI does not prove equality.
TEST_VALIDITY: Check actual endpoint behavior and GitHub Actions logs, not merely workflow success; no publication, no token changes, no destructive Git operations.
CONCURRENCY: Protected feature branch; re-read authoritative HEAD and target blobs before committing. Cancel this mutation if another active owner changed the same files.
