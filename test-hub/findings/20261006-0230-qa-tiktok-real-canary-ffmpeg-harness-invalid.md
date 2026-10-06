# QA TikTok real canary harness invalid: ffmpeg absent
STATUS: FAILED
AREA: tiktok
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37403086793
JOB: 112074440850
COMMIT: 2aae551e25380c39f28d021b68dae50f2fbb151d
SUPERSEDES: none

## Objetivo
Audit whether the latest TikTok Real Publish failure tested the production publisher.

## Resultado
It did not. The synthetic-controlled-canary job stopped before session restore or publication because ffmpeg was absent on the runner.

## Evidência decisiva
The first executable step failed with `ffmpeg: command not found` and exit 127. The session-restore-probe was skipped.

## Consequência
Classify this run as harness INVALID for TikTok publication. Do not infer session or publisher regression. A retry is causally valid only after provisioning a known ffmpeg path or avoiding runtime media generation.