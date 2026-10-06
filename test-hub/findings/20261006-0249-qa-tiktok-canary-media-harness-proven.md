# QA TikTok synthetic canary harness — cloud media path proven
STATUS: PROVEN
AREA: tiktok
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37405248345
JOB: 112081253557; 112081253709; 112081253718
COMMIT: a2b6090833036c23580b65650a10774e340fcf63
SUPERSEDES: test-hub/findings/20261006-0242-tiktok-canary-media-harness-fiveway-running.md

## Objetivo
Close the five-way no-PC media-generation matrix after the repaired workflow actually executed.

## Resultado
Three independent cloud mechanisms produced a non-empty MP4 and emitted the declared SUCCESS_SIGNAL:
- imageio_ffmpeg: PROVEN
- apt_ffmpeg: PROVEN
- docker_ffmpeg: PROVEN

static_ffmpeg did not emit the success signal. system_paths exited 127. Those failures do not affect the proven mechanisms.

Canonical mechanism to preserve for the next canary: imageio_ffmpeg. It provisions its own ffmpeg executable in the GitHub runner and does not rely on ffmpeg already existing in system PATH.

## Evidência decisiva
Job 112081253557: CANARY_MEDIA_HARNESS=PROVEN imageio_ffmpeg
Job 112081253709: CANARY_MEDIA_HARNESS=PROVEN apt_ffmpeg
Job 112081253718: CANARY_MEDIA_HARNESS=PROVEN docker_ffmpeg

TEST_VALIDITY was satisfied because runner shell/Python executed and each successful branch generated /tmp/canary.mp4 before emitting SUCCESS_SIGNAL.

## Consequência
The ffmpeg harness blocker from run 37403086793 is closed. Do not reopen generic ffmpeg discovery. Use imageio_ffmpeg as the canonical deterministic cloud preparation path unless production evidence later supersedes it. This finding proves media preparation only; it does not claim a TikTok publication.