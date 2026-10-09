# Physical Android official Kwai share handoff APK built
STATUS: PARTIAL
AREA: kwai-physical-android-companion
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37964111088
JOB: 113934018641
COMMIT: 6d784f8f0c7a14013a9bf33c2d37d7147846724e
SUPERSEDES: 20261009-lease-kwai-physical-android-share.md; 20261009-lease-kwai-physical-agent-ci.md

BASELINE_PROVEN: live mobile Chrome CDP session and Android-like UA/touch/viewport failed to expose Kwai video upload. Kwai official help directs camera/Album in the native application. Previous APK Android Agent and com.kwai.video manifest ACTION_SEND video/* path were available.
CHANGE: Android Agent MainActivity now exposes native Android document picker and receives anthares-kwai://send links; KwaiVideoHandoff.java securely downloads from allowlisted HTTPS anthares.us, validates required SHA-256 and 250 MiB bound, stores video in app-private cache, shares via temporary FileProvider URI grant and ACTION_SEND video/mp4 explicitly to com.kwai.video. android-agent/make_handoff.py generates integrity-checked links. android.useAndroidX=true was added after observed failed builds. GitHub workflow concurrency now cancels superseded runs.
SUCCESS_SIGNAL: run 37964111088 compiled APK and uploaded artifact id 11632877768 (anthares-android-agent-debug), 2,190,414 bytes. Prior corrected run 37964064100 also succeeded and uploaded artifact 11632652869. APK source compiles on GitHub hosted runner without PC and without emulator.
LIMITATION: This is a compiled handoff agent, not a real Kwai upload or published video. No physical Android device is connected or logged in for end-to-end confirmation; actual ACTION_SEND destination UI acceptance and account ownership still require live validation. The existing Accessibility service may navigate unexpectedly if enabled during share; verify on device before unattended automation. Do not mark KWAI_REAL_REMOTE_POST PROVEN.
NEXT: Install APK on an Android phone with official Kwai app and signed-in target account; verify picker->ACTION_SEND->Kwai editor. Only then add a securely authenticated cloud queue/polling worker and consented Accessibility automation with account check and idempotent ledger. No PC as executor.
TEST_VALIDITY: build/artifact only; physical-device acceptance NOT_TESTED.
