# TikTok owned clip filename reconstruction 5-way
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261006-0225-tiktok-wp-registry-fiveway-running.md

BASELINE_PROVEN: run 37403154501 showed guid/attachment/www/http references remain stale; REST record itself is live.
FAILED_AVOIDED: do not retry stale canonical URLs. Derive alternate physical upload names/paths from live REST metadata.
SUCCESS_SIGNAL: one reconstructed owned-media path returns HTTP 200/206 with >=1024 bytes.
FAILURE_SIGNAL: all five metadata-derived reconstructions return missing/non-video.
TEST_VALIDITY: live REST record must expose source_url and media_details/file.

## Objetivo
Test five filename/path reconstructions from WordPress media metadata.