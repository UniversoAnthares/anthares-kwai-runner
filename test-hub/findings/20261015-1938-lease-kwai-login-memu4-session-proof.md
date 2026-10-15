# Lease — Kwai login / MEmu4 session proof
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
LEASE_OWNER: chatgpt-memu4-session-proof-20261015
LEASE_EXPIRES: 2026-10-15T20:08:00-04:00

BASELINE_PROVEN: `MEmu_4` is Running; package `com.kwai.video` is installed; user-context ADB `-P 5038` reports `127.0.0.1:21543 device` and `sys.boot_completed=1`.

FAILED_AVOIDED: do not treat SYSTEM-context ADB 5037/offline as device failure; do not clear app data; do not reinstall Kwai; do not publish; do not use GitHub Android experimental fallback.

SUCCESS_SIGNAL: launch existing Kwai session on MEmu4, reach stable app UI, and obtain read-only evidence sufficient to determine whether target identity `@lucasrosalem` is already authenticated, without changing account/session data.

FAILURE_SIGNAL: app cannot launch, transport falls offline in the user-context 5038 path, or UI evidence shows unauthenticated/login-required state.

TEST_VALIDITY: ADB must remain `device`, boot_completed must equal 1, package `com.kwai.video` must remain installed, and no publication action may be invoked.