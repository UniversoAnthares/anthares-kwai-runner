# TikTok WP registry consistency 5-way
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2212-tiktok-wp-historical-media-running.md

BASELINE_PROVEN: run 37402934447 validly showed newest/middle/oldest source_url objects return 404; header/path tweaks do not recover them.
FAILED_AVOIDED: do not retry source_url transport. Test five distinct WordPress registry/origin references to locate where the owned clip actually lives.
SUCCESS_SIGNAL: a registry/origin strategy resolves to an owned video resource with HTTP 200/206 and >=1024 bytes, or exposes a distinct live canonical URL that does.
FAILURE_SIGNAL: each strategy resolves only to missing/stale/non-video resources.
TEST_VALIDITY: REST media record must load successfully first.

## Objetivo
Find a causally distinct canonical location for Anthares-owned clips after source_url was proven stale.