# Lease: TikTok v14 harness repair and parallel preflight
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
LEASE_AREA: tiktok-publish
LEASE_EXPIRES: 2026-10-06T12:05:00Z
BASELINE_PROVEN: run 37455150759 failed before publication_started because its checkout attempted cross-repository anthares-clipper with an inaccessible token; no real publish was attempted.
FAILED_AVOIDED: do not repeat cross-repository checkout; do not run simultaneous irreversible publish attempts. Parallelism is restricted to read-only OIDC/Render/session/profile preflight.
SUCCESS_SIGNAL: multiple parallel read-only replicas prove control OIDC + Render OIDC + profile inventory, then exactly one serialized v14 canary reaches independent profile confirmation.
FAILURE_SIGNAL: read-only matrix isolates a common failing boundary, or the single canary reaches UNCERTAIN and is observation-only.
TEST_VALIDITY: each read-only replica must obtain both OIDC tokens and receive non-401 responses; irreversible path remains single-job fenced.
