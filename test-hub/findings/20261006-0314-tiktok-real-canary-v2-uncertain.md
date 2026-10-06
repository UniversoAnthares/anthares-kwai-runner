# TikTok real canary v2 — post-start 502, UNCERTAIN
STATUS: PARTIAL
AREA: tiktok-publish
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37407210637
JOB: 112087313503
COMMIT: 76b5f10f2c4e021f814234bc9093cc0c7b8d50e6
SUPERSEDES: none

## Objective
Observe the single fenced production canary v2 without blind retry and classify its terminal evidence.

## Result
The deterministic MP4 passed validation. The exact pre-publication session gate returned bootstrapped=true, identity_verified=true and ready_for_tiktok=true. The queue leased the exact canary with lease_generation=1 and the workflow crossed publication_started. The Render /publish request later returned HTTP 502. The workflow correctly invoked the post-start fail-safe and emitted CANARY_STATE=UNCERTAIN.

## Decisive evidence
SYNTHETIC_MP4_VALID
PREPUBLISH_IDENTITY {"bootstrapped": true, "identity_verified": true, "ready_for_tiktok": true}
curl: (22) The requested URL returned error: 502
CANARY_STATE=UNCERTAIN

## Consequence
DO NOT rerun or republish this canary. Publication may have occurred before the 502. Next action is observation-only reconciliation against the expected account/post. Only strong absence proof may permit a later new publication attempt under a new explicit decision. This run is valid evidence that post-start ambiguity fails closed; it is not TIKTOK_REAL_REMOTE_POST=PROVEN.