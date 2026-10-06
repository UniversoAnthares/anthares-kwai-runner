# Kwai direct SEND reached FSM MAIN but media precondition was invalid because ffmpeg was absent
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37391970438
JOB: 112038914630
COMMIT: 045c3a18fa412e7cd42aab90618a31ce2d51de1e
SUPERSEDES: test-hub/findings/20261005-2121-kwai-direct-send-single-entrypoint-running.md

BASELINE_PROVEN: Manifest ACTION_SEND video/* contract and proven FSM MAIN.
FAILED_AVOIDED: prior shell-harness failures were eliminated by the single Bash entrypoint. No Publish action occurred and no conclusion about ACTION_SEND is inferred from this run.
SUCCESS_SIGNAL: not reached.
FAILURE_SIGNAL: not reached.
TEST_VALIDITY: PARTIALLY VALID PRECONDITION, HYPOTHESIS NOT TESTED. The run executed the repository Bash entrypoint, installed/launched Kwai and emitted `FSM_MAIN_REACHED` plus `TEST_VALIDITY=FSM_MAIN_REACHED`. It then failed before MP4 creation, MediaStore identity and ACTION_SEND because the hosted runner did not provide an `ffmpeg` executable.

## Resultado
The single-entrypoint repair succeeded and removed the `/usr/bin/sh` semantics blocker. The next failure is explicit and causal: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'` inside `kwai_direct_send_probe.py`. No generated media existed, so the validity requirements for MediaStore row/id, AM_RESULT and post-send UI were not reached.

## Consequência
The direct SEND hypothesis remains NOT_TESTED. The next run may repeat it only after installing/providing ffmpeg before the emulator probe. Preserve the same FSM/media/ACTION_SEND success and failure signals and do not alter the hypothesis itself.
