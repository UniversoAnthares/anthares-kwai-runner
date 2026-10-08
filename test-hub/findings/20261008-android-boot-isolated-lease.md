# Isolated Android boot diagnostics lease
STATUS: RUNNING
AREA: android-boot-diagnostic
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: API35 x86_64 with KVM can reach Android MAIN in prior independent tests.
FAILED_AVOIDED: run 37788411479 ADB daemon port 5037 failure; avoid live publisher and authentication chain.
SUCCESS_SIGNAL: emulator boots, adb get-state=device, sys.boot_completed=1 in hosted GitHub runner.
FAILURE_SIGNAL: explicit adb/emulator diagnostics with distinct timeouts.
TEST_VALIDITY: absent KVM, SDK installation failure or host resource failure classified INVALID rather than Kwai login failure.

Lease: isolated Android boot-only workflow, expires 2026-10-08T23:59:00Z. No kwai-login, kwai-publish or session mutations.
