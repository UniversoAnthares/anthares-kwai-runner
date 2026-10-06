# Kwai direct video ACTION_SEND probe with single Bash entrypoint
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: direct-media-ingress
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2054-kwai-uri-router-video-send-contract.md; FSM MAIN is proven; test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md.
FAILED_AVOIDED: test-hub/findings/20261005-2108-kwai-direct-send-harness-invalid.md and test-hub/findings/20261005-2119-kwai-direct-send-action-script-semantics-invalid.md. The android-emulator-runner YAML now contains exactly one script command, `bash kwai_direct_send_runner.sh`; all pipefail/PIPESTATUS logic lives inside that repository Bash script. No Publish action is present.
SUCCESS_SIGNAL: `TEST_VALIDITY=FSM_MAIN_REACHED`, exact generated media/MediaStore identity, successful explicit ACTION_SEND video/mp4, and `SUCCESS_SIGNAL=DIRECT_SEND_MEDIA_EDITOR` with post-send evidence.
FAILURE_SIGNAL: after all valid preconditions, explicit ACTION_SEND rejection/import error, Kwai leaving foreground, or unchanged MAIN.
TEST_VALIDITY: FSM_MAIN_REACHED + nonempty generated MP4 + exact MediaStore row/id + Android send result + post-send UI dump. Earlier failure remains harness-only and may not be counted against the route.

## Objetivo
Execute the media-ingress hypothesis through the emulator action's proven single-command shell boundary so the actual ACTION_SEND contract is finally reached.
