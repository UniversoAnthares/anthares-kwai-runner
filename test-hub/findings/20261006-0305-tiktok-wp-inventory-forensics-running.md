# TikTok WP inventory forensics 5-way
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261006-0240-tiktok-wp-filename-reconstruction-running.md

BASELINE_PROVEN: run 37405252389 reached REST but all five variants were INVALID because the newest video record lacks media_details.file.
FAILED_AVOIDED: no reconstruction assumes media_details.file. Inspect five independent evidence sources across the full live inventory.
SUCCESS_SIGNAL: strategy yields a distinct actionable owned-media locator or proves a consistent registry property.
FAILURE_SIGNAL: strategy executes validly and yields no locator/property.
TEST_VALIDITY: REST inventory must be reachable and non-empty.

## Objetivo
Extract actionable media-location evidence without assuming WordPress file metadata.