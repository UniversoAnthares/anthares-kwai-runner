# Android Agent CI single-current-build lease
STATUS: RUNNING
AREA: kwai-physical-android-agent-build
DATE: 2026-10-09
OWNER: chatgpt-kwai-physical-share
LEASE_UNTIL: 2026-10-09T23:59:00Z
HEAD_BASELINE: 2b096e5224bf3582894d29f4c01d586170e0c219
RESOURCES: .github/workflows/android-agent-build.yml
BASELINE_PROVEN: Android Agent build workflow starts on android-agent/** changes. Multiple intermediate commits created simultaneous builds, and AndroidX build failed without android.useAndroidX; corrected at 2b096e52.
FAILED_AVOIDED: do not repeat stale builds, do not create Android emulator, no PC. Existing workflow path-only trigger preserved.
SUCCESS_SIGNAL: latest-commit APK build success and artifact; earlier in-progress builds canceled by concurrency on subsequent commits.
FAILURE_SIGNAL: workflow syntax error or no APK artifact.
TEST_VALIDITY: APK build is only compilation, not physical Kwai app upload/post proof.
PEER: check GitLab workflow before mutation; no blind mirroring.
