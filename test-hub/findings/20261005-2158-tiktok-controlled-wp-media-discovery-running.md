# TikTok controlled WordPress media discovery
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2055-tiktok-render-direct-ready-queue-and-source-proven.md; run 37397646284 proves anthares.us is publicly reachable but the two sampled pages contain no direct video.
FAILED_AVOIDED: anonymous YouTube/Piped/Invidious extraction is excluded; this test queries only owned Anthares WordPress public media metadata and direct uploads.
SUCCESS_SIGNAL: at least one public Anthares-owned video attachment returns a direct downloadable video URL and valid media bytes.
FAILURE_SIGNAL: WordPress media inventory is reachable but contains no usable video attachment.
TEST_VALIDITY: REST/search HTTP failure or inability to inspect media bytes is INVALID harness/source reachability, not absence of media.

## Objetivo
Discover a controlled cloud media source for the TikTok canary without YouTube extraction and without publishing.