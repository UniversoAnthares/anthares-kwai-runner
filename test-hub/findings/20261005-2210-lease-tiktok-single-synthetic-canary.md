# Lease — TikTok single synthetic diagnostic canary
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-05
OWNER: CHAT 3
EXPIRES: 2026-10-05T22:40:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2055-tiktok-render-direct-ready-queue-and-source-proven.md; identity universo.anthares verified and Render direct publisher preflight proven. test-hub/findings/20261005-2257-tiktok-controlled-diagnostic-ready.md instruments the 3/day diagnostic path.
FAILED_AVOIDED: anonymous YouTube is closed by 429/login gating; Render network independently reproduced 429 for default/android_vr/tv/web_safari/mweb. WordPress REST inventory exposes orphan video metadata but five transport methods return 404. This test does not reuse either source.
SUCCESS_SIGNAL: create one deterministic cloud-only MP4, validate ffprobe, acquire one stable queue lease, verify exact TikTok identity immediately before irreversible action, publish exactly once, and independently observe exactly one new profile /video/<id>; close central state with that remote_id/evidence.
FAILURE_SIGNAL: media validation failure, identity mismatch, queue refusal, upload failure, zero or multiple new profile IDs, or ambiguous confirmation => no positive completion; mark UNCERTAIN if publication_started.
TEST_VALIDITY: synthetic MP4 must be generated and ffprobe-valid before any queue/publication mutation; publisher revision must include fail-closed profile verifier.
SAFETY: exactly one canary; no retry after publication_started unless reconciliation proves no post; no PC dependency.
