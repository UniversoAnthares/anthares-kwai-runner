# Lease — Kwai Phone Chrome FRE closure
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: pending
JOB: none
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: run 37470899378 proves MAIN -> native login chooser -> Phone action, and proves the resulting foreground is Chrome FirstRunActivity.
FAILED_AVOIDED: direct Activity/deeplink guessing, coordinate matrices and repeated Phone discovery are closed and will not be repeated.
SUCCESS_SIGNAL: after deterministic Chrome FRE initialization, the same legitimate native Phone action reaches a real web Phone/auth/challenge surface rather than FirstRunActivity.
FAILURE_SIGNAL: after FRE is proven cleared, Phone still cannot reach an auth/challenge surface.
TEST_VALIDITY: current Agent build, emulator boot, apps installed, FSM_MAIN_REACHED, LOGIN_SURFACE_REACHED, and Chrome FRE-cleared marker.
EXPIRY: 2026-10-06T13:50:00Z

Mutation scope is only kwai-login runtime normalization before the already-proven Phone action. No publish and no LIVE mutation.
