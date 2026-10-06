# Kwai heartbeat wrapper normal-exit race
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: 37397420475
JOB: 112056595572
COMMIT: 9ca0c13516a78c674acf089413ed256b092c83c5
SUPERSEDES: none

## Resultado
Contract test exposed a wrapper coordination bug before publication. A normal child completion terminated the heartbeat helper with SIGTERM; exit 143 was incorrectly treated as lease-heartbeat loss.

## Consequencia
No media publication occurred. Fix wrapper shutdown semantics before integration. Do not classify this run as evidence against control v16 or renew.
