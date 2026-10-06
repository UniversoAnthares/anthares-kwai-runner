# TikTok WordPress video transport methods
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2158-tiktok-controlled-wp-media-discovery-running.md

BASELINE_PROVEN: run 37402232780 proves the WP REST inventory exposes 191 video attachments, but its success predicate was too weak: sampled Range GETs returned HTTPError.
FAILED_AVOIDED: do not treat attachment metadata as downloadable media; change causally by testing transport methods and requiring actual MP4 bytes.
SUCCESS_SIGNAL: a method returns HTTP 200/206 plus non-empty video bytes from an Anthares-owned attachment.
FAILURE_SIGNAL: all distinct direct transport methods are rejected after REST discovery succeeds.
TEST_VALIDITY: WP REST discovery must return at least one video; otherwise INVALID.

## Objetivo
Determine whether the owned WordPress clips are directly retrievable from a cloud runner and which HTTP method works.