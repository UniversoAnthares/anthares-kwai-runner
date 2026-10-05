# Kwai direct video ACTION_SEND runtime probe after shell-harness repair
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: direct-media-ingress
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2054-kwai-uri-router-video-send-contract.md; proven kwai_state_driver FSM reaches MAIN; test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md.
FAILED_AVOIDED: test-hub/findings/20261005-2108-kwai-direct-send-harness-invalid.md; the previous run never reached the hypothesis because android-emulator-runner invoked `set -o pipefail` through `/usr/bin/sh`. The repaired workflow explicitly starts a Bash heredoc before enabling pipefail or reading PIPESTATUS. No Publish control is clicked.
SUCCESS_SIGNAL: after `TEST_VALIDITY=FSM_MAIN_REACHED` and exact single MediaStore identity, explicit ACTION_SEND video/mp4 to exported UriRouterActivity returns Android success and produces a changed Kwai media editor/composer UI with observable editor/post controls.
FAILURE_SIGNAL: valid preconditions are reached but ACTION_SEND is rejected, explicit import error appears, Kwai is not foreground after the send, or the post-send UI remains unchanged MAIN.
TEST_VALIDITY: must show FSM_MAIN_REACHED, generated nonempty MP4, exact MediaStore row/id, Android send result and a post-send UI dump. Failure before these signals is INVALID/NOT_TESTED.

## Objetivo
Repeat the previously invalid direct-media ingress experiment with the shell harness corrected and preserve the exact same hypothesis/signals.
