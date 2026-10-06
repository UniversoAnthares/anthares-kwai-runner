# TikTok WP historical video recovery 5-way
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2205-tiktok-wp-video-transport-running.md

BASELINE_PROVEN: run 37402350620 found REST video metadata but direct newest source_url transport failed.
FAILED_AVOIDED: test distinct historical objects/paths, not more headers against the same stale URL.
SUCCESS_SIGNAL: a distinct historical/path strategy returns HTTP 200/206 and >=1024 bytes.
FAILURE_SIGNAL: all five fail after REST inventory succeeds.
TEST_VALIDITY: REST inventory contains >=20 rows.

## Objetivo
Test whether alternate owned historical media paths remain retrievable.