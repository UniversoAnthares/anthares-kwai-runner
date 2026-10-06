# Kwai direct video ACTION_SEND probe after ffmpeg dependency repair
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: direct-media-ingress
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: Manifest ACTION_SEND video/* contract; proven FSM MAIN; single Bash entrypoint now works; publisher lifecycle static proof remains valid.
FAILED_AVOIDED: test-hub/findings/20261005-2130-kwai-direct-send-missing-ffmpeg-invalid.md plus prior shell-harness invalid runs. The preparation step now installs ffmpeg explicitly and verifies `command -v ffmpeg`/version before emulator execution. No Publish action exists in the probe.
SUCCESS_SIGNAL: `TEST_VALIDITY=FSM_MAIN_REACHED`, nonempty generated MP4, exact single MediaStore row/id, successful explicit ACTION_SEND video/mp4, post-send UI evidence, and `SUCCESS_SIGNAL=DIRECT_SEND_MEDIA_EDITOR`.
FAILURE_SIGNAL: after all validity preconditions, ACTION_SEND rejected, explicit import error, Kwai not foreground, or unchanged MAIN.
TEST_VALIDITY: must reach FSM_MAIN_REACHED, media generation, MediaStore id, AM_RESULT and post-send UI dump. Failure before those signals remains harness/precondition-only.

## Objetivo
Reach the actual direct-media handoff hypothesis after explicitly repairing the missing ffmpeg dependency.
