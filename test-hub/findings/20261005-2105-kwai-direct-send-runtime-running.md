# Kwai direct video ACTION_SEND runtime probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: direct-media-ingress
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2054-kwai-uri-router-video-send-contract.md; proven kwai_state_driver FSM reaches MAIN; test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md.
FAILED_AVOIDED: current gallery path's candidates[0] is not assumed deterministic; no Publish control will be clicked; no login hypothesis is tested; the probe reaches FSM_MAIN_REACHED first so onboarding/harness divergence is INVALID rather than media-route failure.
SUCCESS_SIGNAL: from FSM_MAIN_REACHED with exactly one staged test video, explicit ACTION_SEND video/mp4 to exported UriRouterActivity returns Android success and the post-send UI leaves the baseline MAIN surface for a media editor/composer state with observable editing/posting controls tied to the handed-off media.
FAILURE_SIGNAL: valid precondition is reached but ACTION_SEND is rejected, returns to unchanged MAIN without media/editor transition, or exposes an explicit import error.
TEST_VALIDITY: requires FSM_MAIN_REACHED, generated MP4 nonempty, exact single MediaStore row/id, successful UI dump after intent. Any failure before these preconditions is INVALID/NOT_TESTED.

## Objetivo
Determine whether the Manifest-proven ACTION_SEND video/* contract can replace arbitrary gallery tile selection with an exact content-URI handoff. The probe is strictly non-publishing and must capture XML/screenshot evidence.
