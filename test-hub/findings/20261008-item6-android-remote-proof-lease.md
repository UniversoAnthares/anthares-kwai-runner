# Item 6 Android remote executor proof lease
STATUS: RUNNING
AREA: android-remote-executor
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: CircleCI Android executor smoke passed in 3m14s and prior GitHub API35 x86_64 KVM runs reached Android MAIN.
FAILED_AVOIDED: do not repeat run 37788411479 publisher path; isolate emulator/ADB boot only and use reactivecircus/android-emulator-runner@v2.
SUCCESS_SIGNAL: hosted GitHub runner reports adb get-state=device and sys.boot_completed=1, then ANDROID_ADB_BOOT=PROVEN.
FAILURE_SIGNAL: explicit KVM/ADB/emulator failure before success marker.
TEST_VALIDITY: missing KVM or host/runtime failure is INVALID for the Android-executor hypothesis.

Lease scope: item 6 isolated remote Android/ADB executor proof only. No Kwai login, publication, session or queue mutation.
