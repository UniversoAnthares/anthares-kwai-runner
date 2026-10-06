# CircleCI ADB boundary matrix — 10/10 success
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
RUN_EXAMPLE: https://circleci.com/gh/UniversoAnthares/anthares-kwai-runner/390
COMMIT: 387cbfd8422763e978a393af449e0dbab3c5e605
SUPERSEDES: test-hub/findings/20261006-circleci-adb-boundary-10-replica-matrix.md

## Resultado
All ten independent CircleCI Android 35 boundary probes completed successfully: kwai_boundary_probe_01 through kwai_boundary_probe_10. In each valid replica, the emulator/ADB precondition step and the immediately following next-step ADB check both succeeded.

## Consequência
The hypothesis that CircleCI inherently destroys the emulator/ADB device at every run-step boundary is refuted. Job 339's FAIL_ADB_WAIT_TIMEOUT was an intermittent or job-specific device-liveness failure, not a deterministic CircleCI boundary property.

## Evidence
GitHub commit statuses for 387cbfd8422763e978a393af449e0dbab3c5e605 show success for jobs 386, 387, 388, 389, 390, 391, 392, 393, 394 and 395.

## Next rule
Do not redesign the architecture around a presumed mandatory same-step requirement. Keep bounded ADB liveness checks/recovery. The Kwai install failure in job 384 remains a separate causal target.